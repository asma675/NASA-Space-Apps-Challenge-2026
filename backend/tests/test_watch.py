"""Tests focus on honest, auditable observation signals rather than fire predictions."""
from __future__ import annotations
from datetime import datetime, timezone
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app import watch

@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv('BLINDSPOT_DB_PATH', str(tmp_path/'test-watch.sqlite3'))
    monkeypatch.delenv('FIRMS_MAP_KEY', raising=False)
    monkeypatch.delenv('ADMIN_TOKEN', raising=False)
    watch._cached.clear()
    with TestClient(app) as c:
        yield c
    watch._cached.clear()


def test_live_endpoint_disconnected_does_not_claim_no_fires(client):
    r=client.get('/api/watch/live?region=alberta_province')
    assert r.status_code == 200
    assert r.json()['status'] == 'not_configured'
    assert r.json()['alerts'] == []
    assert 'NOT evidence of no current fires' in r.json()['note']
    assert client.get('/api/watch/live?region=not_a_region').status_code == 400


def test_live_satellite_groups_and_first_check(client, monkeypatch):
    monkeypatch.setenv('FIRMS_MAP_KEY', 'private-test-value')
    dt=datetime.now(timezone.utc)
    # Two independent VIIRS feeds can report activity in same projected 10-km grid-day.
    csv_data=(
        'latitude,longitude,acq_date,acq_time,type,confidence,frp\n'
        f'54.2,-115.0,{dt:%Y-%m-%d},{dt:%H%M},0,n,4.3\n'
        f'54.21,-115.02,{dt:%Y-%m-%d},{dt:%H%M},3,n,2.3\n' # Offshore/non-vegetation excluded
    )
    called=[]
    class FakeResponse:
        text=csv_data
        def raise_for_status(self): pass
    class FakeClient:
        def __init__(self,*a,**k): pass
        def __enter__(self): return self
        def __exit__(self,*a): return False
        def get(self,url):
            called.append(url)
            return FakeResponse()
    monkeypatch.setattr(watch.httpx,'Client',FakeClient)
    r=client.get('/api/watch/live?region=alberta_province')
    assert r.status_code==200,r.text
    data=r.json()
    assert data['status']=='ok'
    assert data['verified_wildfires'] is False
    assert len(data['source_products'])==2
    assert len(data['alerts'])==1
    assert data['alerts'][0]['n_observations']==2
    assert data['alerts'][0]['minutes_observation_to_first_check'] >= 0
    assert data['alerts'][0]['first_blindspot_check_utc']
    assert all('private-test-value' not in str(v) for v in data.values())
    r2=client.get('/api/watch/live?region=alberta_province')
    assert r2.json()['alerts'][0]['first_blindspot_check_utc'] == data['alerts'][0]['first_blindspot_check_utc']
    assert len(called)==2  # Cache avoids repeated NASA calls for 15 min.


def test_globe_and_watch_html_present(client):
    r=client.get('/explore')
    assert r.status_code==200
    assert 'id="hero-globe"' in r.text
    assert 'id="live-watch"' in r.text
    assert 'id="seasonal-watch"' in r.text
    assert 'globe.gl' in client.get('/assets/app.js').text
