"""One-time idempotent backfill of NASA FIRMS 'type' from the original ZIPs.
This never creates extra observations; it only classifies existing rows by stable UID.
"""
from __future__ import annotations
import argparse, csv, io, sys, zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'backend'))
from app.storage import init_db, connection, normalize_row


def backfill(path,product):
    seen=typed=0
    batch=[]
    with zipfile.ZipFile(path) as archive:
        items=[f for f in archive.namelist() if f.lower().endswith('.csv')]
        if len(items)!=1:raise ValueError('Expected one FIRMS CSV inside '+str(path))
        with archive.open(items[0]) as stream,io.TextIOWrapper(stream,encoding='utf-8-sig',newline='') as file:
            reader=csv.DictReader(file)
            with connection() as conn:
                for item in reader:
                    row={str(k).lower().strip():v for k,v in item.items() if k}
                    v=normalize_row(row,product)
                    seen+=1
                    if v is None:continue
                    batch.append((v[-1],v[0]))
                    if len(batch)>=5000:
                        conn.executemany('UPDATE observations SET fire_type=? WHERE uid=?',batch)
                        typed+=len(batch); batch.clear()
                if batch:
                    conn.executemany('UPDATE observations SET fire_type=? WHERE uid=?',batch)
                    typed+=len(batch)
                # Full requested NASA archive May-Oct 2023, even if no observations on some days.
                conn.execute('INSERT OR IGNORE INTO archive_coverage (product,start_day,end_day,source_file) VALUES (?,?,?,?)',
                             (product,'2023-05-01','2023-10-31',Path(path).name))
    return seen,typed

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--modis',default=str(ROOT/'data/raw/DL_FIRE_M-C61_849825.zip'))
    parser.add_argument('--viirs',default=str(ROOT/'data/raw/DL_FIRE_SV-C2_849826(1).zip'))
    options=parser.parse_args()
    init_db()
    for product,path in [('MODIS_SP',options.modis),('VIIRS_SNPP_SP',options.viirs)]:
        print(product,backfill(path,product),flush=True)
    with connection() as conn:
        print([tuple(r) for r in conn.execute("SELECT product,fire_type,COUNT(*) FROM observations WHERE mode='real' GROUP BY product,fire_type ORDER BY product,fire_type")])
