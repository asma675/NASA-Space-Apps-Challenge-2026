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
    "northern_ontario": {"name": "Northern Ontario", "bbox": [-94.0, 47.0, -79.0, 56.0], "center": [51.4, -85.7], "zoom": 5},
    "alberta_boreal": {"name": "Alberta Boreal", "bbox": [-120.0, 53.0, -110.0, 60.0], "center": [56.5, -115.0], "zoom": 6},
    "bc_interior": {"name": "B.C. Interior", "bbox": [-124.0, 49.0, -116.0, 56.0], "center": [52.6, -120.0], "zoom": 6},
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
          frp REAL
        );
        CREATE INDEX IF NOT EXISTS idx_obs_analysis ON observations(mode,acq_date,latitude,longitude);
        CREATE INDEX IF NOT EXISTS idx_obs_product ON observations(product);
        """)


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
    # Satellite time and coordinates form a stable record identity; preserves distinct passes.
    ident = "|".join((product, day, acq_time, f"{lat:.5f}", f"{lon:.5f}",mode))
    return (hashlib.sha256(ident.encode()).hexdigest(),product,SOURCES[product],mode,origin,day,
            acq_time,lat,lon,confidence,frp)


def insert_rows(rows: Iterable[tuple]):
    with connection() as conn:
        before = conn.total_changes
        conn.executemany("""INSERT OR IGNORE INTO observations
             (uid, product, family, mode, origin, acq_date, acq_time, latitude, longitude, confidence, frp)
             VALUES (?,?,?,?,?,?,?,?,?,?,?)""", rows)
        return conn.total_changes - before


def get_rows(mode: str, region: str, start: str, end: str, limit: int = 250000):
    bbox = REGIONS[region]["bbox"]
    with connection() as conn:
        return [dict(r) for r in conn.execute("""SELECT * FROM observations WHERE mode=?
          AND acq_date>=? AND acq_date<=? AND longitude BETWEEN ? AND ?
          AND latitude BETWEEN ? AND ? ORDER BY acq_date, product, uid LIMIT ?""",
          (mode,start,end,bbox[0],bbox[2],bbox[1],bbox[3],limit))]


def counts():
    with connection() as conn:
        rows = conn.execute("SELECT mode,product,origin,COUNT(*) as count FROM observations GROUP BY mode,product,origin").fetchall()
    return [dict(row) for row in rows]
