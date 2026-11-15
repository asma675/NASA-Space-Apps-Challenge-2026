"""Opt-in near-real-time *satellite detection* watch, distinct from verified fire incident alerts.

A FIRMS acquisition timestamp is the satellite observation time, NOT ignition or FIRMS
publication time. We persist when BLINDSPOT first successfully *checked* a grid-day,
so the resulting gap is never misrepresented as official reporting latency.
"""
from __future__ import annotations

import csv
import io
import os
import threading
import time
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from typing import Any

import httpx

from .analysis import cell_id
from .firms import NASA_BASE
from .storage import REGIONS, connection, init_db

# Current NOAA-20 and NOAA-21 VIIRS near-real-time streams, rather than historic S-NPP.
LIVE_PRODUCTS = ('VIIRS_NOAA20_NRT', 'VIIRS_NOAA21_NRT')
CACHE_SECONDS = 15 * 60
_cached: dict[str, tuple[float, dict[str, Any]]] = {}
_cache_lock = threading.Lock()


def _utc_iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00', 'Z')


def _parse_acquired(row: dict[str, str]) -> datetime | None:
    day = (row.get('acq_date') or '').strip()
    value = (row.get('acq_time') or '0000').strip().zfill(4)
    if len(value) != 4 or not value.isdigit():
        return None
    try:
        return datetime.strptime(day + value, '%Y-%m-%d%H%M').replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def build_clusters(rows: list[dict[str, str]], checked: datetime, global_grid: bool=False) -> list[dict]:
    """Group detections by the SAME global Equal Earth EPSG:8857 10-km grid and UTC day.

    No wildfire ignition / continuity / containment inference is made.
    """
    groups: dict[tuple, dict] = {}
    for row in rows:
        # NASA FIRMS Type 0 = presumed vegetation fire. The classification is not validation.
        if row.get('type') not in (None, '', '0'):
            continue
        try:
            lat, lon = float(row['latitude']), float(row['longitude'])
            if not (-90 <= lat <= 90 and -180 <= lon <= 180):
                continue
        except (TypeError, ValueError, KeyError):
            continue
        observed = _parse_acquired(row)
        if observed is None or observed > checked + timedelta(minutes=5):
            continue
        c = cell_id(lat, lon,global_grid)
        key = (observed.date().isoformat(), c)
        item = groups.setdefault(key, {
            'id': f'{key[0]}_{c[0]}_{c[1]}', 'date': key[0],
            'latitude': lat, 'longitude': lon, 'n_observations': 0,
            'first': observed, 'last': observed, 'products': set(),
        })
        item['n_observations'] += 1
        item['first'] = min(item['first'], observed)
        item['last'] = max(item['last'], observed)
        item['products'].add(row.get('_source', 'VIIRS'))
    return [{
        'id': x['id'], 'date': x['date'],
        'latitude': round(x['latitude'], 5), 'longitude': round(x['longitude'], 5),
        'n_observations': x['n_observations'],
        'first_satellite_observation_utc': _utc_iso(x['first']),
        'last_satellite_observation_utc': _utc_iso(x['last']),
        'minutes_since_last_observation': max(0, int((checked-x['last']).total_seconds()//60)),
        'products': sorted(x['products']),
    } for x in groups.values()]


def _record_first_check(clusters: list[dict], checked: datetime) -> None:
    stamp = _utc_iso(checked)
    with connection() as conn:
        for item in clusters:
            conn.execute('''INSERT OR IGNORE INTO watch_discoveries
              (cluster_key, first_satellite_observation_utc, first_site_check_utc)
              VALUES (?, ?, ?)''', (item['id'], item['first_satellite_observation_utc'], stamp))
        ids = [x['id'] for x in clusters]
        if not ids:
            return
        stored = {}
        for start in range(0, len(ids), 500):
            batch = ids[start:start+500]
            placeholders = ','.join('?' * len(batch))
            for row in conn.execute(f'SELECT cluster_key, first_site_check_utc FROM watch_discoveries WHERE cluster_key IN ({placeholders})', batch):
                stored[row['cluster_key']] = row['first_site_check_utc']
        for item in clusters:
            first_check = stored[item['id']]
            observed = datetime.fromisoformat(item['first_satellite_observation_utc'].replace('Z', '+00:00'))
            site_seen = datetime.fromisoformat(first_check.replace('Z', '+00:00'))
            item['first_blindspot_check_utc'] = first_check
            item['minutes_observation_to_first_check'] = max(0, int((site_seen-observed).total_seconds()//60))


def live_watch(region: str) -> dict:
    if region not in REGIONS:
        raise ValueError('Unsupported region')
    key = os.getenv('FIRMS_MAP_KEY', '').strip()
    if not key:
        return {'status': 'not_configured', 'region': region, 'checked_at_utc': None,
                'alerts': [], 'note': 'No live FIRMS key. This is NOT evidence of no current fires.',
                'verified_wildfires': False}
    now = datetime.now(timezone.utc)
    with _cache_lock:
        cached = _cached.get(region)
        if cached and time.monotonic() - cached[0] < CACHE_SECONDS:
            return cached[1]
    bbox = ','.join(str(x) for x in REGIONS[region]['bbox'])
    start = (now - timedelta(days=1)).date().isoformat()
    rows = []
    sources_ok = []
    failed_sources = []
    with httpx.Client(timeout=22, follow_redirects=False) as client:
        for product in LIVE_PRODUCTS:
            # NASA Area API requests return a 2-day window beginning at start.
            # The API key is NEVER returned in responses, errors, logs, or UI.
            url = f'{NASA_BASE}/{key}/{product}/{bbox}/2/{start}'
            try:
                response = client.get(url)
                response.raise_for_status()
                body = response.text.lstrip('\ufeff')
                if '<html' in body[:200].lower():
                    raise ValueError('Unexpected response content')
                reader = csv.DictReader(io.StringIO(body))
                names = {n.lower().strip() for n in (reader.fieldnames or []) if n}
                if not {'latitude', 'longitude', 'acq_date', 'acq_time'}.issubset(names):
                    raise ValueError('Missing FIRMS CSV columns')
                for j, raw in enumerate(reader):
                    if j >= 100000:
                        raise ValueError('Too many NRT records; narrow the region')
                    cleaned = {str(k).lower().strip(): v for k, v in raw.items() if k}
                    cleaned['_source'] = product
                    rows.append(cleaned)
                sources_ok.append(product)
            except (httpx.HTTPError, ValueError) as exc:
                # Do not stringify exception: URL contains private key.
                failed_sources.append({'product': product, 'reason': 'NASA feed unavailable or invalid response'})
    if not sources_ok:
        return {'status': 'unavailable', 'region': region, 'checked_at_utc': _utc_iso(now),
                'alerts': [], 'failed_sources': failed_sources,
                'note': 'Unable to check live satellite data. Do not infer an absence of active fires.',
                'verified_wildfires': False}
    # Limit to last 48h of detections, excluding earlier items from the returned 2-day window.
    cutoff = now - timedelta(hours=48)
    rows = [r for r in rows if (dt := _parse_acquired(r)) and cutoff <= dt <= now + timedelta(minutes=5)]
    clusters = build_clusters(rows, now,REGIONS[region].get("grid_projection")=="global")
    init_db()
    _record_first_check(clusters, now)
    clusters.sort(key=lambda c: c['last_satellite_observation_utc'], reverse=True)
    result = {
        'status': 'partial' if failed_sources else 'ok',
        'region': region, 'checked_at_utc': _utc_iso(now),
        'source_products': sources_ok, 'failed_sources': failed_sources,
        'total_potential_hotspot_clusters': len(clusters),
        'alerts': clusters[:15], 'window_hours': 48,
        'verified_wildfires': False,
        'note': ('Thermal anomalies / presumed vegetation hotspots, NOT official active wildfire incidents. '
                 'Ignition/start time, NASA publication time, and official posting delay are unknown. '
                 'The site-check gap is observation-to-our-first-successful-fetch, NOT reporting latency.'),
    }
    with _cache_lock:
        _cached[region] = (time.monotonic(), result)
    return result
