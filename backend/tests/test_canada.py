"""Official Canadian agency integration must remain independent of NASA synthetic / real modes."""
import io
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.canada import import_agency_csv, agency_context, parse_date

@pytest.fixture
def client(tmp_path,monkeypatch):
    monkeypatch.setenv('BLINDSPOT_DB_PATH',str(tmp_path/'test.sqlite3'))
    monkeypatch.delenv('ADMIN_TOKEN',raising=False)
    with TestClient(app) as c:yield c

CSV='''year,fire_number,latitude,longitude,current_size,general_cause,fire_start_date,discovered_date,reported_date
2023,EWF001,54.123,-115.555,21.5,Lightning,2023-05-04 11:00:00,2023-05-04 11:25:00,2023-05-04 12:25:00
2023,EWF002,53.456,-113.899,0.3,Recreation,2023-06-01 11:00:00,,2023-06-01 15:00:00
2024,EWF003,55.234,-114.222,10,Lightning,2024-07-01,,, 
2023,BAD,200,0,1,Other,2023-07-01,,,
'''

def test_agency_import_and_no_fake_missing_data(client):
    r=client.get('/api/context/alberta?year=2023')
    assert r.status_code==200 and r.json()['status']=='not_imported' and r.json()['count'] is None
    r=client.post('/api/context/alberta/import-csv',content=CSV,headers={'Content-Type':'text/csv'})
    assert r.status_code==200,r.text
    assert r.json()['parsed']==3 and r.json()['invalid_or_skipped']==1
    r=client.get('/api/context/alberta?year=2023')
    data=r.json()
    assert data['status']=='loaded' and data['count']==2
    assert data['discovery_to_report']['sample_size']==1 and data['discovery_to_report']['median_minutes']==60.0
    assert any(x['month']=='2023-05' and x['count']==1 for x in data['monthly'])
    assert data['points'][0]['fire_id']=='EWF001'
    # Idempotent upsert preserves unique agency incident IDs and never populates NASA real observations
    assert client.post('/api/context/alberta/import-csv',content=CSV).status_code==200
    assert client.get('/api/context/alberta?year=2023').json()['count']==2
    assert not any(x['mode']=='real' for x in client.get('/api/config').json()['counts'])

def test_csv_validation_and_admin_protection(client,monkeypatch):
    assert client.post('/api/context/alberta/import-csv',content='bad,columns\n1,2').status_code==400
    assert client.get('/api/context/alberta?year=1800').status_code==400
    monkeypatch.setenv('ADMIN_TOKEN','private')
    assert client.post('/api/context/alberta/import-csv',content=CSV).status_code==403
    assert client.post('/api/context/alberta/import-csv',content=CSV,headers={'X-Admin-Token':'private'}).status_code==200

def test_date_timezone_is_not_assumed():
    assert parse_date('') is None
    assert parse_date('2023-05-04 12:30:00')=='2023-05-04 12:30:00'
    assert parse_date('bad') is None
