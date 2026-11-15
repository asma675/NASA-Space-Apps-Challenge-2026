"""Incremental multi-year NASA FIRMS archive importer with source-coverage contract.

PowerShell:
  py scripts/import_multi_year.py --modis data/raw/other/MODIS_2020.zip data/raw/other/MODIS_2021.zip \
      --viirs data/raw/other/VIIRS_2020.zip data/raw/other/VIIRS_2021.zip

Optional: --manifest data/raw/other/coverage.json with NASA request windows:
[
 {"file":"MODIS_2020.zip","product":"MODIS_SP","start":"2020-01-01","end":"2020-12-31"},
 {"file":"VIIRS_2020.zip","product":"VIIRS_SNPP_SP","start":"2020-01-01","end":"2020-12-31"}
]

Do not represent any interval as fully covered without an archive request window.
If omitted, a conservative observation-first/last interval is stored and such
months are eligible for baseline ONLY if detections reach both month boundaries.
"""
from __future__ import annotations
import argparse,json,sys
from datetime import date
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'backend'))
from app.storage import init_db,connection
from import_firms_archives import run_archive


def main():
    p=argparse.ArgumentParser(description='Import additional years of original NASA FIRMS ZIP archives.')
    p.add_argument('--modis',nargs='*',type=Path,default=[])
    p.add_argument('--viirs',nargs='*',type=Path,default=[])
    p.add_argument('--manifest',type=Path,help='Optional JSON with independently documented NASA archive windows and scope')
    p.add_argument('--scope',default='alberta_province',help='Spatial scope e.g. alberta_province, amazon, world. Use world ONLY if file covers entire Earth.')
    opts=p.parse_args()
    from app.storage import REGIONS
    if opts.scope not in REGIONS:p.error('Unknown geographic scope')
    if not opts.modis and not opts.viirs:p.error('Supply --modis and/or --viirs NASA ZIP archive files')
    entries={}
    if opts.manifest:
        for entry in json.loads(opts.manifest.read_text(encoding='utf-8')):
            f=Path(entry['file']).name
            product=entry['product']
            if product not in ('MODIS_SP','VIIRS_SNPP_SP'):raise ValueError(f'Unsupported product for {f}')
            start=date.fromisoformat(entry['start']);end=date.fromisoformat(entry['end'])
            if end<start:raise ValueError(f'Invalid coverage for {f}')
            scope=entry.get('scope',opts.scope)
            if scope not in REGIONS:raise ValueError(f'Unknown archive scope {scope}')
            entries[(f,product)]=(str(start),str(end),scope)
    init_db()
    for product,archives in [('MODIS_SP',opts.modis),('VIIRS_SNPP_SP',opts.viirs)]:
        for archive in archives:
            archive=archive.resolve()
            if not archive.is_file():raise FileNotFoundError(str(archive))
            result=run_archive(archive,product,f'NASA FIRMS user archive: {archive.name}',record_coverage=False)
            coverage=entries.get((archive.name,product))
            if coverage:
                with connection() as conn:
                    conn.execute('INSERT OR REPLACE INTO archive_coverage(product,start_day,end_day,source_file,scope) VALUES(?,?,?,?,?)',
                                 (product,coverage[0],coverage[1],archive.name,coverage[2]))
            print(product,archive.name,result, 'verified coverage='+str(coverage) if coverage else 'coverage inferred from detections only',flush=True)
    print('Import complete. Restart the server to refresh cached historical comparisons.')

if __name__=='__main__':main()
