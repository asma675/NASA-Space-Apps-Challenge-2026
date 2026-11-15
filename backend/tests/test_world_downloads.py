"""New NASA World request #850371/#850372 verification and importer regression."""
from pathlib import Path
import csv,io,json,os,sqlite3,sys,zipfile
import pytest
from app.global_data import WORLD_DB,ready,global_analysis,global_investigation,global_inventory,month_classification
from app.storage import ROOT as PROJECT_ROOT

SCRIPTS=PROJECT_ROOT/'scripts'
if str(SCRIPTS) not in sys.path: sys.path.insert(0,str(SCRIPTS))
from build_world_grid import CREATE,index_zip


def test_two_csv_members_and_rerun_are_idempotent(tmp_path):
    path=tmp_path/'tiny-modis.zip'
    header='latitude,longitude,brightness,scan,track,acq_date,acq_time,satellite,instrument,confidence,version,bright_t31,frp,daynight,type\n'
    old=header+'10.0,20.0,300,1,1,2026-06-15,0120,T,MODIS,80,61,200,3,D,0\n10.0001,20.0001,300,1,1,2026-06-15,0121,T,MODIS,80,61,200,3,D,0\n10.0,20.0,300,1,1,2026-06-15,0122,T,MODIS,80,61,200,3,D,2\n'
    new=header.strip().rsplit(',',1)[0]+'\n' # ends with daynight only, no type
    new+='10.0,20.0,300,1,1,2026-09-01,0100,T,MODIS,80,6NRT,200,3,D\n'
    with zipfile.ZipFile(path,'w') as z:
        z.writestr('fire_archive_M-C61_850371.csv',old)
        z.writestr('fire_nrt_M-C61_850371.csv',new)
    c=sqlite3.connect(tmp_path/'global.sqlite3')
    c.executescript(CREATE)
    first=index_zip(path,'MODIS',c)
    second=index_zip(path,'MODIS',c)
    assert c.execute('SELECT COUNT(*) FROM import_days').fetchone()[0]==2
    assert c.execute('SELECT SUM(msp),SUM(mnrt) FROM cells').fetchone()==(2,1)
    assert c.execute('SELECT SUM(excluded) FROM import_days').fetchone()[0]==1
    assert c.execute('SELECT COUNT(*) FROM cells').fetchone()[0]==2
    assert c.execute('SELECT product FROM member_info ORDER BY product').fetchall()==[('MODIS_NRT',),('MODIS_SP',)]
    c.close()


@pytest.mark.skipif(not WORLD_DB.is_file(),reason='World source data only included in complete edition')
def test_real_world_archive_counts_and_monthly(monkeypatch):
    monkeypatch.delenv('BLINDSPOT_DB_PATH',raising=False)
    manifest=json.loads((PROJECT_ROOT/'data/global_archive_manifest.json').read_text())
    assert ready()
    assert manifest['raw_counts']=={'total':20659624,'eligible':19573939,'excluded':1085685}
    assert manifest['distinct_global_equal_earth_10km_utc_cell_days']==5708602
    coverage=global_inventory('world')
    assert coverage['total_records']==19573939
    assert len(coverage['documented_coverage'])==4
    standard=global_analysis('world','2026-06-01','2026-06-30')
    assert standard['loaded_observations']>1000000
    assert standard['global_processing_counts']['mnrt']==0
    assert standard['global_processing_counts']['vnrt']==0
    assert standard['summary']['combined']>0
    assert len(standard['points'])<=750
    assert standard['timeline'][0]['coverage']=='complete'
    provisional=global_analysis('world','2026-09-01','2026-09-30')
    assert provisional['loaded_observations']>2000000
    assert provisional['global_processing_counts']['msp']==0
    assert provisional['global_processing_counts']['vsp']==0
    assert provisional['timeline'][0]['coverage']=='provisional_nrt'


@pytest.mark.skipif(not WORLD_DB.is_file(),reason='World source data only included in complete edition')
def test_world_reveal_month_totals(monkeypatch):
    monkeypatch.delenv('BLINDSPOT_DB_PATH',raising=False)
    a=global_analysis('australia','2026-06-01','2026-06-30')
    b=global_investigation('australia','2026-06-01','2026-06-30')
    assert a['summary']['combined']==b['totals']['union']
    assert a['summary']['both']==b['totals']['both']
    assert a['summary']['modis_only']==b['totals']['modis_only']
    assert a['summary']['viirs_only']==b['totals']['viirs_only']
    assert b['calibration']['status']=='not_validated'
