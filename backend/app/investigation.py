"""Independent BLINDSPOT investigation calculations (not derived from Zij).

Denominator: 10-km global Equal Earth EPSG:8857 cell by UTC day, once per sensor family.
A matched cell-day means co-occurrence, not simultaneous observation of one fire.
Type 0 is a *presumed* vegetation-fire thermal anomaly, not an incident label.
Historical anomalies need multiple independently covered years and are never
manufactured from one season.  Calibration is intentionally unavailable until
at least three joint sensor years have been imported and held-out tested.
"""
from __future__ import annotations
from collections import Counter, defaultdict
from datetime import date, timedelta
from functools import lru_cache
from calendar import monthrange
from math import sqrt
from pathlib import Path
from statistics import median

from .analysis import TRANSFORMER, GLOBAL_TRANSFORMER, CELL_METRES, cell_id
from .storage import REGIONS, connection, db_path


def _month_range(start: str, end: str):
    y, m = map(int,start[:7].split('-'))
    ey, em = map(int,end[:7].split('-'))
    while (y,m)<=(ey,em):
        yield f'{y}-{m:02d}'
        y,m = (y+1,1) if m==12 else (y,m+1)


def _rows(conn, region: str, start: str, end: str, mode='real', custom_bbox=None):
    w,s,e,n = custom_bbox if custom_bbox else REGIONS[region]['bbox']
    sql='''SELECT acq_date, latitude, longitude, family FROM observations
      WHERE mode=? AND acq_date BETWEEN ? AND ?
      AND longitude BETWEEN ? AND ? AND latitude BETWEEN ? AND ?
      AND (mode!='real' OR fire_type=0 OR fire_type IS NULL)'''
    return conn.execute(sql,(mode,start,end,w,e,s,n))


def _events(rows, global_grid=True):
    events={}
    # More efficient than retaining every raw detection; 2023 yields ~17k cell-days.
    for r in rows:
        flag = 1 if r['family']=='MODIS' else 2 if r['family']=='VIIRS' else 0
        if not flag: continue
        k=(r['acq_date'], *cell_id(r['latitude'],r['longitude'],global_grid))
        events[k]=events.get(k,0)|flag
    return events


def _monthly(events, first, last):
    out={m:{'month':m,'modis':0,'viirs':0,'both':0,'modis_only':0,'viirs_only':0,'union':0}
         for m in _month_range(first,last)}
    for (day,x,y),flag in events.items():
        q=out.get(day[:7])
        if q is None: continue
        q['union']+=1
        if flag & 1: q['modis']+=1
        if flag & 2: q['viirs']+=1
        if flag==3: q['both']+=1
        elif flag==1: q['modis_only']+=1
        else: q['viirs_only']+=1
    return list(out.values())


def _coverage(conn, region):
    try:
        scopes=['alberta_province'] if region=='alberta_boreal' else [region]
        placeholders=','.join('?' for _ in scopes)
        entries=[dict(x) for x in conn.execute(
            f'SELECT product,start_day,end_day,source_file,scope FROM archive_coverage WHERE scope IN ({placeholders})',scopes)]
    except Exception:
        entries=[]
    return entries


def _complete_months(coverage):
    complete={}
    for entry in coverage:
        for m in _month_range(entry['start_day'],entry['end_day']):
            year,mon=map(int,m.split('-'))
            start=f'{m}-01'
            end=f'{m}-{monthrange(year,mon)[1]:02d}'
            if entry['start_day']<=start and entry['end_day']>=end:
                complete.setdefault(m,set()).add(entry['product'])
    # A full comparison month must include the archive date window for both sensors.
    return {m for m,products in complete.items() if
            any(p.startswith('MODIS') for p in products) and
            any(p.startswith('VIIRS') for p in products)}


def _percentile(arr, fraction):
    if not arr:return None
    s=sorted(arr)
    pos=(len(s)-1)*fraction
    lo=int(pos); hi=min(len(s)-1,lo+1)
    return round(s[lo]+(s[hi]-s[lo])*(pos-lo),1)


def _anomalies(monthly, complete):
    out=[]
    for row in monthly:
        key=row['month']; year=int(key[:4]); mon=key[5:]
        peers=[other['union'] for other in monthly if other['month'].endswith('-'+mon)
               and int(other['month'][:4])!=year and other['month'] in complete]
        d={'month':key,'observed':row['union'],'supported':key in complete,
           'comparison_years':len(peers)}
        if key in complete and len(peers)>=3:
            baseline=median(peers)
            d.update({'status':'comparable','baseline_median':round(baseline,1),
                      'reference_p25':_percentile(peers,.25), 'reference_p75':_percentile(peers,.75),
                      'change_pct': round(100*(row['union']-baseline)/baseline,1) if baseline else None,
                      'note':'Descriptive anomaly relative to other imported fully covered years, not fire probability.'})
        else:
            d.update({'status':'insufficient_history', 'baseline_median':None,
                      'reference_p25':None,'reference_p75':None,'change_pct':None,
                      'note':'A real anomaly needs this month in at least 3 other fully covered imported years.'})
        out.append(d)
    return out


def _calibration(monthly, complete):
    paired=[r for r in monthly if r['month'] in complete and r['modis']>0 and r['viirs']>0]
    years=sorted(set(int(r['month'][:4]) for r in paired))
    basic={'status':'not_validated', 'years_available':years,
           'method':'Provisional MODIS→VIIRS active cell-day rate scaling, evaluated on unseen year; not a correction for clouds or orbital coverage.',
           'note':'At least 3 independent archive years with 3 common fully covered months are required. The 2023 archive alone cannot validate sensor calibration.'}
    if len(years)<3: return basic
    months_by_year={y:{r['month'][5:] for r in paired if int(r['month'][:4])==y} for y in years}
    common_months=set.intersection(*months_by_year.values())
    if len(common_months)<3:return basic
    paired=[r for r in paired if r['month'][5:] in common_months]
    holdout=years[-1]
    train=[r for r in paired if int(r['month'][:4])<holdout]
    test=[r for r in paired if int(r['month'][:4])==holdout]
    if not test or len(set(int(r['month'][:4]) for r in train))<2: return basic
    scale=sum(r['viirs'] for r in train)/max(1,sum(r['modis'] for r in train))
    total=sum(r['viirs'] for r in test)
    if not total:return basic
    raw=sum(abs(r['viirs']-r['modis']) for r in test)/total
    corrected=sum(abs(r['viirs']-scale*r['modis']) for r in test)/total
    return {'status':'experimental_holdout', 'years_available':years,'train_years':years[:-1],
      'heldout_year':holdout,'multiplier':round(scale,3),
      'heldout_wape_raw_pct':round(raw*100,1),
      'heldout_wape_scaled_pct':round(corrected*100,1),
      'method':'Sum(VIIRS active cell-days)/sum(MODIS active cell-days) fitted on earlier covered months; evaluated on unseen calendar year.',
      'note':'A simple held-out reference scaling, NOT validated harmonization or a physical-fire estimate. Results may be worse than raw data. Cloud/overpass/satellite gaps remain uncorrected.'}


@lru_cache(maxsize=12)
def _history_cached(db_name,stamp,region,mode,bbox_key):
    # Intentional separate history query: availability and baseline cannot be inferred
    # from the date window the visitor has selected.
    with connection() as conn:
        years=conn.execute('SELECT MIN(acq_date), MAX(acq_date) FROM observations WHERE mode=?',(mode,)).fetchone()
        if not years[0]:return {'months':[], 'complete':set(), 'coverage':[]}
        start=years[0]; end=years[1]
        events=_events(_rows(conn,region,start,end,mode, bbox_key or None),REGIONS[region].get('grid_projection')=='global')
        coverage=_coverage(conn,region) if mode=='real' and not bbox_key else []
    return {'months':_monthly(events,start,end),'complete':_complete_months(coverage),'coverage':coverage}


def _history(region,mode,custom_bbox=None):
    file=db_path()
    stat=file.stat().st_mtime_ns if file.exists() else 0
    return _history_cached(str(file),stat,region,mode,tuple(custom_bbox) if custom_bbox else ())


def _quality(conn,region,start,end,mode,custom_bbox=None):
    w,s,e,n=custom_bbox if custom_bbox else REGIONS[region]['bbox']
    rows=conn.execute('''SELECT product,fire_type,COUNT(*) AS cnt FROM observations
        WHERE mode=? AND acq_date BETWEEN ? AND ?
        AND longitude BETWEEN ? AND ? AND latitude BETWEEN ? AND ?
        GROUP BY product,fire_type''',(mode,start,end,w,e,s,n)).fetchall()
    raw=sum(r['cnt'] for r in rows)
    excluded=sum(r['cnt'] for r in rows if r['fire_type'] in (1,2,3))
    unknown=sum(r['cnt'] for r in rows if r['fire_type'] is None)
    return {'raw_records':raw,'presumed_vegetation':raw-excluded-unknown,
            'excluded_other_types':excluded,'unclassified':unknown,
            'included_in_analysis':raw-excluded,
            'rule':'NASA type 0 presumed vegetation; 1 volcano, 2 other static land source, 3 offshore. Unclassified imports retained but disclosed. Type 0 can still include false positives.'}


def investigate(region, start, end, mode='real', month='',custom_bbox=None):
    # Selected month is a server-side restriction; never derive totals from map sample.
    first=max(start, month+'-01') if month else start
    if month:
        y,m=map(int,month.split('-'))
        last=min(end, f'{month}-{monthrange(y,m)[1]:02d}')
    else:last=end
    if first>last:first=last
    with connection() as conn:
        event_flags=_events(_rows(conn,region,first,last,mode,custom_bbox),REGIONS[region].get('grid_projection')=='global')
        quality=_quality(conn,region,first,last,mode,custom_bbox)
    monthly=_monthly(event_flags,first,last)
    cell_stats=defaultdict(lambda:{'modis_only':0,'viirs_only':0,'both':0,'modis':0,'viirs':0,'union':0})
    for (day,cx,cy),flag in event_flags.items():
        q=cell_stats[(cx,cy)]
        q['union']+=1
        if flag & 1:q['modis']+=1
        if flag & 2:q['viirs']+=1
        if flag==1:q['modis_only']+=1
        elif flag==2:q['viirs_only']+=1
        else:q['both']+=1
    total={name:sum(q[name] for q in cell_stats.values()) for name in ['modis_only','viirs_only','both','modis','viirs','union']}
    sorted_cells=sorted(cell_stats.items(),key=lambda pair:(-pair[1]['union'],pair[0]))
    limit=850
    if len(sorted_cells)>limit:
        # Mix major cells and systematic coverage across lower activity cells.
        high=sorted_cells[:500]
        rest=sorted_cells[500:]
        stride=max(1,len(rest)//350)
        shown=(high+rest[::stride][:350])[:limit]
    else:shown=sorted_cells
    from pyproj import Transformer
    global_grid=REGIONS[region].get('grid_projection')=='global'
    to_wgs=Transformer.from_crs('EPSG:8857' if global_grid else 'EPSG:3978','EPSG:4326',always_xy=True)
    cells=[]
    for (cx,cy),q in shown:
        lon,lat=to_wgs.transform((cx+.5)*CELL_METRES,(cy+.5)*CELL_METRES)
        cells.append({'lat':round(lat,5),'lon':round(lon,5),**q})
    history=_history(region,mode,custom_bbox)
    complete=history['complete']
    anomalies=_anomalies(history['months'],complete)
    calibration=_calibration(history['months'],complete)
    return {'region':('Custom focus inside '+REGIONS[region]['name']) if custom_bbox else REGIONS[region]['name'],'mode':mode,'start':first,'end':last,'focus_bbox':list(custom_bbox) if custom_bbox else None,
        'selected_month':month or None,'totals':total,
        'overlap_pct':round(100*total['both']/total['union'],1) if total['union'] else None,
        'cells':cells,'displayed_cells':len(cells),'total_cells':len(cell_stats),
        'monthly':monthly,'quality':quality,
        'historical_months':history['months'],
        'complete_months':sorted(complete),
        'historical_years':sorted(set(int(x['month'][:4]) for x in history['months'] if x['month'] in complete)),
        'anomalies':anomalies,'calibration':calibration,
        'methodology':{'unit':('10 km global Equal Earth EPSG:8857' if global_grid else '10 km Canada EPSG:3978')+' cell × UTC day; MODIS/VIIRS presence per cell-day',
          'comparison':'Co-occurrence in a cell-day, not the same fire or an assessment of either sensor accuracy',
          'sample':'Map markers show representative grid cells; every eligible cell-day contributes to totals',
          'classification':'Type 0 presumed vegetation-fire detections; unknown types separately disclosed',
          'coverage':'A month counts as covered only when documented MODIS and VIIRS archive windows cover the full month AND selected geographic scope. Alberta archives do not establish worldwide coverage.',
          'availability':'No observations or no archive coverage do NOT imply no fire.'}}


def agency_match(region='alberta_province',year=2023,days=3,distance_km=20.0):
    """Conservative spatial+day coincidence for agency fire origins and NASA cell-days.

    These are different phenomena and a coincidence is not an independent truth label.
    """
    with connection() as conn:
        existing=conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='agency_fires'").fetchone()
        if not existing:
            return {'status':'not_imported','count':None,'note':'No Alberta government incident CSV has been imported.'}
        rows=[dict(r) for r in conn.execute('SELECT fire_id,latitude,longitude,discovered,fire_start,reported FROM agency_fires WHERE year=? ORDER BY fire_id LIMIT 10000',(year,))]
        if not rows:return {'status':'not_imported','count':None,'note':'No Alberta government incidents for this year; not evidence of zero fires.'}
        events=_events(_rows(conn,region,f'{year-1}-12-25',f'{year+1}-01-08','real'))
    byday=defaultdict(set)
    for (day,cx,cy),flag in events.items():byday[day].add((cx,cy))
    classified=[]; not_dated=0; matched=0; no_nearby=0
    for agency in rows:
        stamp=agency['discovered'] or agency['reported'] or agency['fire_start']
        try:when=date.fromisoformat(stamp[:10]) if stamp else None
        except (ValueError,TypeError):when=None
        if when is None: not_dated+=1;continue
        cx,cy=cell_id(agency['latitude'],agency['longitude'])
        neighbor=int(distance_km*1000/CELL_METRES)+2
        found=None
        for delta in range(-days,days+1):
            dt=(when+timedelta(days=delta)).isoformat()
            cells=byday.get(dt,set())
            for x in range(cx-neighbor,cx+neighbor+1):
                for y in range(cy-neighbor,cy+neighbor+1):
                    if (x,y) in cells and sqrt((x-cx)**2+(y-cy)**2)*10<=distance_km+7.1:
                        found={'agency_id':agency['fire_id'],'agency_discovered':stamp,
                               'satellite_grid_day':dt,'approx_km':round(sqrt((x-cx)**2+(y-cy)**2)*10,1),
                               'latitude':agency['latitude'],'longitude':agency['longitude']}
                        break
                if found:break
            if found:break
        if found:
            matched+=1
            if len(classified)<120:classified.append(found)
        else:no_nearby+=1
    return {'status':'loaded','year':year,'source':'Alberta agency fire-history CSV',
        'agency_incidents':len(rows),'with_dates':len(rows)-not_dated,
        'nearby_satellite_cell_days':matched,'no_nearby_match':no_nearby,'missing_dates':not_dated,
        'matches_sample':classified[:75],
        'matching_rule':f'Agency discovery date ±{days} calendar days; projected 10-km grid centers within approximately {distance_km} km.',
        'limitations':'Temporal/spatial coincidence is NOT proof that a satellite recorded the same agency incident. No nearby observation is NOT a false negative; satellite coverage is unknown. Includes fire origins rather than perimeters.'}
