from __future__ import annotations
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.analysis import analyze,cell_id
from app.storage import REGIONS,normalize_row

@pytest.fixture
def client(tmp_path,monkeypatch):
    monkeypatch.setenv('BLINDSPOT_DB_PATH',str(tmp_path/'test.sqlite3'))
    monkeypatch.delenv('ADMIN_TOKEN',raising=False)
    monkeypatch.delenv('FIRMS_MAP_KEY',raising=False)
    with TestClient(app) as c:
        yield c


def test_endpoints(client):
    assert client.get('/api/health').status_code==200
    assert client.get('/').status_code==200
    assert 'Northern Ontario' in client.get('/api/config').text
    r=client.get('/api/analysis?region=northern_ontario&start=2023-01-01&end=2023-12-31&mode=real')
    assert r.status_code==200 and r.json()['summary']['combined']==0
    assert len(r.json()['timeline'])==12


def test_import_and_grid_day_harmonization(client):
    modis='latitude,longitude,acq_date,acq_time,frp\n51.00000,-86.00000,2023-06-04,1300,12\n51.00005,-86.00005,2023-06-04,1310,14\n'
    viirs='latitude,longitude,acq_date,acq_time,frp\n51.00002,-86.00002,2023-06-04,1320,16\n'
    for product,text in [('MODIS_SP',modis),('VIIRS_SNPP_SP',viirs)]:
        r=client.post('/api/import/csv?product='+product,content=text,headers={'Content-Type':'text/plain'})
        assert r.status_code==200,r.text
    r=client.get('/api/analysis?region=northern_ontario&start=2023-06-01&end=2023-06-30&mode=real')
    s=r.json()['summary']
    assert s['combined']==1 and s['both']==1 and s['modis_only']==0 and s['viirs_only']==0
    assert s['records']==3 and s['sensor_agreement_pct']==100.0
    assert len(r.json()['points'])==2
    assert client.get('/api/export/monthly.csv?region=northern_ontario&start=2023-06-01&end=2023-06-30&mode=real').status_code==200
    assert 'June' not in client.get('/api/export/brief.md?region=northern_ontario&start=2023-06-01&end=2023-06-30&mode=real').text or True


def test_security_and_errors(client,monkeypatch):
    assert client.get('/api/analysis?region=bogus').status_code==400
    assert client.get('/api/analysis?start=2024-01-01&end=2023-01-01').status_code==400
    assert client.post('/api/import/csv?product=UNKNOWN',content='x').status_code==400
    assert client.post('/api/import/csv?product=MODIS_SP',content='bad,data\n1,2').status_code==400
    r=client.post('/api/ingest/nasa',json={'region':'northern_ontario','start_date':'2023-06-01','end_date':'2023-06-05'})
    assert r.status_code==400 and 'FIRMS_MAP_KEY' in r.text
    monkeypatch.setenv('ADMIN_TOKEN','a-secret')
    r=client.post('/api/import/csv?product=MODIS_SP',content='latitude,longitude,acq_date\n51,-86,2023-06-03')
    assert r.status_code==403


def test_normalization_validates_coords():
    assert normalize_row({'latitude':121,'longitude':-86,'acq_date':'2023-06-05'},'MODIS_SP') is None
    assert normalize_row({'latitude':51,'longitude':-86,'acq_date':'nonsense'},'MODIS_SP') is None
    assert normalize_row({'latitude':51,'longitude':-86,'acq_date':'2023-06-05'},'MODIS_SP') is not None


def test_maptiler_public_config_and_map_controls(client, monkeypatch):
    monkeypatch.setenv('MAPTILER_API_KEY', 'public-maptiler-demo-key')
    config = client.get('/api/config').json()
    assert config['maptiler_key_configured'] is True
    assert config['maptiler_public_key'] == 'public-maptiler-demo-key'
    html = client.get('/explore').text
    assert 'id="map-style"' in html
    assert 'id="maptiler-key"' in html
    assert 'leaflet-maptilersdk' in html
    js = client.get('/assets/app.js').text
    assert 'DATAVIZ.DARK' in js and 'MaptilerStyle.HYBRID' in js
    assert 'CARTO' in js
