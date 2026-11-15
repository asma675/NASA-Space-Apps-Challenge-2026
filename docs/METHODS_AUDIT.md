# NASA BLINDSPOT — independently reproducible methods & limitations

## What the complete ZIP actually contains

- Alberta archive request **849825**, MODIS C6.1, May 1–October 31, 2023: **90,039** source observations.
- Alberta archive request **849826**, S-NPP VIIRS C2, same request window: **456,982** source observations.
- Raw combined observations: **547,021**. Original ZIPs preserved in `data/raw/`.
- NASA `type = 0` (presumed vegetation) included for main burning activity: **542,775** records.
- NASA `type = 1,2,3` excluded: **4,246** tagged nonvegetation/static/offshore/volcanic observations.
- These are *thermal anomaly detections*, not official wildfire event counts. NASA `type 0` is a presumption, not confirmation.

## The comparable unit

Transform each observation WGS84 lat/lon into EPSG:8857 (global Equal Earth, equal-area), take a 10,000 m projected x/y bin, group by UTC acquisition date. Collapse repeats within **each** sensor family to a presence/absence flag. A union grid-day is active when any eligible sensor family has at least one detection.

For the archived Alberta 2023 season (main type-0 filter):

| Category | Cell × UTC day units |
|---|---:|
| MODIS-only | 1,084 |
| VIIRS-only | 6,742 |
| Both MODIS and VIIRS | 9,268 |
| Union | 17,094 |
| Both / union | 54.2% |

A shared projected cell/day does not establish identical overpass timing, the same ignition, equal land area per cell, or a verified wildfire. No agreement measure is interpreted as detection accuracy or a false-negative rate. Map layers show **sampled cell centres**; full analytic totals use every eligible stored observation.

## Missing coverage is not zero

Archive coverage is recorded per product and source request window in `archive_coverage`. A calendar month is `complete` only if both MODIS and VIIRS archive coverage intervals span the *entire month*. Months without complete documented coverage are marked **NO DATA** rather than converted into confirmed zero burning.

For the bundled season May–October 2023 is documented complete for the two original archive requests. Other years are *not* present.

## Fire Season Detective — no fabricated anomalies

A month gets a descriptive anomaly only if that month has a complete two-sensor archive window in **at least three other years**. Its historical comparator is the median of those independent other years. P25/P75 are descriptive reference percentiles, **not uncertainty in satellite sensitivity**. No comparator is produced for this one-year ZIP.

## Calibration Audit — experimental only

When at least **three** independent overlap years with at least **three common fully covered months** are imported, a simple MODIS-to-VIIRS monthly active-cell-day scale can be fit on all earlier years, then evaluated on the *most recent, unseen holdout year* using weighted absolute percentage error (WAPE). The UI reports raw and adjusted heldout WAPE, even if adjustment makes things worse. This method does **not** correct orbit times, clouds, sensor fields-of-view, observation gaps, differing false positives, or pixel physics. It is a baseline research diagnostic—not a validated harmonization solution or a VIIRS-equivalent fire history extending back to 2000.

A robust future project should train on many years, compare multiple candidate models, do leave-one-year-out validation and chronological holdout, characterize outages and coverage, and report calibrated intervals. Do not fill in unavailable earlier years.

## Canadian agency reality check

Official Government of Alberta incident records are distinct from satellite thermal detections. If imported from the government's licensed CSV, the application can look for agency fire origin grid-days coinciding with satellite thermal grid-days within ±3 calendar days and an approximately 20-km projected-centre search distance. Coincidence **does not prove same wildfire**; no nearby detection is **not a false negative** due to unknown effective satellite coverage. The agency dataset is not shipped in the ZIP because the external CSV download could not be completed in this environment.

## Time and space precision

- `acq_date` groups by UTC date, not local day or ignition time.
- 10-km map coordinates do not imply universally equal surface area.
- No cloud mask or overpass weighting is built into this prototype.
- Species of fire (agricultural vs wildland) is not resolved by type-0 alone.
- Historical imagery tiles are **not** imaging from the dates on the calendar.
- NASA real-time FIRMS feed checks are *hotspot observations*, not official incident alerts or forecasts.
- The current live feed is optional and needs a FIRMS API key; it cannot predict ignitions.

## Official documentation

NASA FIRMS VIIRS types and semantics: https://firms.modaps.eosdis.nasa.gov/content/descriptions/FIRMS_VIIRS_Firehotspots.html

NASA FIRMS MODIS data descriptions: https://firms.modaps.eosdis.nasa.gov/descriptions/FIRMS_MODIS_Firehotspots.html

NASA FIRMS Fire Alerts notes: https://firms.modaps.eosdis.nasa.gov/alerts/notes.php

Official Alberta incident history: https://open.canada.ca/data/en/dataset/a221e7a0-4f46-4be7-9c5a-e29de9a3447e

CWFIS: https://cwfis.cfs.nrcan.gc.ca/en/

> **Global edition methodology change (Nov 2026):** These counts were recomputed under the unified global Equal Earth EPSG:8857 10-km grid; legacy Canada EPSG:3978 counts are NOT directly comparable. Source observation counts remain unchanged.
