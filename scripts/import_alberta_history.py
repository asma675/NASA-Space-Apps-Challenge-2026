"""Ingest an OFFICIAL Alberta fire history CSV (no keys required). Run from repository root.

Example: py scripts/import_alberta_history.py --csv data/raw/fp-historical-wildfire-data-2006-2025.csv
Or:      py scripts/import_alberta_history.py --download
"""
import argparse
import csv
import io
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'backend'))
from app.canada import ALBERTA_CSV_URL, import_agency_csv, agency_context


def main():
    p=argparse.ArgumentParser(description='Import Canadian official wildfire incident history, kept distinct from NASA hotspots.')
    p.add_argument('--csv',type=Path,help='Path to official Alberta CSV downloaded from open.alberta.ca')
    p.add_argument('--download',action='store_true',help='Download CSV from current official Alberta open-data portal URL')
    args=p.parse_args()
    if not args.csv and not args.download:p.error('Use --csv FILENAME or --download')
    if args.download:
        import httpx
        path=ROOT/'data'/'raw'/'fp-historical-wildfire-data-2006-2025.csv'
        path.parent.mkdir(parents=True,exist_ok=True)
        print('Downloading official Alberta history (network required):',ALBERTA_CSV_URL)
        try:
            with httpx.stream('GET',ALBERTA_CSV_URL,timeout=50,follow_redirects=True) as resp:
                resp.raise_for_status()
                content_type=resp.headers.get('content-type','')
                with path.open('wb') as out:
                    for chunk in resp.iter_bytes():out.write(chunk)
                if path.stat().st_size > 100_000_000:
                    path.unlink(missing_ok=True);raise ValueError('CSV file too large')
        except Exception as exc:
            path.unlink(missing_ok=True)
            raise SystemExit(f'Official download unavailable: {exc}. Download manually from {ALBERTA_CSV_URL}')
        args.csv=path
    with args.csv.open('r',encoding='utf-8-sig',newline='') as f:
        result=import_agency_csv(f)
    print(result)
    print('2023 verification:',{k:v for k,v in agency_context(2023).items() if k in ('status','count','discovery_to_report')})

if __name__=='__main__':main()
