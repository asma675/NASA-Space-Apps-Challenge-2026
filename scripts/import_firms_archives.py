"""Stream original NASA FIRMS historical ZIP archives directly into BLINDSPOT SQLite.

Examples (PowerShell from project root):
    py scripts/import_firms_archives.py --modis "data/raw/DL_FIRE_M-C61_849825.zip" --viirs "data/raw/DL_FIRE_SV-C2_849826(1).zip"

Re-running is safe: observations have a source/product/date/time/coordinate UID,
and INSERT OR IGNORE prevents duplicate copies. No manual unzipping or API key.
"""
from __future__ import annotations
import argparse
import csv
import io
import sys
import zipfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'backend'))
from app.storage import init_db, normalize_row, insert_rows, db_path, connection  # noqa: E402

ARCHIVES = [
    ('modis','MODIS_SP','NASA FIRMS historical archive #849825, MODIS C6.1, Alberta 2023'),
    ('viirs','VIIRS_SNPP_SP','NASA FIRMS historical archive #849826, S-NPP VIIRS C2, Alberta 2023'),
]


def run_archive(zip_path: Path, product: str, origin: str, record_coverage: bool=True):
    if not zip_path.is_file():
        raise FileNotFoundError(f'NASA archive not found: {zip_path}')
    parsed=invalid=inserted=0
    oldest=newest=None
    batch=[]
    with zipfile.ZipFile(zip_path) as z:
        matches=[i for i in z.infolist() if i.filename.lower().endswith('.csv') and not i.is_dir()]
        if len(matches)!=1:
            raise ValueError(f'Expected exactly 1 FIRMS CSV within {zip_path.name}, found {len(matches)}')
        with z.open(matches[0]) as raw, io.TextIOWrapper(raw,encoding='utf-8-sig',newline='') as text:
            reader=csv.DictReader(text)
            columns={s.lower().strip() for s in (reader.fieldnames or [])}
            if not {'latitude','longitude','acq_date','acq_time'}.issubset(columns):
                raise ValueError('Missing FIRMS CSV latitude, longitude, acquisition date/time columns')
            for row in reader:
                parsed+=1
                day=str(row.get('acq_date',''))[:10]
                if len(day)==10 and day[:4].isdigit():
                    oldest=day if oldest is None or day<oldest else oldest
                    newest=day if newest is None or day>newest else newest
                data={str(k).lower().strip(): v for k,v in row.items() if k}
                val=normalize_row(data,product,'real',origin)
                if val is None:
                    invalid+=1
                    continue
                batch.append(val)
                if len(batch)>=5000:
                    inserted+=insert_rows(batch)
                    batch.clear()
            if batch:
                inserted+=insert_rows(batch)
    if record_coverage and oldest and newest:
        with connection() as conn:
            conn.execute("INSERT OR IGNORE INTO archive_coverage (product,start_day,end_day,source_file) VALUES (?,?,?,?)",
                         (product,oldest,newest,str(zip_path.name)))
    return {'source_file':str(zip_path),'product':product,'parsed':parsed,'invalid':invalid,
            'inserted':inserted,'already_present_or_duplicate':parsed-invalid-inserted}


def main():
    parser=argparse.ArgumentParser(description='Load original NASA MODIS/VIIRS ZIP files; no manual extraction or API key.')
    parser.add_argument('--modis',type=Path,required=True,help='NASA MODIS C6.1 ZIP archive')
    parser.add_argument('--viirs',type=Path,required=True,help='NASA S-NPP VIIRS C2 ZIP archive (one copy only)')
    args=parser.parse_args()
    init_db()
    for name, product, origin in ARCHIVES:
        stats=run_archive(getattr(args,name),product,origin)
        print(f"{name.upper()}: {stats['parsed']:,} rows read, {stats['inserted']:,} inserted, {stats['invalid']:,} invalid, {stats['already_present_or_duplicate']:,} duplicate/already stored")
    print('Database:',db_path())
    with connection() as conn:
        print('Stored real:',conn.execute("SELECT product, COUNT(*) FROM observations WHERE mode='real' GROUP BY product").fetchall())

if __name__=='__main__': main()
