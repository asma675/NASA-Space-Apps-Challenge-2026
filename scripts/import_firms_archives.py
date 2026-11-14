#!/usr/bin/env python3
"""Import NASA FIRMS archive ZIPs directly into BLINDSPOT SQLite, idempotently."""
from __future__ import annotations

import argparse
import csv
import io
import sys
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
from app.storage import init_db, normalize_row, connection  # noqa: E402


def import_zip(path: Path, product: str, request_id: str, batch_size: int = 5000):
    summary = {"parsed": 0, "inserted": 0, "duplicates": 0, "invalid": 0}
    with zipfile.ZipFile(path) as archive:
        csv_names = [n for n in archive.namelist() if n.lower().endswith(".csv")]
        if len(csv_names) != 1:
            raise ValueError(f"Expected one CSV in {path}, found {len(csv_names)}")
        with archive.open(csv_names[0]) as binary:
            stream = io.TextIOWrapper(binary, encoding="utf-8-sig", newline="")
            reader = csv.DictReader(stream)
            if not reader.fieldnames or not {"latitude", "longitude", "acq_date"}.issubset(reader.fieldnames):
                raise ValueError(f"Unexpected FIRMS columns in {path}: {reader.fieldnames}")
            batch = []
            with connection() as conn:
                for raw in reader:
                    summary["parsed"] += 1
                    row = normalize_row(raw, product, "real", f"NASA FIRMS archive request {request_id}; {path.name}")
                    if row is None:
                        summary["invalid"] += 1
                        continue
                    batch.append(row)
                    if len(batch) >= batch_size:
                        before = conn.total_changes
                        conn.executemany("""INSERT OR IGNORE INTO observations
                          (uid,product,family,mode,origin,acq_date,acq_time,latitude,longitude,confidence,frp)
                          VALUES (?,?,?,?,?,?,?,?,?,?,?)""", batch)
                        summary["inserted"] += conn.total_changes - before
                        batch.clear()
                if batch:
                    before = conn.total_changes
                    conn.executemany("""INSERT OR IGNORE INTO observations
                      (uid,product,family,mode,origin,acq_date,acq_time,latitude,longitude,confidence,frp)
                      VALUES (?,?,?,?,?,?,?,?,?,?,?)""", batch)
                    summary["inserted"] += conn.total_changes - before
            summary["duplicates"] = summary["parsed"] - summary["invalid"] - summary["inserted"]
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--modis", required=True, type=Path, help="NASA MODIS FIRMS ZIP")
    parser.add_argument("--viirs", required=True, type=Path, help="NASA S-NPP VIIRS FIRMS ZIP (one copy)")
    args = parser.parse_args()
    init_db()
    totals = {}
    for path, product, request_id in ((args.modis, "MODIS_SP", "849825"), (args.viirs, "VIIRS_SNPP_SP", "849826")):
        result = import_zip(path, product, request_id)
        totals[product] = result
        print(f"{product}: {result}")
    print(f"Done. Reruns are safe; unique rows are keyed by product/date/time/coordinates/mode.")


if __name__ == "__main__":
    main()
