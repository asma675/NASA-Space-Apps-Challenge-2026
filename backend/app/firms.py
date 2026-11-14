"""NASA FIRMS server-side importer. Credentials never go to the client."""
from __future__ import annotations
import csv
import io
import os
from datetime import date, timedelta
import httpx
from .storage import SOURCES, normalize_row, insert_rows, REGIONS

NASA_BASE = "https://firms.modaps.eosdis.nasa.gov/api/area/csv"


def parse_csv(csv_text: str, product: str, mode="real", origin="NASA FIRMS"):
    if product not in SOURCES:
        raise ValueError("Unsupported FIRMS product")
    if "<html" in csv_text.lower()[:200]:
        raise ValueError("The server returned HTML, not a NASA FIRMS CSV")
    data = io.StringIO(csv_text.lstrip("\ufeff"))
    reader = csv.DictReader(data)
    names = {n.lower().strip() for n in (reader.fieldnames or [])}
    if not {"latitude","longitude","acq_date"}.issubset(names):
        raise ValueError("CSV must contain FIRMS latitude, longitude and acq_date columns")
    normalized=[]
    for line_num, raw in enumerate(reader):
        if line_num >= 125000:
            raise ValueError("Import exceeds 125,000 records. Split the file into smaller batches.")
        row={str(k).lower().strip():v for k,v in raw.items() if k is not None}
        result=normalize_row(row,product,mode,origin)
        if result: normalized.append(result)
    return normalized


def fetch_nasa(region: str, start: date, end: date, products: list[str]):
    key = os.getenv("FIRMS_MAP_KEY", "").strip()
    if not key:
        raise ValueError("Set FIRMS_MAP_KEY in your .env file")
    if region not in REGIONS: raise ValueError("Invalid supported region")
    if not products or any(p not in SOURCES for p in products):
        raise ValueError("Invalid sensor selections")
    if start>end or (end-start).days>20:
        raise ValueError("Maximum 21-day window for the interactive NASA fetch; use archive CSV for longer periods")
    bbox=','.join(str(x) for x in REGIONS[region]["bbox"])
    total=0
    requests=0
    with httpx.Client(timeout=40, follow_redirects=False) as client:
        for product in products:
            cursor=start
            while cursor<=end:
                days=min(5, (end-cursor).days+1)
                url=f"{NASA_BASE}/{key}/{product}/{bbox}/{days}/{cursor.isoformat()}"
                try:
                    response=client.get(url)
                    response.raise_for_status()
                except httpx.HTTPError as e:
                    status = e.response.status_code if isinstance(e, httpx.HTTPStatusError) else "network error"
                    # Never echo an exception URL: it contains the server-side NASA MAP_KEY.
                    raise ValueError(f"NASA FIRMS request failed for {product}, {cursor} (status: {status}). Check key, source availability and dates.") from e
                normalized=parse_csv(response.text,product,origin=f"NASA FIRMS API ({product})")
                total+=insert_rows(normalized)
                requests+=1
                cursor += timedelta(days=days)
    return {"inserted":total,"requests":requests,"products":products}
