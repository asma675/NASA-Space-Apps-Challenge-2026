"""Parallax BLINDSPOT — FastAPI backend and embedded production-build-less frontend."""
from __future__ import annotations
import csv
import io
import os
from contextlib import asynccontextmanager
from datetime import date
from functools import lru_cache
from pathlib import Path
from fastapi import FastAPI, HTTPException, Header, Query, Request
from fastapi.responses import FileResponse, JSONResponse, PlainTextResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from .storage import REGIONS, SOURCES, counts, init_db, get_rows, insert_rows, db_path
from .analysis import analyze
from .firms import parse_csv, fetch_nasa
from .watch import live_watch
from .canada import agency_context, import_agency_csv
from .investigation import investigate, agency_match, _history
from .global_explorer import archive_inventory, latest_hotspots, LIVE_SOURCES

ROOT=Path(__file__).resolve().parents[2]
FRONTEND=ROOT/"frontend"

@asynccontextmanager
async def lifespan(app: FastAPI):
    if os.getenv("APP_ENV", "development")=="production" and not os.getenv("ADMIN_TOKEN"):
        raise RuntimeError("ADMIN_TOKEN must be configured in production")
    init_db()
    yield

app=FastAPI(title="Parallax BLINDSPOT API", version="0.9.0", lifespan=lifespan,
            description="Historical satellite observation alignment and seasonality prototype; not operational emergency guidance.")

class ImportNASA(BaseModel):
    region: str
    start_date: date
    end_date: date
    products: list[str] = Field(default_factory=lambda: ["MODIS_SP","VIIRS_SNPP_SP"])


def admin_required(token: str | None):
    configured=os.getenv("ADMIN_TOKEN","").strip()
    if configured and token != configured:
        raise HTTPException(status_code=403,detail="Admin token required to import data")


def validate_params(region, start, end, mode):
    if region not in REGIONS: raise HTTPException(400,"Unknown region")
    if mode not in ["demo","real"]: raise HTTPException(400,"Mode must be demo or real")
    try:
        s=date.fromisoformat(start); e=date.fromisoformat(end)
    except ValueError: raise HTTPException(400,"Use ISO dates YYYY-MM-DD")
    if s>e or (e-s).days>366*30:
        raise HTTPException(400,"Invalid date interval")
    return s,e

@app.get("/api/health")
def health():
    return {"status":"ok","service":"BLINDSPOT API"}

@app.get("/api/config")
def config():
    return {"regions":REGIONS,"firms_key_configured":bool(os.getenv("FIRMS_MAP_KEY")),
            "admin_token_required":bool(os.getenv("ADMIN_TOKEN")),"maptiler_key_configured":bool(os.getenv("MAPTILER_API_KEY")),
            "maptiler_public_key":os.getenv("MAPTILER_API_KEY", ""),"counts":counts(),
            "method":"Projected cell-day presence. Not calibrated for orbital/observational differences."}

def parse_focus_bbox(value: str, region: str):
    if not value:return None
    try:
        bbox=tuple(float(x) for x in value.split(','))
    except ValueError:
        raise HTTPException(400,'Custom area requires west,south,east,north coordinates')
    if len(bbox)!=4:raise HTTPException(400,'Custom area requires four coordinates')
    from math import isfinite
    w,s,e,n=bbox
    rw,rs,re,rn=REGIONS[region]['bbox']
    if not all(isfinite(v) for v in bbox) or not (rw<=w<e<=re and rs<=s<n<=rn) or e-w<.08 or n-s<.08:
        raise HTTPException(400,'Custom bounding box must be a valid area inside the chosen region (at least 0.08° wide and tall)')
    return tuple(round(x,5) for x in bbox)


@lru_cache(maxsize=12)
def cached_analysis(db_path_string: str, db_mtime_ns: int, region: str, start: str, end: str, mode: str, focus_bbox):
    # Cache immutable aggregate results, not raw 500k+ row arrays.
    meta=REGIONS[region].copy()
    if focus_bbox:
        meta['bbox']=list(focus_bbox)
        meta['name']='Custom focus · '+meta['name']
        meta['center']=[(focus_bbox[1]+focus_bbox[3])/2,(focus_bbox[0]+focus_bbox[2])/2]
    return analyze(get_rows(mode,region,start,end,custom_bbox=focus_bbox),meta,start,end,mode)


def compute_analysis(region: str, start: str, end: str, mode: str, focus_bbox=None):
    path=db_path()
    timestamp=path.stat().st_mtime_ns if path.exists() else 0
    return cached_analysis(str(path),timestamp,region,start,end,mode,tuple(focus_bbox) if focus_bbox else ()).copy()


@app.get("/api/analysis")
def analysis(region: str="northern_ontario", start: str="2021-01-01", end: str="2024-12-31", mode: str="demo",bbox: str=""):
    validate_params(region,start,end,mode)
    focus=parse_focus_bbox(bbox,region)
    result=compute_analysis(region,start,end,mode,focus)
    if mode=='real':
        covered=_history(region,'real',focus)['complete']
        for item in result['timeline']:
            item['coverage']='complete' if item['month'] in covered else 'unverified'
        # Do not average missing months as observed zeros in Fire DNA.
        names=['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']
        seasonal=[]
        for month_no,name in enumerate(names,1):
            sample=[t['combined'] for t in result['timeline'] if int(t['month'][5:])==month_no and t['coverage']=='complete']
            seasonal.append({'name':name,'month':month_no,'average':round(sum(sample)/len(sample),2) if sample else 0,
                             'total':sum(sample),'years_in_range':len(sample),'coverage':'complete' if sample else 'unverified'})
        result['seasonal']=seasonal
        peak=sorted((x for x in seasonal if x['years_in_range']),key=lambda x:x['average'],reverse=True)[:3]
        result['summary']['peak_months']=[x['name'] for x in peak]
        result['summary']['headline']=(f"{', '.join(x['name'] for x in peak)} had the highest observed grid-day activity among archive-covered months in this selection." if peak else "No fully covered months are available for this selection; no seasonal ranking can be made.")
    else:
        for item in result['timeline']:item['coverage']='synthetic_demo'
    result["data_origin"]="ILLUSTRATIVE SYNTHETIC DATA — NOT NASA" if mode=="demo" else "NASA FIRMS API or user-imported FIRMS-format CSV; verify provenance"
    if mode=='real':
        result['coverage_note']=(
            'WORLD VIEW IS NOT A GLOBAL ARCHIVE: only Alberta 2023 is preloaded. Other regions need imported NASA archives; the global map shows only the records actually stored. Dates outside a documented source-area window must not be interpreted as zero fires.'
            if region=='world' else
            'Only Alberta May–October 2023 is preloaded. This region may have no historical archive until its source data are imported.'
            if REGIONS[region].get('grid_projection')=='global' else
            'Alberta May–October 2023 is preloaded; regional coverage requires source archive verification.')
    result["truncated"]=False  # Streaming full-source aggregation; no silent cap.
    return result

@app.get('/api/global/coverage')
def global_coverage(region: str='world'):
    if region not in REGIONS:raise HTTPException(400,'Unknown geographic region')
    return archive_inventory(region)

@app.get('/api/global/latest')
def global_latest(region: str='world', source: str='VIIRS_SNPP_NRT', days: int=1):
    if region not in REGIONS or source not in LIVE_SOURCES or days not in (1,2,3,4,5):
        raise HTTPException(400,'Choose a supported region, FIRMS NRT source, and a 1–5 day window')
    try:return JSONResponse(latest_hotspots(region,source,days),headers={'Cache-Control':'no-store'})
    except ValueError as exc:raise HTTPException(400,str(exc)) from None

@app.get("/api/investigation")
def investigation(region: str="alberta_province", start: str="2023-05-01",
                  end: str="2023-10-31", mode: str="real", month: str="", bbox: str=""):
    validate_params(region,start,end,mode)
    focus=parse_focus_bbox(bbox,region)
    if month:
        if len(month)!=7 or month[4]!='-' or not month[:4].isdigit() or not month[5:].isdigit() or not 1<=int(month[5:])<=12:
            raise HTTPException(400,"Invalid selected month")
        if not (start[:7] <= month <= end[:7]):
            raise HTTPException(400,"Selected month is outside date range")
    return investigate(region,start,end,mode,month,focus)

@app.get("/api/investigation/agency-match")
def investigation_agency_match(region: str="alberta_province", year: int=2023,
                               days: int=3, distance_km: float=20.0):
    if region not in ("alberta_province","alberta_boreal") or year<2000 or year>2100 or days>7 or days<0 or distance_km<1 or distance_km>50:
        raise HTTPException(400,"Unsupported agency comparison parameters")
    return agency_match(region,year,days,distance_km)

@app.post("/api/context/alberta/import-csv")
async def import_alberta_csv(request: Request, x_admin_token: str | None=Header(default=None)):
    admin_required(x_admin_token)
    raw=await request.body()
    if len(raw)>50_000_000:
        raise HTTPException(413,"Alberta agency CSV upload exceeds 50 MB. Use scripts/import_alberta_history.py")
    try:
        rows=io.StringIO(raw.decode("utf-8-sig"),newline="")
        out=import_agency_csv(rows)
    except (ValueError, UnicodeDecodeError) as exc:
        raise HTTPException(400, str(exc)) from exc
    return out

@app.get("/api/context/alberta")
def get_alberta_context(year: int = 2023):
    try:
        return JSONResponse(agency_context(year), headers={"Cache-Control": "no-store"})
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

@app.get("/api/watch/live")
def watch_live(region: str = "alberta_province"):
    """Opt-in NRT observation check, not a verified fire incident or predictive forecast."""
    if region not in REGIONS:
        raise HTTPException(400,"Unknown region")
    if region=='world':
        return JSONResponse({'status':'unavailable','alerts':[], 'note':'For World, use the single-source Global Atlas live check instead of a multi-satellite alert cluster. No current fires have been verified.'},headers={'Cache-Control':'no-store'})
    return JSONResponse(live_watch(region), headers={"Cache-Control":"no-store"})


@app.post("/api/ingest/nasa")
def ingest_nasa(payload: ImportNASA, x_admin_token: str | None=Header(default=None)):
    admin_required(x_admin_token)
    if payload.region not in REGIONS: raise HTTPException(400,"Unsupported region")
    try:
        out=fetch_nasa(payload.region,payload.start_date,payload.end_date,payload.products)
    except ValueError as e:
        raise HTTPException(400, str(e))
    return {"status":"ok",**out}

@app.post("/api/import/csv")
async def import_csv(request: Request, product: str=Query(...), x_admin_token: str | None=Header(default=None)):
    admin_required(x_admin_token)
    if product not in SOURCES: raise HTTPException(400,"Unsupported product")
    raw=await request.body()
    if len(raw)>9_000_000: raise HTTPException(413,"Upload exceeds 9 MB")
    try:
        text=raw.decode("utf-8-sig")
        parsed=parse_csv(text,product,mode="real",origin="User imported FIRMS-format CSV (not independently verified)")
        inserted=insert_rows(parsed)
    except (ValueError, UnicodeDecodeError) as e:
        raise HTTPException(400,str(e))
    return {"status":"ok","inserted":inserted,"parsed":len(parsed),"product":product}

@app.get("/api/export/brief.md")
def export_brief(region: str="northern_ontario", start: str="2021-01-01", end: str="2024-12-31", mode: str="demo",bbox: str=""):
    validate_params(region,start,end,mode)
    focus=parse_focus_bbox(bbox,region)
    result=compute_analysis(region,start,end,mode,focus)
    s=result["summary"]
    label="**ILLUSTRATIVE DATA ONLY — NOT NASA OBSERVATIONS**" if mode=="demo" else "**Real mode — verify imported provenance and completeness**"
    lines=[f"# BLINDSPOT — Seasonal observation briefing: {REGIONS[region]['name']}",
           f"Period: {start} through {end}",label,"",
           "## Historical observation summary",s["headline"],s["explanation"],
           f"MODIS-only grid-days: {s['modis_only']:,}",f"VIIRS-only grid-days: {s['viirs_only']:,}",
           f"Both sensor families: {s['both']:,}","",
           "## Interpretation and decision","Review the highest activity months for potential seasonal monitoring planning,",
           "subject to local expert judgment, official forecasts and verification of data coverage.","",
           "## Methodology",result["methodology"]["grid"],result["methodology"]["harmonization"],"",
           "## Limitations"]
    lines.extend("- "+x for x in result["methodology"]["limitations"])
    if mode=='real' and REGIONS[region].get('grid_projection')=='global':
        lines.extend(['','## Geographic coverage disclosure',
          ('WORLD VIEW IS NOT A WORLD ARCHIVE: only Alberta May–October 2023 is bundled; no full-Earth historical coverage is established.'
           if region=='world' else
           'Real archive completeness for the selected geographic region must be verified independently. The bundled real ZIPs cover Alberta only.'),
          'Global Equal Earth EPSG:8857 10-km cells are used for every region in this edition; old Canada-grid counts will differ.'])
    if mode == 'real' and region in ('alberta_province', 'alberta_boreal') and start[:4] == end[:4]:
        agency = agency_context(int(start[:4]))
        lines.extend(['', '## Independent Canadian agency context (NOT satellite counts)'])
        if agency['status'] == 'loaded':
            lines.append(f"Government of Alberta reported wildfire incidents in {start[:4]} (FULL calendar year; not necessarily this selected NASA date window): {agency['count']:,}.")
            lag=agency.get('discovery_to_report') or {}
            if lag.get('median_minutes') is not None:
                lines.append(f"Agency discovery-to-report median: {lag['median_minutes']} minutes among {lag['sample_size']} records with valid fields. This is NOT satellite detection latency or website posting delay.")
            lines.append('Agency fire origins and NASA satellite hotspots have different units and coverage; no one-to-one match is claimed.')
        else:
            lines.append('Official Alberta incident CSV NOT IMPORTED. No number of agency-confirmed fires or time delay can be inferred.')
        lines.append('Official record: https://open.canada.ca/data/en/dataset/a221e7a0-4f46-4be7-9c5a-e29de9a3447e')
    if mode=='real':
        evidence=investigate(region,start,end,mode,custom_bbox=focus)
        quality=evidence['quality']
        years=evidence['historical_years']
        lines.extend(['', '## Data-quality gate',
            f"Raw observations in selected period: {quality['raw_records']:,}.",
            f"NASA type-0 presumed vegetation observations included: {quality['presumed_vegetation']:,}.",
            f"Non-vegetation/static/offshore/volcanic source types excluded: {quality['excluded_other_types']:,}.",
            f"Unclassified observations retained but reported separately: {quality['unclassified']:,}.",
            'Type 0 is not a confirmed wildfire. Confirm incident status with the relevant fire management agency.',
            '', '## Blindspot investigation',
            f"Selected grid-days: {evidence['totals']['union']:,}; MODIS-only: {evidence['totals']['modis_only']:,}; VIIRS-only: {evidence['totals']['viirs_only']:,}; both: {evidence['totals']['both']:,}.",
            'These are co-observed grid-day relationships, not accuracy, false negatives, or individual fire counts.',
            '', '## Historical baseline and sensor calibration'])
        anoms=[a for a in evidence['anomalies'] if a['status']=='comparable' and start[:7]<=a['month']<=end[:7]]
        if anoms:
            for a in anoms[:15]:
                lines.append(f"{a['month']}: {a['observed']:,} observed union cell-days; median {a['baseline_median']} in {a['comparison_years']} other covered years; change {a['change_pct']}%.")
        else:
            lines.append(f"Unavailable. Only {len(years)} fully covered overlapping archive year(s) present ({', '.join(map(str,years)) or 'none'}). At least three OTHER comparable years are needed for a defensible anomaly.")
        cal=evidence['calibration']
        if cal['status']=='experimental_holdout':
            lines.append(f"Provisional MODIS->VIIRS scale {cal['multiplier']} fitted on earlier years; unseen {cal['heldout_year']} heldout WAPE raw {cal['heldout_wape_raw_pct']}%, adjusted {cal['heldout_wape_scaled_pct']}%. NOT fully validated sensor harmonization.")
        else:
            lines.append('A quantitative inter-sensor calibration is NOT available: three or more overlapping full archive years are required for held-out evaluation.')
        lines.extend(['', '## Suggested analyst next steps',
            '1. Investigate the months with more observed grid-day activity in the available archived period; do not infer anomaly without a baseline.',
            '2. Examine VIIRS-only and MODIS-only grid-days and investigate satellite coverage and time-of-day differences.',
            '3. Independently cross-check nearby agency fire records and historical burned-area products; do not conflate reporting units.',
            '4. Request additional multi-year historical FIRMS archives and document their complete coverage before making seasonal comparisons.'])
    lines.extend(['', '## Data sources','NASA FIRMS: https://firms.modaps.eosdis.nasa.gov/', 
                  "Canadian historical context: https://cwfis.cfs.nrcan.gc.ca/en/fire-history"])
    return PlainTextResponse("\n\n".join(lines),media_type="text/markdown",headers={
        "Content-Disposition":f'attachment; filename="blindspot-{region}-brief.md"'})

@app.get("/api/export/monthly.csv")
def export_monthly(region: str="northern_ontario", start: str="2021-01-01", end: str="2024-12-31", mode: str="demo",bbox: str=""):
    validate_params(region,start,end,mode)
    focus=parse_focus_bbox(bbox,region)
    result=compute_analysis(region,start,end,mode,focus)
    if mode=='real':
        covered=_history(region,'real',focus)['complete']
        for item in result['timeline']:
            item['coverage']='complete' if item['month'] in covered else 'unverified'
    else:
        for item in result['timeline']:item['coverage']='synthetic_demo'
    stream=io.StringIO()
    writer=csv.DictWriter(stream,fieldnames=list(result["timeline"][0].keys()))
    writer.writeheader(); writer.writerows(result["timeline"])
    return Response(stream.getvalue(),media_type="text/csv",headers={
      "Content-Disposition":f'attachment; filename="blindspot-{region}-monthly.csv"'})

# Static frontend loaded from the same origin. API key remains on the server.
app.mount("/assets", StaticFiles(directory=FRONTEND), name="assets")

@app.get("/")
def index():
    return FileResponse(FRONTEND/"landing.html")

@app.get("/observatory")
def observatory_story():
    return FileResponse(FRONTEND/"observatory.html")

@app.get("/explore")
def explorer():
    return FileResponse(FRONTEND/"index.html")
