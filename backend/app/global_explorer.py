"""World Atlas: NASA FIRMS near-real-time preview and locally held archive coverage.

A global map is not a globally complete historical time series. No inferred wildfire
ignitions or sensor false-negative claims. Credentials stay server-side.
"""
from __future__ import annotations
import csv, io, os, time
from datetime import datetime, timezone
from threading import RLock
import httpx
from .storage import REGIONS, connection
from .firms import NASA_BASE

LIVE_SOURCES=('VIIRS_SNPP_NRT','VIIRS_NOAA20_NRT','VIIRS_NOAA21_NRT','MODIS_NRT')
_CACHE={}
_LOCK=RLock()

def archive_inventory(region='world'):
    bbox=REGIONS[region]['bbox']; w,s,e,n=bbox
    with connection() as conn:
        records=[dict(x) for x in conn.execute("""SELECT product,COUNT(*) AS count,MIN(acq_date) AS earliest,
          MAX(acq_date) AS latest,MIN(latitude) AS southernmost,MAX(latitude) AS northernmost,
          MIN(longitude) AS westernmost,MAX(longitude) AS easternmost
          FROM observations WHERE mode='real' AND latitude BETWEEN ? AND ? AND longitude BETWEEN ? AND ?
          GROUP BY product""",(s,n,w,e))]
        try:
            coverage=[dict(x) for x in conn.execute("""SELECT product,start_day,end_day,source_file,scope
                 FROM archive_coverage WHERE scope=? ORDER BY start_day""",(region,))]
        except Exception:
            coverage=[]
    return {'region':region,'region_name':REGIONS[region]['name'], 'mode':'historical_offline',
            'records':records,'total_records':sum(q['count'] for q in records),
            'documented_coverage':coverage,
            'global_archive_complete':False,
            'note':('WORLD mode searches loaded records from every imported region. The bundled 2023 source archives cover ALBERTA only, NOT the globe. '
                    'A blank map elsewhere does not prove no fire. Global historical comparisons require NASA archives for each requested country/time and documented coverage.'
                    if region=='world' else
                    'This shows records currently imported for the selected area. Zero local records does not establish satellite coverage or absence of fires.'),
            'data_link':'https://firms.modaps.eosdis.nasa.gov/download/'}

def latest_hotspots(region='world',source='VIIRS_SNPP_NRT',days=1):
    if region not in REGIONS:raise ValueError('Unknown geographic region')
    if source not in LIVE_SOURCES:raise ValueError('Unsupported near-real-time source')
    if not isinstance(days,int) or days<1 or days>5:raise ValueError('Select 1 to 5 days')
    if region=='world' and days>1:raise ValueError('World queries are limited to 1 day to avoid excessive NASA request volume. Zoom into a region for up to 5 days.')
    key=os.getenv('FIRMS_MAP_KEY','').strip()
    if not key:
        return {'status':'not_configured','source':source,'region':region,'points':[],
                'note':'Set FIRMS_MAP_KEY in .env and restart the server. No live query was performed; this does not imply there are no fires.'}
    cache_key=(region,source,days)
    with _LOCK:
        hit=_CACHE.get(cache_key)
        if hit and time.monotonic()-hit[0]<600:return hit[1]
    area='world' if region=='world' else ','.join(map(str,REGIONS[region]['bbox']))
    url=f'{NASA_BASE}/{key}/{source}/{area}/{days}'
    accepted=0;excluded=0; seen=0;sample=[]
    # 50 MB guard; return a clear error rather than silently truncating global totals.
    try:
        with httpx.Client(timeout=40,follow_redirects=False) as client:
            with client.stream('GET',url) as response:
                if response.status_code!=200:raise ValueError(f'NASA returned HTTP {response.status_code}; source may be unavailable')
                body=[];size=0
                for chunk in response.iter_bytes():
                    size+=len(chunk)
                    if size>50_000_000:raise ValueError('World response exceeded 50 MB. Choose a smaller regional view or use NASA archive download')
                    body.append(chunk)
                raw=b''.join(body).decode('utf-8-sig')
    except (httpx.HTTPError,UnicodeError) as e:
        # Never expose an exception URL; it contains the NASA key.
        raise ValueError('NASA feed unavailable; check internet access, product availability, and MAP_KEY') from None
    if '<html' in raw[:200].lower():raise ValueError('NASA returned HTML rather than hotspot CSV')
    reader=csv.DictReader(io.StringIO(raw))
    cols={n.strip().lower() for n in (reader.fieldnames or []) if n}
    if not {'latitude','longitude','acq_date','acq_time'}.issubset(cols):
        raise ValueError('NASA did not return expected hotspot columns')
    # Uniform deterministic sample across input rows, not an early-rows subset.
    import random
    rng=random.Random(2026)
    for row in reader:
        seen+=1
        if row.get('type','0') not in ('0','',None):excluded+=1;continue
        try:
            lat=float(row['latitude']);lon=float(row['longitude'])
            if not (-90<=lat<=90 and -180<=lon<=180):continue
        except (KeyError,ValueError,TypeError):continue
        accepted+=1
        item={'lat':round(lat,5),'lon':round(lon,5),'date':row.get('acq_date',''),
              'acq_time':row.get('acq_time',''),'confidence':row.get('confidence',''),
              'frp':row.get('frp',''),'source':source}
        if len(sample)<450:sample.append(item)
        else:
            j=rng.randrange(accepted)
            if j<450:sample[j]=item
    result={'status':'ok','region':region,'source':source,'days':days,
            'queried_at_utc':datetime.now(timezone.utc).isoformat(timespec='seconds'),
            'total_source_rows':seen,'presumed_vegetation_rows':accepted,'excluded_other_types':excluded,
            'sampled_points':len(sample),'points':sample,
            'verified_fires':False,'prediction':False,
            'note':'Recent NASA thermal observations, not verified active wildfire incidents or ignition predictions. '
                   'Map points are a sample; only raw source rows are counted. Source/coverage may be incomplete or delayed.'}
    with _LOCK:_CACHE[cache_key]=(time.monotonic(),result)
    return result
