"""Generate deterministic SYNTHETIC data strictly for illustrative onboarding.
This is NEVER NASA data and must never be used for claims about real fires.
"""
from __future__ import annotations
import random
import sys
from datetime import date, timedelta
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'backend'))
from app.storage import init_db, insert_rows, normalize_row, REGIONS


def seed():
    init_db()
    rng=random.Random(661382)
    rows=[]
    for r_idx, (region, spec) in enumerate(REGIONS.items()):
        west,south,east,north=spec['bbox']
        for year in (2021,2022,2023,2024):
            for month in range(1,13):
                # Intentionally synthetic seasonal shape. NOT modeled after actual historical events.
                seasonal={1:0,2:0,3:1,4:2,5:6,6:9,7:10,8:8,9:5,10:2,11:0,12:0}[month]
                n_days=round(seasonal*(0.75+rng.random()*.75))
                for d in sorted(rng.sample(range(1,29),min(n_days,28))):
                    day=f'{year:04d}-{month:02d}-{d:02d}'
                    n_cells=rng.randint(3,13)
                    for j in range(n_cells):
                        lat=rng.uniform(south+.8,north-.6)
                        lon=rng.uniform(west+.8,east-.6)
                        # Common site, with slight coordinate offsets between sensors.
                        variants= rng.choices([["MODIS_SP","VIIRS_SNPP_SP"],["MODIS_SP"],["VIIRS_SNPP_SP"]],weights=[6,2,3])[0]
                        for product in variants:
                            dlat=rng.uniform(-.015,.015)
                            dlon=rng.uniform(-.015,.015)
                            record={"latitude":round(lat+dlat,5),"longitude":round(lon+dlon,5),
                                    "acq_date":day,"acq_time":"1300","frp":rng.randint(5,125),"confidence":"nominal"}
                            row=normalize_row(record,product,"demo","SYNTHETIC — illustration only")
                            if row: rows.append(row)
    inserted=insert_rows(rows)
    print(f'Demo seed: {inserted} synthetic records inserted (duplicates ignored).')

if __name__=='__main__':
    seed()
