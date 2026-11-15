"""NASA archive ZIP ingestion is idempotent and needs no API key/unzipping."""
from __future__ import annotations
import os
import sqlite3
import subprocess
import sys
import zipfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]

def test_zip_importer_without_unzip(tmp_path):
    modis=tmp_path/'modis.zip'
    viirs=tmp_path/'viirs.zip'
    def make(path,lat):
        csvdata=f'latitude,longitude,acq_date,acq_time,frp\n{lat},-115.0,2023-08-13,0912,10\n'
        with zipfile.ZipFile(path,'w') as z:
            z.writestr('fire_archive.csv',csvdata)
    make(modis,54.2);make(viirs,54.3)
    db=tmp_path/'import-test.sqlite3'
    env={**os.environ,'BLINDSPOT_DB_PATH':str(db)}
    command=[sys.executable,str(ROOT/'scripts'/'import_firms_archives.py'), '--modis',str(modis),'--viirs',str(viirs)]
    r=subprocess.run(command,cwd=ROOT,env=env,text=True,capture_output=True)
    assert r.returncode==0,r.stderr
    assert '1 inserted' in r.stdout
    r=subprocess.run(command,cwd=ROOT,env=env,text=True,capture_output=True)
    assert r.returncode==0,r.stderr
    assert '0 inserted' in r.stdout
    with sqlite3.connect(db) as c:
        assert c.execute("SELECT COUNT(*) FROM observations WHERE mode='real'").fetchone()[0]==2
