# BLINDSPOT World Atlas — data scope and NASA FIRMS selections

**World mode is implemented. Complete worldwide historical data is NOT embedded.**
The shipped archive covers NASA FIRMS MODIS C6.1 and S-NPP VIIRS C2 for Alberta, Canada, 2023-05-01 through 2023-10-31. These 547,021 real records include 542,775 presumed vegetation-fire detections and 4,246 NASA tagged other thermal sources, which are excluded from the principal vegetation-fire calendar. A thermal hotspot is not an individually verified wildfire.

## What to select on NASA FIRMS

Official NASA area API: https://firms.modaps.eosdis.nasa.gov/api/area/

| UI field | For a global recent check | For a reproducible historical calendar |
|---|---|---|
| Area | **world** | Prefer a manageable country/region bounding box; `world` if your planned archive resources permit |
| Fire Source | `VIIRS_SNPP_NRT` (start with this) | `MODIS_SP` **and** `VIIRS_SNPP_SP` as separate data sources |
| Extra sources | `VIIRS_NOAA20_NRT` and `VIIRS_NOAA21_NRT`; also `MODIS_NRT` | `VIIRS_NOAA20_SP` / `VIIRS_NOAA21_SP` may extend coverage if separately harmonized |
| Day range | `1` globally, up to `5` in NASA's API | Download standard-processed archive CSV or ZIP by year/area |
| Map key | Required; keep private | Not needed once archive ZIPs are downloaded |

API endpoint follows `/api/area/csv/<MAP_KEY>/<SOURCE>/world/1` for the most recent day. Do not commit or publicly link any URL containing your key. Historical `SP` products are preferable for science when available; NRT is preliminary.

## In-app use

1. Extract the complete ZIP. Launch BLINDSPOT with `py -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8765 --reload`.
2. Open **World Atlas**. Choose *World* or a regional preset.
3. Click **Analyze archive**: the historic calendar and Satellite Blindspot Reveal use locally imported NASA records in the chosen extent. In World, **only Alberta 2023** currently has points. Regions with no imported data must never be represented as fire-free.
4. To check near-real-time observations, create a `.env` file with `FIRMS_MAP_KEY=YOUR_KEY`, restart with `--env-file .env`, choose **VIIRS S-NPP NRT** (or NOAA20/21, MODIS), **1 day** for World, and click **Check NASA now**.
5. New NRT points appear in green on the map and on the globe; they do not enter the historical calendar or modify historical statistics. They are *not* verified active fire incidents or ignition forecasts.
6. To explore historical burning outside Alberta, download new **actual** NASA historical archive ZIPs for that area, then import them with the supplied incremental script and a manifest declaring the genuine geographic scope and date window.

## Import more countries and years

Create a JSON manifest (example: `data/raw/other/manifest.json`):

```json
[
  {"file":"amazon_modis_2020.zip","product":"MODIS_SP","start":"2020-01-01","end":"2020-12-31","scope":"amazon"},
  {"file":"amazon_viirs_2020.zip","product":"VIIRS_SNPP_SP","start":"2020-01-01","end":"2020-12-31","scope":"amazon"}
]
```

These names are **examples only**, not files supplied with this application. Request real archive files that cover the claimed region/date interval. Then:

```powershell
py scripts/import_multi_year.py --modis "data/raw/other/amazon_modis_2020.zip" --viirs "data/raw/other/amazon_viirs_2020.zip" --scope amazon --manifest "data/raw/other/manifest.json"
```

The importer does not mark months as complete merely because it found detections. Use a documented full-month, full-region archive request. `--scope world` is only valid for a genuinely worldwide download, not an Alberta ZIP. If importing a narrow rectangle inside a broad preset, don't certify the whole preset with that manifest.

## Harmonization and area comparability

This global edition **uses one Equal Earth projected 10-km (EPSG:8857) grid** for all regions, UTC calendar days, and one sensor-family presence per cell/day. This makes World/Alberta counts directly comparable for identical bounding boxes in the local archive. It is a *spatial-temporal presence alignment*, not a calibrated sensor probability of detection. Neither the spatial grid nor the live preview corrects for clouds, orbital sampling, sensor sensitivity, atmospheric conditions or fire duration.

The method revision changes Alberta's counts versus earlier editions that used Canada EPSG:3978:

- Raw NASA archive records: **547,021** (unchanged)
- Presumed vegetation-fire records: **542,775** (unchanged)
- Other thermal source types excluded: **4,246** (unchanged)
- **17,094** union active grid-days; **9,268** with co-observation; **1,084** MODIS-only; **6,742** VIIRS-only; **54.2%** co-observation, computed using the new Equal Earth grid

The geographical and temporal completeness of World mode is not established. Seasonal anomalies and held-out sensor scaling require additional independently covered years and cannot be claimed for the shipped single season. Source dates and provenance remain inspectable.

## Restrictions and safety

- NASA thermal detections are NOT confirmed fires. Global recent query is not an emergency dispatch service.
- Current monitoring requires the user's key and an actual live network response; empty/unavailable is never labeled zero fires.
- 50MB live response guard and 10-minute cache limit API abuse; worldwide queries are restricted to 1 day in the app.
- Do not reveal API keys in screenshots or GitHub commits. World Atlas's API key stays server-side.
- For confirmed active wildfire incidents, consult the appropriate regional agency, not a hotspot map alone.

NASA data reference: https://firms.modaps.eosdis.nasa.gov/ — MODIS C6.1 and VIIRS S-NPP Collection 2 (user-downloaded archival requests #849825 and #849826).
