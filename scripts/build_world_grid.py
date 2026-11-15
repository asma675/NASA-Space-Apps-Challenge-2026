"""Build an *exact sensor-presence/10-km UTC-day* global index from NASA FIRMS world ZIPs.

This does not store every raw detection separately in SQLite. All 20m+ original
records stay in the bundled NASA ZIPs. The indexed materialization retains the
exact active cell-day union, per-source detection counts, and point samples.

Command (Windows from project root):
  py scripts/build_world_grid.py --modis "data/raw/DL_FIRE_M-C61_850371.zip" --viirs "data/raw/DL_FIRE_SV-C2_850372.zip"

The standard and NRT CSV members are ingested separately. Excludes NASA type 1/2/3
from principal analysis; NRT lacks type and is included but marked unclassified.
Inserts are idempotent at (ZIP basename + member filename + day). Never treat
NRT as confirmed operational incidents or comprehensive coverage.
"""
from __future__ import annotations
import argparse,csv,io,json,sqlite3,sys,time,zipfile
from collections import defaultdict
from datetime import date
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'backend'))
from app.analysis import GLOBAL_TRANSFORMER,CELL_METRES

CREATE="""
CREATE TABLE IF NOT EXISTS cells (
  day TEXT NOT NULL, cx INTEGER NOT NULL, cy INTEGER NOT NULL,
  lat REAL NOT NULL, lon REAL NOT NULL,
  msp INTEGER NOT NULL DEFAULT 0, mnrt INTEGER NOT NULL DEFAULT 0,
  vsp INTEGER NOT NULL DEFAULT 0, vnrt INTEGER NOT NULL DEFAULT 0,
  PRIMARY KEY (day,cx,cy)
) WITHOUT ROWID;
CREATE TABLE IF NOT EXISTS import_days (
  member_id TEXT NOT NULL, day TEXT NOT NULL, raw_rows INTEGER NOT NULL,
  eligible INTEGER NOT NULL, excluded INTEGER NOT NULL,
  PRIMARY KEY (member_id,day)
);
CREATE TABLE IF NOT EXISTS member_info (
  member_id TEXT PRIMARY KEY, zip_filename TEXT NOT NULL, csv_filename TEXT NOT NULL,
  product TEXT NOT NULL, processing TEXT NOT NULL,
  min_day TEXT NOT NULL, max_day TEXT NOT NULL,
  scope TEXT NOT NULL DEFAULT 'world', note TEXT NOT NULL
);
"""
UPSERT="""INSERT INTO cells (day,cx,cy,lat,lon,msp,mnrt,vsp,vnrt)
  VALUES(?,?,?,?,?,?,?,?,?)
  ON CONFLICT(day,cx,cy) DO UPDATE SET
   msp=msp+excluded.msp, mnrt=mnrt+excluded.mnrt,
   vsp=vsp+excluded.vsp, vnrt=vnrt+excluded.vnrt"""


def index_zip(path:Path, family:str, conn:sqlite3.Connection):
  started=time.monotonic()
  if not path.is_file():raise FileNotFoundError(str(path))
  summaries=[]
  with zipfile.ZipFile(path) as archive:
    members=[m for m in archive.infolist() if m.filename.lower().endswith('.csv')]
    if not members:raise ValueError(f'{path}: no NASA CSV found')
    for member in members:
      n=member.filename.lower()
      processing='nrt' if 'nrt' in n else 'sp' if 'archive' in n else None
      if not processing: raise ValueError(f'Unknown NASA source member: {member.filename}')
      product=('VIIRS_SNPP' if family=='VIIRS' else 'MODIS')+'_'+processing.upper()
      col={'MODIS':('mnrt' if processing=='nrt' else 'msp'),
           'VIIRS':('vnrt' if processing=='nrt' else 'vsp')}[family]
      index={'msp':0,'mnrt':1,'vsp':2,'vnrt':3}[col]
      member_id=path.name+'::'+member.filename
      print('IMPORT',member_id,'as',col,flush=True)
      total_raw=total_eligible=total_excluded=0
      current_day=None
      raw_rows=[]
      first=last=None
      processed_days=0
      def flush(day,source_rows):
        nonlocal total_raw,total_eligible,total_excluded,processed_days
        if not source_rows:return
        # One day's ~100k detections -> one vector projection then reduction.
        lons=[t[1] for t in source_rows if t[2]]
        lats=[t[0] for t in source_rows if t[2]]
        raw_count=len(source_rows)
        included=len(lons)
        excluded=raw_count-included
        if conn.execute('SELECT 1 FROM import_days WHERE member_id=? AND day=?',(member_id,day)).fetchone():
          print('  skipped already indexed',day,flush=True);return
        aggregated={}
        if included:
          xx,yy=GLOBAL_TRANSFORMER.transform(lons,lats)
          for lon,lat,x,y in zip(lons,lats,xx,yy):
            cx=int(x//CELL_METRES);cy=int(y//CELL_METRES)
            key=(cx,cy)
            if key in aggregated:aggregated[key][2]+=1
            else:aggregated[key]=[lat,lon,1]
        batch=[]
        for (cx,cy),(lat,lon,count) in aggregated.items():
          source_counts=[0,0,0,0];source_counts[index]=count
          batch.append((day,cx,cy,lat,lon,*source_counts))
        # Commit day and its audit record in one transaction; safe to re-run.
        with conn:
          conn.executemany(UPSERT,batch)
          conn.execute('INSERT INTO import_days(member_id,day,raw_rows,eligible,excluded) VALUES(?,?,?,?,?)',
                       (member_id,day,raw_count,included,excluded))
        total_raw+=raw_count;total_eligible+=included;total_excluded+=excluded
        processed_days+=1
        if processed_days%25==0:
          print(f'  {day}: {total_raw:,} rows; {total_eligible:,} eligible; {total_excluded:,} excluded; {len(aggregated):,} distinct cells today; elapsed {time.monotonic()-started:.0f}s',flush=True)
      with archive.open(member) as raw,io.TextIOWrapper(raw,encoding='utf-8-sig',newline='') as source:
        reader=csv.reader(source)
        header=[s.strip().lower() for s in next(reader)]
        required=('latitude','longitude','acq_date','acq_time')
        if any(h not in header for h in required):raise ValueError(f'{member.filename}: missing FIRMS fields')
        h={label:header.index(label) for label in required}
        type_i=header.index('type') if 'type' in header else -1
        if processing=='sp' and type_i<0:raise ValueError(f'Standard archive has no type field: {member.filename}')
        for row in reader:
          if len(row)<len(header):continue
          day=row[h['acq_date']].strip()
          try:
            date.fromisoformat(day)
            lat=float(row[h['latitude']]);lon=float(row[h['longitude']])
            if not (-90<=lat<=90 and -180<=lon<=180):continue
          except (ValueError,IndexError):continue
          if current_day is None:current_day=day;first=day
          if day!=current_day:
            if day<current_day:raise ValueError(f'{member.filename}: records not sorted by day; importer requires day order')
            flush(current_day,raw_rows)
            raw_rows=[];current_day=day
          keep=(type_i<0 or row[type_i].strip()=='0')
          raw_rows.append((lat,lon,keep))
          last=day
        if current_day:flush(current_day,raw_rows)
      if first:
        with conn:
          conn.execute('INSERT OR REPLACE INTO member_info(member_id,zip_filename,csv_filename,product,processing,min_day,max_day,scope,note) VALUES(?,?,?,?,?,?,?,?,?)',
          (member_id,path.name,member.filename,product,processing,first,last,'world',
           'NRT data have no NASA fire-type column; provisional/unclassified' if processing=='nrt' else 'NASA type 0 presumed vegetation; other types excluded'))
      summaries.append({'member':member.filename,'product':product,'start':first,'end':last,
        'processed_now':total_raw,'accepted_now':total_eligible,'excluded_now':total_excluded,
        'elapsed_s':round(time.monotonic()-started)})
      print('DONE',summaries[-1],flush=True)
  return summaries


def main():
  p=argparse.ArgumentParser(description='Build global grid-day indexes from NASA FIRMS world ZIPs.')
  p.add_argument('--modis',type=Path,required=True)
  p.add_argument('--viirs',type=Path,required=True)
  p.add_argument('--out',type=Path,default=ROOT/'data'/'global_grid.sqlite3')
  args=p.parse_args();args.out.parent.mkdir(parents=True,exist_ok=True)
  started=time.monotonic()
  conn=sqlite3.connect(args.out,timeout=240)
  conn.execute('PRAGMA journal_mode=WAL')
  conn.execute('PRAGMA synchronous=NORMAL')
  conn.execute('PRAGMA cache_size=-40000')
  conn.executescript(CREATE)
  out=[]
  for path,family in ((args.modis,'MODIS'),(args.viirs,'VIIRS')):
    out+=index_zip(path,family,conn)
  conn.execute('PRAGMA wal_checkpoint(TRUNCATE)')
  conn.execute('PRAGMA journal_mode=DELETE')
  row=conn.execute('SELECT COUNT(*) FROM cells').fetchone()[0]
  aggregates=conn.execute('SELECT SUM(msp),SUM(mnrt),SUM(vsp),SUM(vnrt) FROM cells').fetchone()
  raw=conn.execute('SELECT SUM(raw_rows),SUM(eligible),SUM(excluded) FROM import_days').fetchone()
  print('SUMMARY distinct grid-day cells:',row,'source counts:',aggregates,'raw/eligible/excluded:',raw,'elapsed',round(time.monotonic()-started),flush=True)
  print('INTEGRITY',conn.execute('PRAGMA quick_check').fetchone()[0],flush=True)
  conn.close()
  manifest={'source':'NASA FIRMS user-provided World downloads (request IDs 850371 MODIS C6.1 and 850372 VIIRS S-NPP C2)',
    'source_members':out,'raw_counts':{'total':raw[0],'eligible':raw[1],'excluded':raw[2]},
    'eligible_by_processing':{'MODIS_SP':aggregates[0],'MODIS_NRT':aggregates[1],
                              'VIIRS_SNPP_SP':aggregates[2],'VIIRS_SNPP_NRT':aggregates[3]},
    'distinct_global_equal_earth_10km_utc_cell_days':row,
    'scope':'World request (do not infer complete satellite coverage over oceans/clouds)',
    'data_preservation':'Every original source row remains in data/raw ZIPs; the SQLite grid-day index stores exact grid/day/source counts but not every original coordinate.',
    'limitations':'Type=0 standard assumed vegetation, not confirmed fires. NRT has no type field. Aggregated cell-day counts are not wildfire incidence or calibrated sensor sensitivity.'}
  (args.out.parent/'global_archive_manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
  print(json.dumps(manifest,indent=2),flush=True)

if __name__=='__main__':main()
