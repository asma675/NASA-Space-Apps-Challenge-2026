# Parallax BLINDSPOT — Observatory Experience / NASA World 2025–2026 Update

**Current complete edition:** The original observatory story, Globe, Blindspot Reveal, historical calendar, Watchtower, Canadian evidence, and seasonal brief are preserved. New NASA global data are already bundled; no API key or manual ZIP extraction is needed.

- World requests **#850371 MODIS C6.1** and **#850372 VIIRS S-NPP C2**: **20,659,624 original rows** in two preserved ZIP files. Dates cover parts of **November 12, 2025 to November 13, 2026** (S-NPP VIIRS NRT through November 2, 2026).
- **19,573,939 eligible records** indexed into **5,708,602 unique 10-km Equal Earth UTC grid-days**; standard-processing `type=1/2/3` excluded; NRT (no type field) labeled provisional/unclassified.
- Separate full-resolution Alberta 2023 archive: **547,021 raw records**, kept in `data/blindspot.sqlite3` with original source ZIPs.
- **World June 2026** is the recommended default; both sensors then have standard-processing data. Choose **Alberta 2023** from the one-click case-study control to see the prior record and Canada Evidence Lab.
- A global 2025–26 archive does **not** provide a multi-decade trend or validated sensor calibration. The two scopes are never misrepresented as one comparable climate baseline.

**Start on Windows:**

```powershell
cd "C:\Users\asmaa\Downloads\Parallax_BLINDSPOT_Observatory_World_Data"
py -m pip install -r backend/requirements.txt
py -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8765 --reload
```

Open **http://127.0.0.1:8765** for the animated observatory story, or **http://127.0.0.1:8765/explore** for the worldwide NASA comparison.

Full provenance and limitations: [`docs/WORLD_DATA_2025_2026.md`](docs/WORLD_DATA_2025_2026.md). The older README sections below describe the **original Alberta-only edition**, before this global dataset was added.

---

# Parallax BLINDSPOT — Observatory Experience Edition

An original immersive landing page and guided **Northern Watch House** narrative, with a distinct Parallax visual language (boreal greens, copper, field-guide typography and hand-drawn SVG observatory), plus a redesigned Explore front end. The earlier NASA analysis engine, comparison maps, source import, Watchtower, calendar, archive and evidence lab are preserved.

## Start on Windows

1. Extract the complete ZIP. Open its extracted `Parallax_BLINDSPOT_Observatory_Edition` folder in VS Code.
2. Open a PowerShell terminal and run:

```powershell
py -m pip install -r backend/requirements.txt
py -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8765 --reload
```

Open **http://127.0.0.1:8765/**. The new routes are:

- `/` — original immersive editorial landing, real NASA archive counter and clickable observatory doorway
- `/observatory` — animated four-chapter interactive story (Maya → sensors → blindspot → decision)
- `/explore` — full satellite comparison, World Atlas, rotating WebGL globe, calendar, Watchtower, Fire DNA, Agency Evidence and export brief
- `/api/config` — provenance and database counts

The **Illustrated Atlas** basemap uses geographically accurate OpenStreetMap raster tiles with a designed color treatment. It is *not* a custom topological model or a substitute for real observation data. Users can switch back to Esri World Imagery in the comparison map and main map.

### What is and is not available

The complete ZIP includes **547,021 real NASA FIRMS raw observations**, from MODIS 90,039 and VIIRS S-NPP 456,982, for **Alberta, Canada, May 1–October 31, 2023**, plus original source archives. The spatial comparison uses verified eligible records, excludes certain NASA-classified non-vegetation thermal events, and normalizes to a common grid/day. This is **not full sensor-bias correction**. Other world regions or multi-year anomaly baselines require additional official archive downloads. Recent global NASA checks require your own `FIRMS_MAP_KEY`. A thermal hotspot is not a confirmed wildfire or prediction.

### Design inspiration and original work

The multi-step editorial storytelling and explorer-separated navigation are inspired by modern science-explainer experiences, including [Zij](https://zij.watch/) (2026). The building illustration, HTML, CSS, transitions, guided scene, and explorer layout are newly authored for **Parallax Labs**; no Zij source files, branding or artwork have been copied. Prior Parallax features and the Wildfire Watch satellite-map aesthetic remain part of this app. Source imagery/maps retain their individual provider attribution.

**Submission note:** This version was not pushed to GitHub or hosted publicly. Test external map/globe CDN availability and a complete browser demo before submitting. Do not upload `.env` or the ~200MB local SQLite file to GitHub; the smaller code ZIP omits both the database and source archives.

---

# 🌍 PARALLAX BLINDSPOT — Global Investigation Edition (NASA Space Apps 2026)

**One planet. Two satellite stories.** A full-stack global-capable satellite fire-history investigation tool, with an interactive World Atlas, NASA FIRMS recent-source selection, side-by-side Satellite Blindspot Reveal, 3D globe, historical calendar, custom area investigation, Canadian evidence lab, and source-aware readiness brief.

### What is truly included

- **547,021 genuine NASA FIRMS observations** in an embedded `data/blindspot.sqlite3`, **Alberta May 1–October 31, 2023 only**; original MODIS and VIIRS ZIPs also included in the *Complete* distribution.
- **Global navigation and globe/map visualization**. Other countries do not have historical archives preloaded. A world-shaped map alone does not imply global satellite coverage.
- **Optional global recent NASA data** via private `FIRMS_MAP_KEY`, starting with `VIIRS_SNPP_NRT` and a one-day `world` query. The recent signals are shown separately and do not change historical stats.
- **Unified global Equal Earth EPSG:8857 grid**, 10-km projected cell × UTC day, for World and all regional views. This revision changes Alberta grid-day figures versus legacy Canada EPSG:3978. The validated new figures are in `docs/WORLD_ATLAS_AND_DATA_SCOPE.md`.
- Not a calibrated multi-decade sensor series, an ignition forecast, a verified wildfire alert, or operational dispatch advice.

### Start on Windows

```powershell
cd "C:\Users\asmaa\Downloads\Parallax_BLINDSPOT_Global_Edition"
py -m pip install -r backend/requirements.txt
py -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8765 --reload
```

Open **http://127.0.0.1:8765**. It showcases **Real FIRMS → Alberta May–October 2023** by default, with World Atlas above the main analysis. To configure optional recent worldwide NASA checks, create `.env` containing `FIRMS_MAP_KEY=YOUR_PRIVATE_KEY` and restart with `--env-file .env`; never commit `.env`.

**Official 2026 submission:** use `docs/SUBMISSION_2026_READY_TO_PASTE.md`, `docs/DEMO_7_SLIDES.md`, and `docs/DEMO_30_SECONDS.md`. The formal demonstration is **≤30 seconds video OR ≤7 slides**, not the separate 3-minute local live pitch.

---

# PARALLAX BLINDSPOT — Investigation Edition

**NASA Space Apps Challenge 2026 · Harmonization of MODIS and VIIRS Hot Spots**  
**Parallax Labs · Original open scientific exploration tool**

> **A fire map shows dots. BLINDSPOT shows which satellite evidence differs, why that uncertainty matters, and what a preparedness analyst should investigate next.**

## 3-minute judges' path

1. **Meet Maya** — an Alberta seasonal-readiness planner who receives conflicting MODIS/VIIRS thermal observation records.
2. **Satellite Blindspot Reveal** — drag the **two synchronized Esri maps** from MODIS to VIIRS, then click **Reveal Blindspots** to expose exclusive and shared *grid-day observations*. Select a month and watch the comparison update.
3. **Own the area** — **Draw your area** by choosing two map corners, then compare that box with the full province. The calendar, comparison and mission brief use the focused region.
4. **Fire Calendar** — investigate recorded months and 2023 seasonal pattern. **NO DATA is not zero** when source archive coverage is unverified.
5. **Evidence Desk / Mission Brief** — 542,775 presumed vegetation hotspots included, 4,246 other thermal anomalies excluded; cross-year anomaly and calibration are explicitly unavailable with one season. Download the evidence-linked decision brief.

**Full pitch:** [`docs/PITCH_3_MINUTES.md`](docs/PITCH_3_MINUTES.md). **Methodological audit:** [`docs/METHODS_AUDIT.md`](docs/METHODS_AUDIT.md).

## The embedded, measured dataset

| NASA FIRMS source | Raw rows | Included as presumed vegetation |
|---|---:|---:|
| MODIS C6.1, archive request 849825 | 90,039 | 90,025 |
| VIIRS S-NPP C2, archive request 849826 | 456,982 | 452,750 |
| **Total** | **547,021** | **542,775** |

Alberta, Canada, May 1–October 31, 2023. Other tagged thermal anomaly types (1/2/3): **4,246** excluded from the principal analysis, not deleted from source files.

**Filtered cell × UTC day counts:** 1,084 MODIS-only; 6,742 VIIRS-only; 9,268 co-observed; 17,094 union; 54.2% co-observation. **This is NOT sensor accuracy.**

## Quickstart (Windows PowerShell)

Extract the **complete** ZIP (which includes `data/blindspot.sqlite3` and the original NASA ZIPs). In that extracted root folder run:

```powershell
py -m pip install -r backend/requirements.txt
py -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8765 --reload
```

Open http://127.0.0.1:8765. **No NASA API key required for the historical archive.** Optional near-real-time checks need a private `FIRMS_MAP_KEY`.

**Tests:** `py -m pip install -r backend/requirements-dev.txt`, then `$env:PYTHONPATH='backend'; py -m pytest -q backend/tests`.

## What is and is not implemented

**Implemented:** globe, Wildfire Watch-style satellite map, sliding and synchronized MODIS/VIIRS maps, one-click reveal, grid-day relationship metrics, custom drawn bounding box, linked monthly fire calendar, Fire DNA, provenance/type filtering, incomplete coverage labels, reusable multi-year ZIP importer, conditional historic anomaly baseline, simple held-out calibration diagnostic when sufficient real years exist, official Alberta CSV importer and spatial/date coincidence checker when records are available, CWFIS optional live tile overlays, Watchtower NRT checking, evidence-linked export.

**Not supplied or not established:** additional FIRMS years; full multi-year calibrated sensor record; confidence interval corrected for cloud/overpass bias; complete nationwide historical coverage; independent Alberta incident CSV records; quantitative predictive fire ignition risk. The app **does not forecast wildfire ignition** or claim a missing MODIS hit is a missed fire.

To extend with real years read [`docs/IMPORT_MORE_YEARS.md`](docs/IMPORT_MORE_YEARS.md). For source credits and prior work disclosure read [`docs/ATTRIBUTIONS.md`](docs/ATTRIBUTIONS.md).

---

# PARALLAX BLINDSPOT — Judge Edition

**NASA Space Apps Challenge 2026 · Parallax Labs**  
**Challenge:** Harmonization of MODIS and VIIRS Hot Spots

> One fire season. Two satellite stories. One evidence-based way to decide what to investigate next.

## Who this is for / what problem it solves

**Maya is a fictional Alberta wildfire preparedness analyst.** Before a fire season, she needs to know which past months saw the most satellite-observed activity and where MODIS and VIIRS disagree. Generic fire maps can imply one definitive picture, even though the two instruments differ in detection sensitivity and overpass timing. BLINDSPOT lets Maya compare a shared spatial/UTC-day index, select seasonal monitoring priorities and check optional near-real-time NASA hotspot feeds. It does **not** predict wildfire ignitions or replace official incident warnings.

## Run on Windows (the complete downloaded ZIP)

1. Extract the complete ZIP. The folder contains `frontend`, `backend`, `scripts`, **a preloaded `data/blindspot.sqlite3` (~197 MB)**, and the original NASA ZIPs in `data/raw`. You can double-click `START_WINDOWS.bat` after installing dependencies.
2. Open a PowerShell terminal inside the extracted folder (the folder containing `backend`).
3. Run:

```powershell
py -m pip install -r backend/requirements.txt
py -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8765 --reload
```

Visit **http://127.0.0.1:8765**. The app automatically selects **Alberta (province archive) / Real FIRMS records / 2023-05-01 to 2023-10-31** if the historical dataset exists. If your previous Uvicorn instance is still running, press Ctrl+C in that other terminal before restarting.

**Verify the database:** open `http://127.0.0.1:8765/api/config`. Look for `mode: real`, `product: MODIS_SP` count `90039` and `product: VIIRS_SNPP_SP` count `456982`. If only demo counts appear, you launched an old folder or the SQLite file is missing. Do not run `seed_demo.py` to fix this; it only adds synthetic examples.

## Data included in the full offline package

| Source | Request | Date window | Stored records |
|---|---|---|---:|
| MODIS Collection 6.1 Standard Processing | NASA FIRMS #849825 | 2023-05-01–2023-10-31 | 90,039 |
| S-NPP VIIRS Collection 2 Standard Processing | NASA FIRMS #849826 | 2023-05-01–2023-10-31 | 456,982 |
| **Total** | | | **547,021** |

These are thermal hotspot *detections*, not verified individual fires. The complete ZIP also bundles the two original NASA source ZIPs in `data/raw/` so the dataset is independently reproducible without manual downloads. The SQLite DB also contains 7,357 **clearly separated synthetic** records for optional Demo mode. The included database is excluded from Git by `.gitignore`, so **GitHub code alone does not include observations**.

**Rebuild from original NASA ZIPs if needed:** the full release ZIP already includes **one** MODIS ZIP and **one** VIIRS ZIP in `data/raw/` (ignored by Git). Do **not** unzip them; run:

```powershell
py scripts/import_firms_archives.py --modis "data/raw/DL_FIRE_M-C61_849825.zip" --viirs "data/raw/DL_FIRE_SV-C2_849826(1).zip"
```

The importer reads ZIP entries directly, streams batches of records, validates coordinates/dates, and avoids duplicate reimport. If your own file names differ, substitute them. The archive importer is safe to rerun and will not duplicate records.

## Features / 3-minute demo path

1. **Rotating globe:** decorative 3D look at a sampled subset of *real historical* observation coordinates, using [Globe.GL](https://globe.gl/) with a CSS fallback if external WebGL/CDN assets cannot load. This is not a real-time global fire map.
2. **Satellite X-Ray:** filter sampled points by MODIS, VIIRS, or unmatched grid-days; map uses the previous Wildfire Watch Canada project's Esri imagery with optional Esri reference labels by default. Full analytical counts are calculated on the complete filtered observations.
3. **Watchtower:** historical seasonal-monitoring watch signal based on selected records, plus an **optional** near-real-time NASA NRT detection check when a server-side `FIRMS_MAP_KEY` is present. The NRT feed uses NOAA-20 and NOAA-21 VIIRS data. An NRT signal is not a verified incident or future fire prediction.
4. **Time Travel + Fire DNA:** which months had the highest historical activity? Click the calendar to narrow the 2D map and globe interpretation.
5. **Readiness Brief:** export an evidence-backed summary of how to prioritize further verification.

Full demo script: [`docs/PITCH_3_MINUTES.md`](docs/PITCH_3_MINUTES.md).

## Watchtower: accurate alerts and detection timeline

Optional GET `/api/watch/live?region=alberta_province` checks the NASA FIRMS Area API for near-real-time VIIRS detections within ~48 hours. It returns **no actual live status** without a key; it says `not_configured`. If the NASA feeds fail, it says `unavailable` (not "no fires"). If connected, it groups **type 0 (presumed vegetation)** observations by **10 km projected cell × UTC date**, returns the 15 latest clusters and draws orange NRT markers on the map. To control NASA requests the feed is cached for 15 minutes. Browser notifications are opt-in and only run while the browser tab remains open; **there is no SMS, background push, or evacuation-alert system**.

The live status displays **first satellite-observed time** and **first time BLINDSPOT successfully checked the feed**, with their elapsed gap. **Neither is the fire ignition/start time.** The acquisition timestamp is the spacecraft's observation time, NOT when NASA published it. Thus the elapsed gap is **NOT** official agency alert latency, NASA publication delay or "how long responders took to notice." Do not make those claims in a demo.

For actual confirmed incident status, use the official [Government of Alberta Wildfire Status](https://www.alberta.ca/wildfire-status) linked from Watchtower. A scientifically validated wildfire danger forecast would require weather, fuels, lightning, human activity and independent validation; this demo instead offers an honest *historical seasonal-watch signal*.

### Add a NASA FIRMS key for optional NRT checks

Create a private `.env` file next to `backend`:

```dotenv
FIRMS_MAP_KEY=PASTE_YOUR_REAL_NASA_FIRMS_KEY_HERE
```

Then start with:

```powershell
py -m pip install python-dotenv
py -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8765 --reload --env-file .env
```

Get a free key via [NASA FIRMS API](https://firms.modaps.eosdis.nasa.gov/api/map_key/). **Do not commit `.env` to GitHub or paste the key in browser source.** `FIRMS_MAP_KEY` is not needed for 2023 archives or the Esri basemap. Use Data Studio to set an optional MapTiler public browser key. Live NRT requests require working internet and available NASA products; these network operations were mocked in automated tests and need testing against your real key.

## Methodology / limitations

Analysis aligns observations from each sensor family to **10-km global Equal Earth projected grid cells (EPSG:8857) × UTC day**, deduplicating each sensor within a cell-day. This is a prototype spatial/temporal common representation, **not detection-probability calibration**; there are no overpass/cloud controls, ground-truth incident labels, ignition prediction, risk probabilities, burned-area estimates, or real validated latency measures. The source archives include observations categorized by NASA as types other than presumed vegetation fire; historical metric totals use NASA type-0 presumed vegetation detections (and disclose unclassified rows separately); non-vegetation types 1/2/3 are excluded. Users should verify hypotheses with agency incident records and official fire danger products before decisions.

## Development and tests

```powershell
py -m pip install -r backend/requirements-dev.txt
$env:PYTHONPATH="backend"
py -m pytest -q backend/tests
node --check frontend/app.js
```

API routes: `/api/config`, `/api/health`, `/api/analysis`, `/api/watch/live`, `/api/ingest/nasa`, `/api/import/csv`, `/api/export/monthly.csv`, `/api/export/brief.md`. Full-page UI uses `frontend` served by FastAPI; no Node build required.

**Distribution:** the release ZIP intentionally includes a ~197 MB SQLite file and is not suitable for direct GitHub commits. For GitHub publish code and importer; host or import the archive separately and document provenance. A public deployment needs stronger authentication, per-endpoint rate limits, job queue/caching, independent validation, data licensing checks, persistent database storage and operational monitoring.

**Credits:** NASA FIRMS standard historical archives (#849825, #849826); Esri / OpenStreetMap geographic basemaps (see displayed map attribution); the earlier [Wildfire Watch Canada HackCanada 2026](https://github.com/asma675/wildfire-watch-canada-HackCanada-2026) map styling; Globe.GL / Three.js. Independent Parallax Labs project, not a NASA or Alberta government emergency service.

---

## Canada Evidence Lab (new)

**This edition retains the embedded NASA 2023 Alberta archive (547,021 genuine FIRMS hotspot records).** It adds *independent* Canadian sources; they never overwrite, merge into, or change the primary MODIS / VIIRS observations and 10-km UTC grid-day calendar.

### 1. Official Alberta historical fire reports — importer and side-by-side evidence

- Data publisher: Government of Alberta, under Open Government Licence — Alberta.
- Dataset: **Historical wildfire data 2006–2025**, available at https://open.canada.ca/data/en/dataset/a221e7a0-4f46-4be7-9c5a-e29de9a3447e.
- Download the CSV from the official site, then use **Canada Evidence Lab → Import Alberta CSV**. Or use PowerShell from the extracted application directory:

```powershell
py scripts/import_alberta_history.py --csv "data/raw/fp-historical-wildfire-data-2006-2025.csv"
```

The file can be stored anywhere; provide its actual path after `--csv`. Alternatively use `py scripts/import_alberta_history.py --download`, which attempts the official public CSV download. This step **requires network access** and may fail if the Alberta server blocks it. Never infer a zero fire count from an unavailable source.

**Why separate?** Each Government of Alberta row represents a reported wildfire (within the agency dataset's scope, especially the Forest Protection Area), whereas each NASA row represents a thermal hotspot *observation*. The UI displays incident counts separately, by calendar year and reported/discovered month. A single wildfire may produce thousands of satellite hotspots. The Alberta **discovered_date** and **reported_date** fields permit an *agency discovery-to-report* interval when both are present. This is **not** ignition-to-detection, FIRMS processing delay, or the site's posting delay. Because the local official CSV could not be fetched in the build environment, this additional source deliberately starts **Not imported**, not with invented numbers.

The source file is excluded from Git. Re-import is idempotent (`source` + `fire_number` + `year`). The optional current UI upload is capped at 50 MB. For hosted deployments, set a strong `ADMIN_TOKEN` to protect import endpoints.

API routes:

- `GET /api/context/alberta?year=2023` — explicit `not_imported` status unless official records have been loaded.
- `POST /api/context/alberta/import-csv` — sends a CSV body; requires `X-Admin-Token` if one is configured.

### 2. Canadian Wildland Fire Information System (CWFIS) — optional live context map layers

The Canada Evidence Lab has user-triggered **current agency-reported active fires** (CWFIF WMS layer `public:cwfif_national_activefires`) and **current Fire Weather Index** (CWFIS WMS `public:fwi`) overlays. These remote services require network access, may migrate or be temporarily unavailable, and are maintained by Natural Resources Canada. **They depict current or updated fire conditions, NOT fire weather / incidents on a historical 2023 date.** They never modify historical NASA analysis. Official catalogue: https://cwfis.cfs.nrcan.gc.ca/en/catalogue. CWFIS 2.0 has migrated several services, so check their published 2026 layer catalogue if WMS requests fail.

### 3. National Burned Area Composite (NBAC) — linked for future validation

NRCan annual composite burned-area polygons: https://cwfis.cfs.nrcan.gc.ca/downloads/nbac/. The large annual spatial datasets are **not bundled or ingested** in this edition; the app labels them as an additional independent reference, not an implemented sensor-bias calibration. Burned area and active-fire detection are not the same physical quantity.

### Source transparency

- Primary NASA dataset: downloaded FIRMS standard-processing 2023 Alberta archives, requests #849825 (MODIS C6.1), #849826 (S-NPP VIIRS C2).
- Agency history: official Alberta dataset only after separately downloaded/imported.
- Operational context: official NRCan CWFIS WMS only when enabled and externally reachable.
- NBAC: documented external source; not locally loaded.

**Challenge framing:** the core deliverable is the historical burning-activity **calendar** and explainable common-cell-day comparison of MODIS/VIIRS. Contextual datasets are for triangulation and human decision-making. BLINDSPOT does not claim cross-sensor detection sensitivity calibration, wildfire ignition prediction, or operational fire alerts.
