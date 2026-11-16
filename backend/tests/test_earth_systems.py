"""Separate Earth Systems pages and honest external-data handling."""
from pathlib import Path
from unittest.mock import AsyncMock
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app import earth_systems as es

FRONT=Path(__file__).resolve().parents[2]/'frontend'

@pytest.fixture
def client():
    with TestClient(app) as c:yield c

def test_new_pages_and_old_pages_all_serve(client):
    for path,token in [('/','Enter the observatory'),('/observatory','story-next'),('/explore','reveal-left-map'),
                       ('/earth','A wildfire is never'),('/vegetation','layer-ndvi'),('/air-quality','air-summary'),
                       ('/navigation','calculate-route'),('/forecast','risk-summary'),('/cascades','concern-sector')]:
        response=client.get(path)
        assert response.status_code==200, path
        assert token in response.text, path

def test_navigation_between_all_new_pages(client):
    for path in ['/vegetation','/air-quality','/navigation','/forecast','/cascades']:
        text=client.get(path).text
        for dest in ['/earth','/vegetation','/air-quality','/navigation','/forecast','/cascades','/explore']:
            assert f'href="{dest}"' in text, (path,dest)

def test_attention_is_explainable_not_a_fire_probability():
    p=es.attention_index(33,24,44,0.2)
    assert p['score'] is not None and 0<=p['score']<=100
    assert p['status']=='illustrative_not_validated'
    assert abs(p['score']-round(sum(p['components'].values())))<=1
    assert es.attention_index(33,24,44,0.2,'hotter_drier')['score']>=p['score']
    assert es.attention_index(33,24,44,0.2,'windier')['score']>=p['score']
    assert es.attention_index(None,24,44,0.2)['score'] is None

def test_invalid_input_rejected():
    with pytest.raises(ValueError):es.check_coords(float('nan'),12)
    with pytest.raises(ValueError):es.check_coords(96,12)
    with pytest.raises(ValueError):es.attention_index(30,25,35,0,'wildfire_probability')

@pytest.mark.asyncio
async def test_forecast_uses_only_real_provider_values(monkeypatch):
    source={'daily':{'time':['2026-11-15','2026-11-16'],'temperature_2m_max':[25,None],
    'relative_humidity_2m_min':[30,25],'wind_speed_10m_max':[32,28],
    'wind_gusts_10m_max':[55,45],'precipitation_sum':[0,0.2]}}
    monkeypatch.setattr(es,'_request',AsyncMock(return_value=source))
    output=await es.weather_conditions(53.55,-113.5)
    assert len(output['days'])==2
    assert output['days'][0]['attention']['baseline']['score'] is not None
    assert output['days'][1]['attention']['baseline']['score'] is None
    assert 'not ignition probabilities' in output['scenario_disclaimer']

@pytest.mark.asyncio
async def test_air_and_grid_get_actual_unfabricated_values(monkeypatch):
    monkeypatch.setattr(es,'_request',AsyncMock(return_value={'current':{'time':'2026-11-15T06:00','us_aqi':42,'pm2_5':7.2,'pm10':13},
           'hourly':{'time':['2026-11-15T06:00'],'us_aqi':[42],'pm2_5':[7.2],'pm10':[13]}}))
    v=await es.air_conditions(53.55,-113.5)
    assert v['current']['us_aqi']==42 and v['days'][0]['pm25_max']==7.2
    records=[{'current':{'time':'2026-11-15T06:00','us_aqi':i,'pm2_5':None}} for i in range(9)]
    monkeypatch.setattr(es,'_request',AsyncMock(return_value=records))
    grid=await es.sampled_air_grid(53.55,-113.5)
    assert len(grid['samples'])==9
    assert grid['samples'][0]['aqi']==0
    assert grid['samples'][0]['pm25'] is None

def test_user_inputs_are_validated_at_api(client):
    response=client.get('/api/earth/weather?lat=99&lon=0')
    assert response.status_code==422
    response=client.get('/api/earth/air-grid?lat=40&lon=0&delta=100')
    assert response.status_code==422

def test_no_unfounded_prediction_claims_and_sources():
    desc=(FRONT.parent/'docs'/'EARTH_SYSTEMS_SOURCES_METHODS.md').read_text()
    js=(FRONT/'earth-systems.js').read_text()
    assert 'NOT a calibrated wildfire ignition forecast' in desc
    assert 'NASA GIBS' in desc and 'Copernicus' in desc
    assert 'router.project-osrm.org' in js
    assert 'api/earth/weather' in js
