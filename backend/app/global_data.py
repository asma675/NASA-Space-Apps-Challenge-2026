"""Indexed 2025–26 NASA worldwide cell-day observations for BLINDSPOT.

Raw global ZIP records are preserved in data/raw; this SQLite materialization
stores exact source-by-cell/day counts. The two standard-processing streams have
NASA type=0 filtering; NRT streams lack a type field and remain provisional.
Missing history, coverage, agency ground truth, and future fire predictions are
never silently inferred.
"""
from __future__ import annotations
import os,sqlite3
from calendar import monthrange
from collections import defaultdict
from datetime import date
from functools import lru_cache
from math import ceil
from pathlib import Path
from .analysis import month_range,MONTH_NAMES,CELL_METRES
from .storage import REGIONS
from .investigation import _monthly,_anomalies,_calibration,_complete_months
ROOT=Path(__file__).resolve().parents[2]
WORLD_DB=ROOT/'data'/'global_grid.sqlite3'
FIRST='2025-11-12';LAST='2026-11-13'


def ready():
    # Tests and deployments can point at an intentionally isolated custom DB.
    # Never graft the bundled global dataset into an unrelated BLINDSPOT_DB_PATH.
    override=os.getenv('BLINDSPOT_DB_PATH')
    if override and Path(override).resolve() != (ROOT/'data'/'blindspot.sqlite3').resolve():
        return False
    return WORLD_DB.is_file() and WORLD_DB.stat().st_size>100000


def open_world():
    c=sqlite3.connect(f'file:{WORLD_DB}?mode=ro',uri=True,timeout=60)
    c.row_factory=sqlite3.Row
    c.execute('PRAGMA cache_size=-32000')
    return c


def bbox_where(region,start,end,bbox=None):
    coords=list(bbox or REGIONS[region]['bbox']);w,s,e,n=coords
    where='day BETWEEN ? AND ? AND lon BETWEEN ? AND ? AND lat BETWEEN ? AND ?'
    args=[start,end,w,e,s,n]
    return where,args


def coverage_entries(region='world'):
    if not ready():return []
    with open_world() as conn:
        rows=[dict(r) for r in conn.execute('SELECT * FROM member_info ORDER BY min_day,product')]
    return [{'product':r['product'],'start_day':r['min_day'],'end_day':r['max_day'],
             'source_file':r['csv_filename'],'scope':'world','processing':r['processing'],
             'provisional':r['processing']=='nrt'} for r in rows]


def month_classification(region='world', bbox=None):
    # Province subsets of a World archive inherit observation-date coverage only;
    # documented geographical coverage is world (though actual orbital gaps unknown).
    docs=coverage_entries(region)
    complete=_complete_months(docs) if not bbox else set()
    nrt=set()
    for entry in docs:
        if not entry['provisional']:continue
        start=entry['start_day'];end=entry['end_day']
        for m in month_range(start,end):
            y,mm=map(int,m.split('-'))
            if start<=m+'-01' and end>=f'{m}-{monthrange(y,mm)[1]:02d}':nrt.add(m)
    return complete,nrt


def _month_query(conn,region,start,end,bbox=None):
    where,args=bbox_where(region,start,end,bbox)
    sql=f'''SELECT substr(day,1,7) mon,
        COUNT(*) AS union_days,
        SUM(CASE WHEN msp+mnrt>0 AND vsp+vnrt>0 THEN 1 ELSE 0 END) both,
        SUM(CASE WHEN msp+mnrt>0 AND vsp+vnrt=0 THEN 1 ELSE 0 END) modis_only,
        SUM(CASE WHEN msp+mnrt=0 AND vsp+vnrt>0 THEN 1 ELSE 0 END) viirs_only,
        SUM(CASE WHEN msp+mnrt>0 THEN 1 ELSE 0 END) modis,
        SUM(CASE WHEN vsp+vnrt>0 THEN 1 ELSE 0 END) viirs,
        SUM(msp+mnrt+vsp+vnrt) records,
        SUM(msp) msp,SUM(mnrt) mnrt,SUM(vsp) vsp,SUM(vnrt) vnrt
        FROM cells WHERE {where} GROUP BY mon ORDER BY mon'''
    return [dict(r) for r in conn.execute(sql,args)]


def _timeline(conn,region,start,end,bbox=None):
    raw={r['mon']:r for r in _month_query(conn,region,start,end,bbox)}
    result=[]
    for m in month_range(start,end):
        r=raw.get(m,{})
        result.append({'month':m,'combined':r.get('union_days',0),'both':r.get('both',0),
          'modis_only':r.get('modis_only',0),'viirs_only':r.get('viirs_only',0),
          'modis':r.get('modis',0),'viirs':r.get('viirs',0),'records':r.get('records',0),
          'msp':r.get('msp',0),'mnrt':r.get('mnrt',0),'vsp':r.get('vsp',0),'vnrt':r.get('vnrt',0)})
    return result


def _samples(conn,region,start,end,bbox,months):
    # Bounded stratified deterministic sample; NOT the analytical denominator.
    where,args=bbox_where(region,start,end,bbox)
    quota=max(5,ceil(335/max(1,len(months))))
    result=[]
    for m in months:
        sql=f'''SELECT day,lat,lon,msp,mnrt,vsp,vnrt FROM cells WHERE {where}
          AND substr(day,1,7)=? AND ABS(cx*347+cy*71+CAST(substr(day,9,2) AS INT)*129)%521=0
          LIMIT ?'''
        pts=conn.execute(sql,args+[m,quota]).fetchall()
        if len(pts)<min(6,quota):
            pts=conn.execute(f'''SELECT day,lat,lon,msp,mnrt,vsp,vnrt FROM cells WHERE {where}
                             AND substr(day,1,7)=? LIMIT ?''',args+[m,quota]).fetchall()
        for r in pts:
            mdet=r['msp']+r['mnrt']>0;vdet=r['vsp']+r['vnrt']>0
            category='matched' if mdet and vdet else 'modis_only' if mdet else 'viirs_only'
            for family in ('MODIS','VIIRS'):
                if family=='MODIS' and not mdet or family=='VIIRS' and not vdet:continue
                product=('MODIS_SP' if r['msp'] else 'MODIS_NRT') if family=='MODIS' else ('VIIRS_SNPP_SP' if r['vsp'] else 'VIIRS_SNPP_NRT')
                result.append({'latitude':r['lat'],'longitude':r['lon'],'date':r['day'],
                 'family':family,'product':product,
                 'category':category,'origin':'NASA FIRMS World #850371/#850372, approximate 10-km cell sample (not exact individual satellite point)',
                 'frp':None,'cell_records':r['msp']+r['mnrt']+r['vsp']+r['vnrt']})
    return result[:750]


def global_analysis(region,start,end,bbox=None):
    if not ready():raise ValueError('Global archive index is missing. Run scripts/build_world_grid.py.')
    meta=REGIONS[region].copy()
    if bbox:
        meta['bbox']=list(bbox);meta['name']='Custom focus · '+meta['name']
        meta['center']=[(bbox[1]+bbox[3])/2,(bbox[0]+bbox[2])/2]
    with open_world() as conn:
        timeline=_timeline(conn,region,start,end,bbox)
        nonempty=[x['month'] for x in timeline if x['combined']]
        points=_samples(conn,region,start,end,bbox,nonempty)
    total={k:sum(t[k] for t in timeline) for k in ('combined','both','modis_only','viirs_only','modis','viirs','records')}
    complete,nrt=month_classification(region,bbox)
    for t in timeline:
        t['coverage']='provisional_nrt' if t['month'] in nrt and t['month'] in complete else 'complete' if t['month'] in complete else 'unverified'
    seasonal=[]
    for idx,name in enumerate(MONTH_NAMES,1):
        sample=[t['combined'] for t in timeline if int(t['month'][5:])==idx and t['coverage'] in ('complete','provisional_nrt')]
        seasonal.append({'name':name,'month':idx,'average':round(sum(sample)/len(sample),2) if sample else 0,
         'total':sum(sample),'years_in_range':len(sample),'coverage':'complete' if sample else 'unverified'})
    peak=sorted((x for x in seasonal if x['years_in_range']),key=lambda x:x['average'],reverse=True)[:3]
    agreement=round(100*total['both']/total['combined'],1) if total['combined'] else 0
    note='World NASA FIRMS standard + provisional near-real-time observations (Nov 2025–Nov 2026). Not decades of global history; NRT has no type classification and data may be revised. Missing detection is not absence of burning.'
    return {'region':meta,'mode':'real','start':start,'end':end,
      'loaded_observations':total['records'],'summary':{**total,'sensor_agreement_pct':agreement,
        'peak_months':[x['name'] for x in peak],
        'headline':('Highest activity within these imported months: '+', '.join(x['name'] for x in peak)+'.' if peak else 'No fully covered months; seasonal ranking withheld.'),
        'explanation':f"{total['combined']:,} unique 10-km UTC grid-days have at least one eligible hotspot detection in the selected area. Both sensors have observations in {agreement}% of these grid-days. This is not detection accuracy."},
      'timeline':[{k:v for k,v in r.items() if k not in ('msp','mnrt','vsp','vnrt')} for r in timeline],
      'seasonal':seasonal,'points':points,'global_processing_counts':{x:sum(t[x] for t in timeline) for x in ('msp','mnrt','vsp','vnrt')},
      'data_origin':'NASA FIRMS World ZIPs #850371 MODIS and #850372 VIIRS; source rows compressed in data/raw; exact 10-km cell-day materialized counts in global_grid.sqlite3',
      'coverage_note':note,'truncated':False,'methodology':{
        'grid':'10-km projected Equal Earth EPSG:8857 grid cells × UTC day',
        'harmonization':'Joint spatial/temporal sensor presence, not a scientifically calibrated MODIS–VIIRS observation rate.',
        'metric':'Active 10-km grid-days with at least one presumed-vegetation (SP) or unclassified NRT hotspot.',
        'agreement':'Percentage of the union active grid-days with both MODIS and VIIRS presence; not detection accuracy.',
        'limitations':['Historical observation coverage limited to the supplied World ZIP windows and the separate 2023 Alberta ZIP.',
          'Near-real-time products have no source type field, are provisional and may change with standard processing.',
          'Standard archive fire_type 1/2/3 filtered; type=0 remains presumed vegetation, not verified incidents.',
          'Clouds, local overpass timing and satellite sensitivity are not corrected.',
          'No detection does not mean no fire; no global multi-year anomaly or validated fire ignition prediction.']}}


def global_inventory(region):
    if not ready():return None
    with open_world() as conn:
        where,args=bbox_where(region,FIRST,LAST)
        vals=conn.execute(f'''SELECT SUM(msp) msp,SUM(mnrt) mnrt,SUM(vsp) vsp,SUM(vnrt) vnrt,
           COUNT(*) cells,MIN(day) earliest,MAX(day) latest FROM cells WHERE {where}''',args).fetchone()
    d=dict(vals)
    records=[]
    for key,product,label in [('msp','MODIS_SP','standard'),('mnrt','MODIS_NRT','provisional'),
                              ('vsp','VIIRS_SNPP_SP','standard'),('vnrt','VIIRS_SNPP_NRT','provisional')]:
        val=d[key] or 0
        if val:records.append({'product':product,'count':val,'processing':label,
                              'earliest':d['earliest'],'latest':d['latest']})
    return {'records':records,'total_records':sum(r['count'] for r in records),
        'grid_day_cells':d['cells'] or 0,'documented_coverage':coverage_entries(region),
        'note':'NASA World request Nov 2025–Nov 2026, mixed standard and provisional NRT. Database stores exact grid-cell/day aggregates; original individual observations are preserved in NASA source ZIPs. Coverage is NOT a globally complete multi-decade archive.',
        'global_archive_complete':False}


@lru_cache(maxsize=12)
def _global_history_cached(path_mtime,region,bbox):
    with open_world() as conn:
        t=_timeline(conn,region,FIRST,LAST,bbox or None)
    complete,nrt=month_classification(region,bbox or None)
    m=[{'month':v['month'],'union':v['combined'],'modis':v['modis'],'viirs':v['viirs'],
        'both':v['both'],'modis_only':v['modis_only'],'viirs_only':v['viirs_only']} for v in t]
    return {'months':m,'complete':complete,'provisional':nrt,'coverage':coverage_entries(region)}


def global_history(region,bbox=None):
    stamp=WORLD_DB.stat().st_mtime_ns if ready() else 0
    return _global_history_cached(stamp,region,tuple(bbox) if bbox else ())


def global_investigation(region,start,end,month='',bbox=None):
    if not ready():raise ValueError('Global archive grid index is not installed')
    if month:
        y,m=map(int,month.split('-'))
        first=max(start,month+'-01');last=min(end,f'{month}-{monthrange(y,m)[1]:02d}')
    else:first,last=start,end
    with open_world() as conn:
        monthly=_timeline(conn,region,first,last,bbox)
        where,args=bbox_where(region,first,last,bbox)
        # Full-resolution totals from per-cell/day union; screen draws bounded sample.
        q=f'''SELECT cx,cy,AVG(lat) lat,AVG(lon) lon,
             SUM(CASE WHEN msp+mnrt>0 AND vsp+vnrt=0 THEN 1 ELSE 0 END) modis_only,
             SUM(CASE WHEN msp+mnrt=0 AND vsp+vnrt>0 THEN 1 ELSE 0 END) viirs_only,
             SUM(CASE WHEN msp+mnrt>0 AND vsp+vnrt>0 THEN 1 ELSE 0 END) both,
             SUM(CASE WHEN msp+mnrt>0 THEN 1 ELSE 0 END) modis,
             SUM(CASE WHEN vsp+vnrt>0 THEN 1 ELSE 0 END) viirs,
             COUNT(*) union_days FROM cells WHERE {where}
             GROUP BY cx,cy ORDER BY union_days DESC,cx,cy LIMIT 850'''
        cells=[{'lat':round(r['lat'],5),'lon':round(r['lon'],5),'modis_only':r['modis_only'],
            'viirs_only':r['viirs_only'],'both':r['both'],'modis':r['modis'],'viirs':r['viirs'],
            'union':r['union_days']} for r in conn.execute(q,args)]
    totals={key:sum(t[key if key!='union' else 'combined'] for t in monthly)
            for key in ('modis_only','viirs_only','both','modis','viirs','union')}
    history=global_history(region,bbox)
    included=sum(t['records'] for t in monthly)
    standard=sum(t['msp']+t['vsp'] for t in monthly)
    provisional=sum(t['mnrt']+t['vnrt'] for t in monthly)
    return {'region':('Custom focus inside '+REGIONS[region]['name']) if bbox else REGIONS[region]['name'],
        'mode':'real','start':first,'end':last,'focus_bbox':list(bbox) if bbox else None,'selected_month':month or None,
        'totals':totals,'overlap_pct':round(100*totals['both']/totals['union'],1) if totals['union'] else None,
        'cells':cells,'displayed_cells':len(cells),'total_cells':None,
        'monthly':[{k:v for k,v in t.items() if k in ('month','modis','viirs','both','modis_only','viirs_only','union')} for t in monthly for _ in [0] ],
        'quality':{'raw_records':None,'presumed_vegetation':standard,'excluded_other_types':None,
           'unclassified':provisional,'included_in_analysis':included,
           'rule':'NASA type 0 in standard products; near-real-time rows have no type and are included as provisional. Excluded source counts are available in data/global_archive_manifest.json for whole World downloads.'},
        'historical_months':history['months'],'complete_months':sorted(history['complete']),
        'historical_years':sorted({int(m[:4]) for m in history['complete']}),
        'anomalies':_anomalies(history['months'],history['complete']),
        'calibration':_calibration(history['months'],history['complete']),
        'methodology':{'unit':'10 km global Equal Earth EPSG:8857 cell × UTC day; MODIS/VIIRS presence per cell-day',
          'comparison':'Shared grid-days are not individual matched fires or sensor-accuracy estimates.',
          'sample':'Map shows top representative cells; every eligible grid-day contributes to the totals.',
          'classification':'Type=0 presumed vegetation in SP; unclassified provisional NRT retained and flagged.',
          'coverage':'2025–26 global ZIPs only, plus independent 2023 Alberta archive. At least 3 comparable covered years are needed for historical anomaly.',
          'availability':'No detections do not imply no fire. NRT may change after standard reprocessing.'}}


def combine_archives(old, world, start, end, old_complete=()):
    """Merge non-overlapping 2023 Alberta raw and 2025–26 World grid indexes.

    Never infer a complete worldwide year from the partial Alberta source window.
    The legacy source is queried only up to 2025-11-11, avoiding double counting
    if the user later loads other records into their legacy SQLite database.
    """
    keys=('combined','both','modis_only','viirs_only','modis','viirs','records')
    old_by={r['month']:r for r in old['timeline']}
    new_by={r['month']:r for r in world['timeline']}
    completed=set(old_complete)
    timeline=[]
    for m in month_range(start,end):
        a=old_by.get(m,{});b=new_by.get(m,{})
        result={'month':m,**{k:a.get(k,0)+b.get(k,0) for k in keys}}
        result['coverage']=b.get('coverage') if b.get('coverage') in ('complete','provisional_nrt') else 'complete' if m in completed else 'unverified'
        timeline.append(result)
    total={k:sum(t[k] for t in timeline) for k in keys}
    agreement=round(100*total['both']/total['combined'],1) if total['combined'] else 0
    seasonal=[]
    for i,name in enumerate(MONTH_NAMES,1):
        sample=[t['combined'] for t in timeline if int(t['month'][5:])==i and t['coverage'] in ('complete','provisional_nrt')]
        seasonal.append({'name':name,'month':i,'average':round(sum(sample)/len(sample),2) if sample else 0,
           'total':sum(sample),'years_in_range':len(sample),'coverage':'complete' if sample else 'unverified'})
    top=sorted((x for x in seasonal if x['years_in_range']),key=lambda x:x['average'],reverse=True)[:3]
    combined=world.copy()
    combined.update({'start':start,'end':end,'timeline':timeline,'seasonal':seasonal,
       'loaded_observations':old['loaded_observations']+world['loaded_observations'],
       'points':old['points'][:440]+world['points'][:690],
       'summary':{**total,'sensor_agreement_pct':agreement,'peak_months':[x['name'] for x in top],
          'headline':'Two distinct NASA archive periods are loaded; compare their spatial coverage before interpreting changes.',
          'explanation':f"The selected period contains {total['combined']:,} observed active grid-days. The 2023 Alberta archive is NOT full worldwide coverage, while 2025–26 files cover a World request; these periods must not be treated as directly comparable global trends."},
       'coverage_note':'MIXED GEOGRAPHIC SCOPE: 2023 observations come only from an Alberta archive; November 2025–November 2026 observations come from World downloads. Missing 2024 and early 2025 records are UNKNOWN, not zero. Do not infer global year-on-year changes or multi-year anomaly from these unequal windows.',
       'data_origin':old['data_origin']+' + '+world['data_origin'],
       'global_indexed':True})
    return combined
