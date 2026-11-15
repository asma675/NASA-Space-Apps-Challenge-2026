"""Official Canadian agency incident records: independent context, NOT satellite truth labels.

Alberta publishes its historical fire register under the Open Government Licence.
Satellite hotspots (radiometric observations) and agency wildfire incident points (fire
origins) have different measurement definitions and never share an ID in this app.
"""
from __future__ import annotations

import csv
import io
import re
import sqlite3
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Iterable

from .storage import connection, safe_float

ALBERTA_DATASET = 'https://open.canada.ca/data/en/dataset/a221e7a0-4f46-4be7-9c5a-e29de9a3447e'
ALBERTA_CSV_URL = ('https://open.alberta.ca/dataset/a221e7a0-4f46-4be7-9c5a-e29de9a3447e/'
    'resource/80480824-0c50-456c-9723-f9d4fc136141/download/fp-historical-wildfire-data-2006-2025.csv')
CWFIS = 'https://cwfis.cfs.nrcan.gc.ca/en/'
CWFIS_DATA = 'https://cwfis.cfs.nrcan.gc.ca/en/catalogue'
NBAC = 'https://cwfis.cfs.nrcan.gc.ca/downloads/nbac/'
AGENCY_SOURCE = 'Government of Alberta — Historical wildfire data 2006–2025'


def init_agency_db() -> None:
    with connection() as conn:
        conn.executescript('''
        CREATE TABLE IF NOT EXISTS agency_fires (
            source TEXT NOT NULL,
            fire_id TEXT NOT NULL,
            year INTEGER NOT NULL,
            latitude REAL NOT NULL,
            longitude REAL NOT NULL,
            area_ha REAL,
            cause TEXT,
            fire_start TEXT,
            discovered TEXT,
            reported TEXT,
            PRIMARY KEY (source, fire_id, year)
        );
        CREATE INDEX IF NOT EXISTS idx_agency_year ON agency_fires (year);
        ''')


def parse_date(raw: str | None) -> str | None:
    """Accept source-documented timestamps, never invent timezone or precision."""
    value = str(raw or '').strip()
    if not value or value.lower() in {'none', 'null', 'nan', 'nat', '-'}:
        return None
    cleaned = value.replace('T', ' ').replace('Z', '+00:00')
    try:
        return datetime.fromisoformat(cleaned).isoformat(sep=' ', timespec='seconds')
    except ValueError:
        pass
    for fmt in ('%m/%d/%Y %H:%M:%S', '%m/%d/%Y %H:%M',
                '%Y/%m/%d %H:%M:%S', '%Y/%m/%d %H:%M',
                '%m/%d/%Y', '%Y/%m/%d', '%b %d, %Y %I:%M %p'):
        try:
            return datetime.strptime(value, fmt).isoformat(sep=' ', timespec='seconds')
        except ValueError:
            continue
    return None


def _value(row: dict, *names: str):
    for name in names:
        v = row.get(name)
        if v is not None and str(v).strip():
            return v
    return None


def normalize_incident(raw: dict, line: int, source: str = AGENCY_SOURCE):
    row = {re.sub(r'[^a-z0-9]+', '_', str(k).lower().strip()).strip('_'): v
           for k, v in raw.items() if k}
    try:
        year = int(str(_value(row, 'year', 'fire_year') or '').strip())
    except ValueError:
        return None
    lat = safe_float(_value(row, 'latitude', 'lat'))
    lon = safe_float(_value(row, 'longitude', 'lon', 'long'))
    if not (1990 <= year <= 2100 and lat is not None and lon is not None and
            48 <= lat <= 61 and -122 <= lon <= -108):
        return None
    fire_id = str(_value(row, 'fire_number', 'fire_id', 'fire_label') or '').strip()
    if not fire_id:
        # Do not synthesize a position-based ID and present it as a verified fire number.
        return None
    area = safe_float(_value(row, 'current_size', 'area_estimate', 'area_ha'))
    return (source, fire_id, year, lat, lon, area if area is not None and area >= 0 else None,
            str(_value(row, 'general_cause', 'cause') or 'Unknown')[:100],
            parse_date(_value(row, 'fire_start_date')),
            parse_date(_value(row, 'discovered_date')),
            parse_date(_value(row, 'reported_date')))


def import_agency_csv(stream: Iterable[str], source: str = AGENCY_SOURCE) -> dict:
    init_agency_db()
    reader = csv.DictReader(stream)
    fields = {re.sub(r'[^a-z0-9]+','_',str(k).lower().strip()).strip('_') for k in (reader.fieldnames or [])}
    if not {'latitude', 'longitude'}.issubset(fields) or not ({'fire_number','fire_id','fire_label'} & fields) or not ({'year','fire_year'} & fields):
        raise ValueError('Expected official agency CSV columns: year, fire_number, latitude, longitude')
    parsed, skipped, inserted = 0, 0, 0
    with connection() as conn:
        for n, raw in enumerate(reader, start=2):
            if n > 500000:
                raise ValueError('CSV exceeds 500,000 incident rows')
            row = normalize_incident(raw, n, source)
            if row is None:
                skipped += 1
                continue
            parsed += 1
            cur = conn.execute('''INSERT INTO agency_fires
                (source,fire_id,year,latitude,longitude,area_ha,cause,fire_start,discovered,reported)
                VALUES (?,?,?,?,?,?,?,?,?,?) ON CONFLICT(source,fire_id,year) DO UPDATE SET
                latitude=excluded.latitude,longitude=excluded.longitude,area_ha=excluded.area_ha,
                cause=excluded.cause,fire_start=excluded.fire_start,
                discovered=excluded.discovered,reported=excluded.reported''', row)
            # total_changes includes updates; report this as processed/upserted, not unique new fires
            inserted += 1
    return {'status':'ok', 'source':source,'accepted_or_updated':inserted,'invalid_or_skipped':skipped,
            'parsed':parsed,'note':'Rows were upserted idempotently; repeat imports do not add duplicate incidents.'}


def agency_context(year: int = 2023) -> dict:
    if not 2000 <= year <= 2100:
        raise ValueError('Invalid year')
    init_agency_db()
    with connection() as conn:
        all_rows = [dict(x) for x in conn.execute('''SELECT fire_id,year,latitude,longitude,area_ha,cause,
             fire_start,discovered,reported FROM agency_fires WHERE year=? ORDER BY fire_id''',(year,))]
    if not all_rows:
        return {'status':'not_imported','year':year,'source':AGENCY_SOURCE,
           'count':None,'cause_counts':[], 'monthly':[], 'points':[], 'discovery_to_report':None,
           'note':'No official Alberta wildfire incident records imported for this year. Zero is NOT implied.',
           'links':{'alberta':ALBERTA_DATASET,'cwfis':CWFIS,'catalogue':CWFIS_DATA,'nbac':NBAC}}
    causes=Counter(r['cause'] or 'Unknown' for r in all_rows)
    months=Counter()
    gaps=[]
    for r in all_rows:
        stamp=r['discovered'] or r['reported'] or r['fire_start']
        if stamp and stamp[:4]==str(year):months[stamp[:7]]+=1
        if r['discovered'] and r['reported']:
            try:
                start=datetime.fromisoformat(r['discovered']);end=datetime.fromisoformat(r['reported'])
                gap=(end-start).total_seconds()/60
                if 0 <= gap <= 30*24*60: gaps.append(gap)
            except (ValueError,TypeError):pass
    gaps.sort()
    return {'status':'loaded','year':year, 'source':AGENCY_SOURCE,'count':len(all_rows),
        'cause_counts':[{'cause':k,'count':v} for k,v in causes.most_common(6)],
        'monthly':[{'month':f'{year}-{m:02d}', 'count':months.get(f'{year}-{m:02d}',0)} for m in range(1,13)],
        'discovery_to_report':{'sample_size':len(gaps),
               'median_minutes':round(gaps[len(gaps)//2],1) if gaps else None,
               'definition':'Alberta agency discovered_date to reported_date, NOT NASA detection delay or website posting time'},
        'points':[{'fire_id':r['fire_id'],'latitude':r['latitude'],'longitude':r['longitude'],
                   'area_ha':r['area_ha'],'cause':r['cause'],
                   'discovered':r['discovered'],'reported':r['reported']}
                  for r in all_rows[::max(1, (len(all_rows)+299)//300)][:300]],
        'sampled_points':min(300,len(all_rows)),
        'note':'Agency fire origin locations are independently reported INCIDENTS, not satellite observations. Counts have different denominators and may cover only the Forest Protection Area. Do not interpret proximity as definitive sensor validation.',
        'links':{'alberta':ALBERTA_DATASET,'cwfis':CWFIS,'catalogue':CWFIS_DATA,'nbac':NBAC}}
