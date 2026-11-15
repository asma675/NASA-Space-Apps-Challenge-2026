"""SQLite storage and integrity checks for NASA FIRMS active-fire observations."""
from __future__ import annotations
import hashlib
import os
import sqlite3
from contextlib import contextmanager
from datetime import date
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parents[2]
REGIONS = {
    "world": {"name":"World · loaded archive coverage only", "bbox":[-180.0,-90.0,180.0,90.0],"center":[10.0,0.0],"zoom":2,"grid_projection":"global"},
    "amazon": {"name":"Amazon Basin", "bbox":[-80.0,-20.0,-45.0,8.0],"center":[-4.0,-62.0],"zoom":4,"grid_projection":"global"},
    "australia": {"name":"Australia", "bbox":[112.0,-44.0,154.0,-10.0],"center":[-26.0,133.0],"zoom":4,"grid_projection":"global"},
    "mediterranean": {"name":"Mediterranean Basin", "bbox":[-11.0,29.0,39.0,47.0],"center":[38.0,14.0],"zoom":4,"grid_projection":"global"},
    "southern_africa": {"name":"Southern Africa", "bbox":[10.0,-35.0,42.0,-12.0],"center":[-25.0,26.0],"zoom":4,"grid_projection":"global"},
    "southeast_asia": {"name":"Southeast Asia", "bbox":[92.0,-11.0,145.0,24.0],"center":[7.0,117.0],"zoom":4,"grid_projection":"global"},
    "western_us": {"name":"Western United States", "bbox":[-125.0,30.0,-102.0,50.0],"center":[40.0,-115.0],"zoom":5,"grid_projection":"global"},
    "northern_ontario": {"name": "Northern Ontario", "bbox": [-94.0, 47.0, -79.0, 56.0], "center": [51.4, -85.7], "zoom": 5, "grid_projection":"global"},
    "alberta_boreal": {"name": "Alberta Boreal", "bbox": [-120.0, 53.0, -110.0, 60.0], "center": [56.5, -115.0], "zoom": 6, "grid_projection":"global"},
    "alberta_province": {"name": "Alberta (province archive)", "bbox": [-120.4, 48.8, -109.6, 60.3], "center": [54.2, -115.0], "zoom": 5, "grid_projection":"global"},
    "bc_interior": {"name": "B.C. Interior", "bbox": [-124.0, 49.0, -116.0, 56.0], "center": [52.6, -120.0], "zoom": 6, "grid_projection":"global"},
}
SOURCES = {
    "MODIS_SP": "MODIS",
    "MODIS_NRT": "MODIS",
    "VIIRS_SNPP_SP": "VIIRS",
    "VIIRS_SNPP_NRT": "VIIRS",
    "VIIRS_NOAA20_SP": "VIIRS",
    "VIIRS_NOAA20_NRT": "VIIRS",
    "VIIRS_NOAA21_SP": "VIIRS",
    "VIIRS_NOAA21_NRT": "VIIRS",
}


def db_path() -> Path:
    return Path(os.getenv("BLINDSPOT_DB_PATH", str(ROOT / "data" / "blindspot.sqlite3")))


@contextmanager
def connection():
    path = db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path, timeout=10)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    with connection() as conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS observations (
          uid TEXT PRIMARY KEY,
          product TEXT NOT NULL,
          family TEXT NOT NULL,
          mode TEXT NOT NULL CHECK (mode IN ('demo','real')),
          origin TEXT NOT NULL,
          acq_date TEXT NOT NULL,
          acq_time TEXT,
          latitude REAL NOT NULL,
          longitude REAL NOT NULL,
          confidence TEXT,
          frp REAL,
          fire_type INTEGER
        );
        CREATE INDEX IF NOT EXISTS idx_obs_analysis ON observations(mode,acq_date,latitude,longitude);
        CREATE INDEX IF NOT EXISTS idx_obs_product ON observations(product);
        CREATE TABLE IF NOT EXISTS archive_coverage (
          product TEXT NOT NULL, start_day TEXT NOT NULL, end_day TEXT NOT NULL,
          source_file TEXT NOT NULL, PRIMARY KEY(product,start_day,end_day,source_file)
        );
        CREATE TABLE IF NOT EXISTS watch_discoveries (
          cluster_key TEXT PRIMARY KEY,
          first_satellite_observation_utc TEXT NOT NULL,
          first_site_check_utc TEXT NOT NULL
        );
        """)
        existing={r[1] for r in conn.execute("PRAGMA table_info(observations)")}
        if 'fire_type' not in existing:
            conn.execute('ALTER TABLE observations ADD COLUMN fire_type INTEGER')
        columns={r[1] for r in conn.execute('PRAGMA table_info(archive_coverage)')}
        if 'scope' not in columns:
            # All pre-bundled archive metadata was downloaded for Alberta; never
            # present it as complete global or continent-wide satellite coverage.
            conn.execute("ALTER TABLE archive_coverage ADD COLUMN scope TEXT NOT NULL DEFAULT 'alberta_province'")


def safe_float(value):
    try:
        v = float(value)
        return v if abs(v) < 1e10 else None
    except (ValueError, TypeError):
        return None


def normalize_row(raw: dict, product: str, mode: str = "real", origin: str = "NASA FIRMS"):
    if product not in SOURCES:
        raise ValueError("Unsupported FIRMS sensor product")
    lat = safe_float(raw.get("latitude"))
    lon = safe_float(raw.get("longitude"))
    day = str(raw.get("acq_date", "")).strip()[:10]
    if lat is None or lon is None or not (-90 <= lat <= 90 and -180 <= lon <= 180):
        return None
    try:
        date.fromisoformat(day)
    except ValueError:
        return None
    acq_time = str(raw.get("acq_time", "")).strip().zfill(4)[:4]
    confidence = str(raw.get("confidence", "")).strip()[:20]
    frp = safe_float(raw.get("frp"))
    try:
        fire_type = int(str(raw.get('type','')).strip())
        if fire_type not in (0,1,2,3): fire_type=None
    except (TypeError,ValueError):
        fire_type = None
    # Satellite time and coordinates form a stable record identity; preserves distinct passes.
    ident = "|".join((product, day, acq_time, f"{lat:.5f}", f"{lon:.5f}",mode))
    return (hashlib.sha256(ident.encode()).hexdigest(),product,SOURCES[product],mode,origin,day,
            acq_time,lat,lon,confidence,frp,fire_type)


def insert_rows(rows: Iterable[tuple]):
    with connection() as conn:
        before = conn.total_changes
        conn.executemany("""INSERT OR IGNORE INTO observations
             (uid, product, family, mode, origin, acq_date, acq_time, latitude, longitude, confidence, frp, fire_type)
             VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""", rows)
        return conn.total_changes - before


def get_rows(mode: str, region: str, start: str, end: str, limit: int | None = None, custom_bbox=None):
    """Stream qualifying rows without a silent 1M cutoff (safe for multi-year archives).

    A cursor is kept open until the caller finishes iterating. Memory usage tracks
    the number of distinct grid-days in analysis, not individual raw detections.
    """
    bbox = custom_bbox if custom_bbox else REGIONS[region]["bbox"]
    sql = """SELECT * FROM observations WHERE mode=?
      AND acq_date>=? AND acq_date<=? AND longitude BETWEEN ? AND ?
      AND latitude BETWEEN ? AND ?
      AND (mode!='real' OR fire_type=0 OR fire_type IS NULL)
      ORDER BY acq_date, product, uid"""
    params=[mode,start,end,bbox[0],bbox[2],bbox[1],bbox[3]]
    if limit is not None:
        sql+=' LIMIT ?'; params.append(limit)
    with connection() as conn:
        for r in conn.execute(sql,params):
            yield dict(r)


def counts():
    with connection() as conn:
        rows = conn.execute("SELECT mode,product,origin,COUNT(*) as count FROM observations GROUP BY mode,product,origin").fetchall()
    return [dict(row) for row in rows]
