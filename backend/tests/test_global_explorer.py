from __future__ import annotations
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.storage import normalize_row,insert_rows,connection
from app import global_explorer

@pytest.fixture
def client(tmp_path,monkeypatch):
    monkeypatch.setenv('BLINDSPOT_DB_PATH',str(tmp_path/'global.sqlite3'))
    monkeypatch.delenv('FIRMS_MAP_KEY',raising=False)
    global_explorer._CACHE.clear()
    with TestClient(app) as c:yield c


def test_world_region_and_isolated_coverage(client):
    d=client.get('/api/config').json()
    assert 'world' in d['regions'] and 'australia' in d['regions']
    for product in ('MODIS_SP','VIIRS_SNPP_SP'):
        row=normalize_row({'latitude':'54.0','longitude':'-115.0','acq_date':'2023-06-14',
                           'acq_time':'1315','type':'0'},product)
        insert_rows([row])
    with connection() as conn:
        for product in ('MODIS_SP','VIIRS_SNPP_SP'):
            conn.execute('INSERT INTO archive_coverage(product,start_day,end_day,source_file) VALUES (?,?,?,?)',
                         (product,'2023-06-01','2023-06-30','alberta-2023.zip'))
    alberta=client.get('/api/analysis?region=alberta_province&start=2023-06-01&end=2023-06-30&mode=real').json()
    assert alberta['loaded_observations']==2
    assert alberta['timeline'][0]['coverage']=='complete'
    world=client.get('/api/analysis?region=world&start=2023-06-01&end=2023-06-30&mode=real').json()
    assert world['loaded_observations']==2
    assert world['timeline'][0]['coverage']=='unverified'
    assert 'not a global archive' in world['coverage_note'].lower()
    assert 'Equal Earth' in world['methodology']['grid']
    inv=client.get('/api/investigation?region=world&start=2023-06-01&end=2023-06-30&mode=real').json()
    assert inv['totals']['both']==1
    assert not inv['complete_months']
    inventory=client.get('/api/global/coverage?region=world').json()
    assert inventory['total_records']==2
    assert inventory['global_archive_complete'] is False
    assert inventory['documented_coverage']==[]
    assert client.get('/api/global/coverage?region=australia').json()['total_records']==0


def test_world_nasa_no_key_and_reject_bad_source(client):
    d=client.get('/api/global/latest?region=world&source=VIIRS_SNPP_NRT&days=1').json()
    assert d['status']=='not_configured'
    assert d['points']==[]
    assert client.get('/api/global/latest?region=world&source=VIIRS_SNPP_SP').status_code==400
    assert client.get('/api/global/latest?region=world&source=VIIRS_SNPP_NRT&days=2').status_code==400


def test_global_recent_source_parsing_is_separate_from_historical_database(client,monkeypatch):
    monkeypatch.setenv('FIRMS_MAP_KEY','SOME_PRIVATE_KEY')
    payload='latitude,longitude,acq_date,acq_time,type,frp,confidence\n-20.1,134.3,2026-11-14,1210,0,4.4,n\n-20.2,134.4,2026-11-14,1212,2,3.1,l\n'
    called=[]
    class Response:
        status_code=200
        def __enter__(self):return self
        def __exit__(self,*args):pass
        def iter_bytes(self):yield payload.encode()
    class Client:
        def __init__(self,**kwargs):pass
        def __enter__(self):return self
        def __exit__(self,*args):pass
        def stream(self,method,url):
            called.append((method,url))
            return Response()
    monkeypatch.setattr(global_explorer.httpx,'Client',Client)
    d=client.get('/api/global/latest?region=world&source=VIIRS_SNPP_NRT&days=1').json()
    assert d['status']=='ok'
    assert d['presumed_vegetation_rows']==1
    assert d['excluded_other_types']==1
    assert len(d['points'])==1 and d['points'][0]['lat']==-20.1
    assert '/VIIRS_SNPP_NRT/world/1' in called[0][1]
    assert client.get('/api/global/coverage?region=world').json()['total_records']==0
    assert d['verified_fires'] is False and d['prediction'] is False
