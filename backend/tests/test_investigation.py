from __future__ import annotations
from fastapi.testclient import TestClient
import pytest
from app.main import app
from app.storage import connection,normalize_row,insert_rows
from app.investigation import _anomalies,_calibration

@pytest.fixture
def client(tmp_path,monkeypatch):
    monkeypatch.setenv('BLINDSPOT_DB_PATH',str(tmp_path/'investigation.sqlite3'))
    monkeypatch.delenv('ADMIN_TOKEN',raising=False)
    with TestClient(app) as c: yield c

def test_vegetation_quality_gate_and_count(client):
    rows=[]
    for product,typ,lat in [('MODIS_SP','0',54.1),('VIIRS_SNPP_SP','0',54.10003),
                            ('VIIRS_SNPP_SP','2',54.10006),('VIIRS_SNPP_SP','3',54.10008)]:
        rows.append(normalize_row({'latitude':lat,'longitude':-114,'acq_date':'2023-06-04',
            'acq_time':'1300','type':typ},product))
    assert insert_rows(rows)==4
    with connection() as db:
        for product in ('MODIS_SP','VIIRS_SNPP_SP'):
            db.execute('INSERT INTO archive_coverage(product,start_day,end_day,source_file) VALUES (?,?,?,?)',(product,'2023-06-01','2023-06-30','test.csv'))
    r=client.get('/api/investigation?region=alberta_province&start=2023-06-01&end=2023-06-30')
    assert r.status_code==200,r.text
    d=r.json()
    assert d['quality']['raw_records']==4
    assert d['quality']['excluded_other_types']==2
    assert d['quality']['presumed_vegetation']==2
    assert d['totals']['union']==1 and d['totals']['both']==1
    assert '2023-06' in d['complete_months']
    analysis=client.get('/api/analysis?region=alberta_province&start=2023-06-01&end=2023-06-30&mode=real').json()
    assert analysis['loaded_observations']==2
    assert analysis['timeline'][0]['coverage']=='complete'

def test_anomaly_needs_three_other_fully_covered_years():
    months=[{'month':f'{y}-07','union':v,'modis':v,'viirs':v*2} for y,v in [(2020,5),(2021,6),(2022,7),(2023,24)]]
    c=set(x['month'] for x in months)
    complete=_anomalies(months,c)
    row=complete[-1]
    assert row['status']=='comparable' and row['baseline_median']==6
    assert row['change_pct']==300
    not_complete=_anomalies(months,c-{'2021-07'})[-1]
    assert not_complete['status']=='insufficient_history'

def test_calibration_has_real_holdout_not_synthetic_score():
    three=[{'month':f'{y}-{m:02d}','modis':10,'viirs':20,'union':20} for y in (2021,2022,2023) for m in (5,6,7)]
    assert _calibration(three[:1],{r['month'] for r in three})['status']=='not_validated'
    d=_calibration(three,{r['month'] for r in three})
    assert d['status']=='experimental_holdout'
    assert d['multiplier']==2.0 and d['heldout_year']==2023
    assert d['heldout_wape_scaled_pct']==0

def test_agency_unloaded_and_month_input_validated(client):
    assert client.get('/api/investigation/agency-match?region=alberta_province&year=2023').json()['status']=='not_imported'
    assert client.get('/api/investigation?month=2023-04').status_code==400
    assert client.get('/api/investigation?month=2023-13').status_code==400
    assert client.get('/api/investigation/agency-match?days=999').status_code==400

def test_months_missing_coverage_are_not_falsely_zero(client):
    raw='latitude,longitude,acq_date,acq_time,type\n54.0,-115.0,2023-06-14,1255,0\n'
    assert client.post('/api/import/csv?product=MODIS_SP',content=raw).status_code==200
    j=client.get('/api/analysis?region=alberta_province&start=2023-05-01&end=2023-07-31&mode=real').json()
    assert [row['coverage'] for row in j['timeline']]==['unverified','unverified','unverified']


def test_custom_area_updates_analysis_and_export(client):
    for lat,lon,time in [(53.7,-114.2,'1201'),(58.8,-111.7,'1202')]:
        row=normalize_row({'latitude':lat,'longitude':lon,'acq_date':'2023-06-17','acq_time':time,'type':'0'},'MODIS_SP')
        assert insert_rows([row])==1
    base='/api/analysis?region=alberta_province&start=2023-06-01&end=2023-06-30&mode=real'
    province=client.get(base).json()
    focused=client.get(base+'&bbox=-115,53,-113,55').json()
    assert province['loaded_observations']==2
    assert focused['loaded_observations']==1
    assert focused['region']['bbox']==[-115.0,53.0,-113.0,55.0]
    inv=client.get('/api/investigation?region=alberta_province&start=2023-06-01&end=2023-06-30&mode=real&bbox=-115,53,-113,55').json()
    assert inv['totals']['union']==1
    csv=client.get('/api/export/monthly.csv?region=alberta_province&start=2023-06-01&end=2023-06-30&mode=real&bbox=-115,53,-113,55').text
    assert 'coverage' in csv
    assert client.get(base+'&bbox=-130,53,-113,55').status_code==400
