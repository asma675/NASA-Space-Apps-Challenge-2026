"""Parallax BLINDSPOT — FastAPI backend and embedded production-build-less frontend."""
from __future__ import annotations
import csv
import io
import os
from contextlib import asynccontextmanager
from datetime import date
from pathlib import Path
from fastapi import FastAPI, HTTPException, Header, Query, Request
from fastapi.responses import FileResponse, JSONResponse, PlainTextResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from .storage import REGIONS, SOURCES, counts, init_db, get_rows, insert_rows
from .analysis import analyze
from .firms import parse_csv, fetch_nasa

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

@app.get("/api/analysis")
def analysis(region: str="northern_ontario", start: str="2021-01-01", end: str="2024-12-31", mode: str="demo"):
    validate_params(region,start,end,mode)
    rows=get_rows(mode,region,start,end)
    result=analyze(rows, REGIONS[region],start,end,mode)
    result["data_origin"]="ILLUSTRATIVE SYNTHETIC DATA — NOT NASA" if mode=="demo" else "NASA FIRMS API or user-imported FIRMS-format CSV; verify provenance"
    result["loaded_observations"]=len(rows)
    result["truncated"]=(len(rows)==250000)
    return result

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
def export_brief(region: str="northern_ontario", start: str="2021-01-01", end: str="2024-12-31", mode: str="demo"):
    validate_params(region,start,end,mode)
    result=analyze(get_rows(mode,region,start,end),REGIONS[region],start,end,mode)
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
    lines.extend(["","## Data sources","NASA FIRMS: https://firms.modaps.eosdis.nasa.gov/",
                  "Canadian historical context: https://cwfis.cfs.nrcan.gc.ca/en/fire-history"])
    return PlainTextResponse("\n\n".join(lines),media_type="text/markdown",headers={
        "Content-Disposition":f'attachment; filename="blindspot-{region}-brief.md"'})

@app.get("/api/export/monthly.csv")
def export_monthly(region: str="northern_ontario", start: str="2021-01-01", end: str="2024-12-31", mode: str="demo"):
    validate_params(region,start,end,mode)
    result=analyze(get_rows(mode,region,start,end),REGIONS[region],start,end,mode)
    stream=io.StringIO()
    writer=csv.DictWriter(stream,fieldnames=list(result["timeline"][0].keys()))
    writer.writeheader(); writer.writerows(result["timeline"])
    return Response(stream.getvalue(),media_type="text/csv",headers={
      "Content-Disposition":f'attachment; filename="blindspot-{region}-monthly.csv"'})

# Static frontend loaded from the same origin. API key remains on the server.
app.mount("/assets", StaticFiles(directory=FRONTEND), name="assets")

@app.get("/")
def index():
    return FileResponse(FRONTEND/"index.html")
