# Alberta 2023 real NASA FIRMS data edition

**This build includes actual NASA FIRMS historical archive data imported from the user-provided 2023 Alberta MODIS and S-NPP VIIRS ZIPs.** You do **not** need a FIRMS MAP_KEY or CSV uploads to explore these historical observations. MapTiler's optional premium basemap still requires a public MapTiler API key.

## Start on Windows
```powershell
cd "C:\Users\asmaa\Downloads\Parallax_BLINDSPOT_Alberta2023_RealData"
py -m pip install -r backend/requirements.txt
py -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8765 --reload
```
Open http://127.0.0.1:8765.

**Select:** Region: Alberta (province archive); Mode: Real FIRMS records; Start: 2023-05-01; End: 2023-10-31; click Analyze region.

### Important changes
- Added **Alberta (province archive)** region to match the archived Alberta data download. The region selector is an approximate bounding box; source observations were downloaded from NASA's Alberta region request.
- Raised in-memory analysis result ceiling from 250,000 to 1,000,000 observation records so the full 2023 season is not silently truncated. The analysis may run more slowly for a full season, depending on your computer.
- No API keys, admin passwords, or private user data are embedded in this distribution.
- Original synthetic demo records remain in Demo mode and are separated from Real FIRMS records.
- Real records are from NASA FIRMS archive request #849825 (MODIS C6.1) and #849826 (S-NPP VIIRS C2), Alberta, May 1 through October 31, 2023.
- **Scientific limitations:** This app aligns fire observations to a 10-km grid and UTC dates and deduplicates within each sensor family. It does NOT calibrate differences in orbital coverage, clouds, or sensor detection sensitivity. A thermal hotspot is not a verified individual wildfire, and MODIS/VIIRS hotspot counts cannot be interpreted as directly comparable fire counts.

For deployment, prefer the separately provided clean starter without a large bundled SQLite dataset, and load official data on the server. If pushing this code to GitHub, `.gitignore` excludes local `.sqlite3` databases; the full dataset will not appear in the GitHub repo by default.

---

# PARALLAX BLINDSPOT
### NASA Space Apps Challenge 2026 — MODIS & VIIRS Hot Spot Harmonization

**The fire history investigator for seasonal preparedness analysts.**

BLINDSPOT asks: **When has satellite-observed burning been most active, and where do sensor differences make the record uncertain?** Rather than another real-time fire alert map, it presents an interactive calendar and an explainable sensor comparison. It makes a defensible *prototype-level* spatial/temporal alignment across MODIS and VIIRS observation records. It does **not** claim to calibrate their detection sensitivities.

## Product scope and stakeholders

**Primary user:** regional wildfire seasonal-readiness analyst or land manager.  
**Core job:** review historical burning activity, identify candidate peak monitoring months, interrogate observational differences, and export an evidence-backed pre-season brief.  
**Not designed for:** emergency dispatch, evacuation, live fire alerts, forecasts or precise ignition counts.

**One-minute user flow:** choose Northern Ontario, Alberta Boreal or B.C. Interior → review a yearly fire activity calendar → activate **Satellite X-Ray** to see MODIS and VIIRS exclusive/matched observations → examine the **Fire DNA** monthly fingerprint → download a **Readiness Brief** stating the evidence and limitations.

## What is implemented

- Complete frontend served at `/`, responsive, light/dark mode, Leaflet map with MapTiler vector Dataviz Dark/Light + Satellite/Hybrid basemap switching, free CARTO fallback, zoom/scale/reset and offline scatter fallback
- FastAPI backend, persistent SQLite data store, data validation, health check and OpenAPI docs at `/docs`
- NASA FIRMS API server-side ingestion (`MODIS_SP`, `VIIRS_SNPP_SP` defaults) up to 21 calendar days; the API itself has a 1–5 day/request limit, so calls are chunked
- Historical FIRMS-format CSV import for longer time series (NASA Archive Download is requested separately)
- Spatial/temporal alignment: projected Canadian 10-km grid cells (EPSG:3978) × UTC day; each sensor is deduplicated within grid-day
- Matched, MODIS-only, VIIRS-only and union active-grid-day counts, months/years calendar, month selection, seasonal fingerprint
- Briefing Markdown and CSV export; explicit provenance and scientific caveats
- Sample synthetic records for interactive demonstrations (**not NASA data**) and configurable token-guarded imports
- Automated API/unit tests, Dockerfile, Compose config, source documentation

## Quickstart — local (Python 3.11+)

```bash
cd parallax-blindspot
python -m pip install -r backend/requirements.txt
python scripts/seed_demo.py
python -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000 --reload
```

Open **http://127.0.0.1:8000**. The default is **ILLUSTRATIVE DATA MODE**, prominently labeled. The bundled demo database is deliberately synthetic; **do not show its numbers as observed wildfire facts**.

To use real data:

1. Request the free NASA FIRMS **MAP_KEY** at https://firms.modaps.eosdis.nasa.gov/api/map_key/.
2. Set the environment variable before launching, e.g. on macOS/Linux: `export FIRMS_MAP_KEY='your-key-here'`; on PowerShell: `$env:FIRMS_MAP_KEY='your-key-here'`.
3. Restart the API, choose **Data Studio**, and import MODIS/VIIRS records. Then select **Real FIRMS records** and dates that match the import.
4. To build a multi-year calendar, request and download science-quality historical CSV files at https://firms.modaps.eosdis.nasa.gov/download/ and import each sensor separately. NASA may process the request asynchronously and email a download link.
5. Use the date range and region that actually have records; no matches means no records loaded for that slice, **not proof of no fires**.

**Admin protection:** configure a strong `ADMIN_TOKEN` environment variable for hosted deployments. Enter it in Data Studio when importing. Do not put the FIRMS key in frontend code. On local development, imports can run without a token; `APP_ENV=production` refuses to start unless `ADMIN_TOKEN` is set.

## MapTiler interactive maps (added in v2)

**Already integrated:** The app uses Leaflet with the MapTiler Leaflet SDK vector plugin. Use the `BASEMAP` selector above Satellite X-Ray for **Auto**, **Dataviz Dark**, **Dataviz Light**, **Satellite imagery**, or **Satellite + labels (Hybrid)**. When your website theme changes, the Auto option follows it. All observation circles, provenance popups, date/month filtering and MODIS/VIIRS toggles continue working on top of the chosen basemap.

**Configure (choose one method):**

1. Quickest, no restart: Open **Data Studio → Option C — Premium map styles**, paste a **MapTiler public browser API key**, and click **Apply MapTiler key**. This is saved to *sessionStorage* for this tab only; it is not sent to your Python backend.
2. For hosted demos: set `MAPTILER_API_KEY` in `.env` (Docker) or as an environment variable (local Python), then restart. The `/api/config` endpoint exposes it **intentionally** because browser tile requests require a public key. Restrict its use to your domain(s) in the MapTiler dashboard.
3. Get a key at https://cloud.maptiler.com/ (free prototype/noncommercial tier is subject to limits and attribution rules).

**No key?** The app still displays real geographic maps using CARTO Dark/Light with OpenStreetMap attribution. Satellite/Hybrid requires a MapTiler key. The background imagery is *not* necessarily from the fire observation date. NASA FIRMS observations require separate ingestion and are never substituted with synthetic values in Real FIRMS mode.

**CDN dependencies:** Browser needs connectivity for Leaflet, MapTiler SDK and plugin, and external map tiles. If Leaflet cannot load, the app displays an offline geographic scatter coordinate reference (not a real basemap). The app does not bundle offline geographic tiles.

**Map source references:** https://docs.maptiler.com/leaflet/examples/vector-tiles-in-leaflet-js/ and https://www.maptiler.com/cloud/pricing/.

## Quickstart — Docker

```bash
cp .env.example .env
# Edit .env with FIRMS_MAP_KEY and ADMIN_TOKEN
# For public hosting also set APP_ENV=production
docker compose up --build
```

Open http://localhost:8000. The app is portable to most container hosts. Configure TLS, persistent storage, authentication/rate limiting, and monitoring before public use.

## API overview

| Route | Purpose |
|---|---|
| GET `/api/config` | Supported regions and data status |
| GET `/api/health` | Health check |
| GET `/api/analysis` | Calendar, sensor comparison, brief inputs |
| POST `/api/ingest/nasa` | Server-side NASA FIRMS area API import |
| POST `/api/import/csv?product=MODIS_SP` | Upload a FIRMS-format CSV body |
| GET `/api/export/brief.md` | Evidence-backed planning brief |
| GET `/api/export/monthly.csv` | Monthly spatial grid-day counts |
| GET `/docs` | Swagger / OpenAPI reference |

Examples:

```bash
curl 'http://127.0.0.1:8000/api/analysis?region=alberta_boreal&start=2023-01-01&end=2023-12-31&mode=demo'
```

Import with a key configured server-side:

```bash
curl -X POST 'http://127.0.0.1:8000/api/ingest/nasa' \
  -H 'Content-Type: application/json' \
  -H 'X-Admin-Token: YOUR_ADMIN_TOKEN' \
  -d '{"region":"northern_ontario","start_date":"2023-06-01","end_date":"2023-06-05","products":["MODIS_SP","VIIRS_SNPP_SP"]}'
```

## Test

```bash
python -m pip install -r backend/requirements-dev.txt
PYTHONPATH=backend pytest -q backend/tests
node --check frontend/app.js
```

On Windows PowerShell, use `$env:PYTHONPATH='backend'; pytest -q backend/tests`.

## Scientific honesty (read before judging)

- This implementation performs **spatial/temporal alignment**, not statistically validated sensor-bias harmonization. For a scientific production version, add overpass/cloud coverage controls and calibration against independent observation records.
- All numbers are **satellite hotspot detection grid-days**, not individual fires, verified fire areas, ignition counts or actual risk scores.
- A 10-km cell-day with hits in both sensors says **both reported at least one hotspot** in the same cell/UTC date; it does **not** establish that they observed the same fire or simultaneous conditions.
- Projected EPSG:3978 grid cells are 10 km × 10 km in map coordinates, not universally equal-area surface cells.
- There is no trusted measure of false negatives or missing coverage in the MVP.
- The **demo data are entirely synthetic**, never blended into real mode.
- **Canadian agency records are linked as potential external validation references, not automatically integrated**. They have different definitions than hotspots and may require licensing or preparation.

## Real sources / next integrations

- NASA FIRMS API and data availability: https://firms.modaps.eosdis.nasa.gov/api/area/
- NASA FIRMS archive download (MODIS 2000 onward, VIIRS S-NPP 2012 onward): https://firms.modaps.eosdis.nasa.gov/download/
- Natural Resources Canada CWFIS historical fire explorer: https://cwfis.cfs.nrcan.gc.ca/en/fire-history
- Government of Alberta wildfire history CSV 2006–2025: https://open.canada.ca/data/dataset/a221e7a0-4f46-4be7-9c5a-e29de9a3447e
- City of Brampton GeoHub may be useful for other challenge applications, but is **not** an appropriate substitute for satellite hotspot history.

## Transparency / work remaining

This is a tested hackathon **starter/MVP**, not certified production wildfire software. Real NASA network ingestion needs your FIRMS MAP_KEY and a live end-to-end test; it cannot be validated without one. Before production deployment implement user authentication, API rate limits, upload quotas, external data license review, retries/caching, monitoring, source validation, historical coverage analysis, sensor-specific calibration, and Canadian agency cross-validation.

See `docs/PRODUCT_BRIEF.md`, `docs/SCIENCE.md`, `docs/DEMO_SCRIPT.md`, and `docs/DATA_SOURCES.md`.
