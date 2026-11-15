# Canada evidence sources — status, definitions and responsible use

This file records the sources and the **current implementation status**. Do not describe a source as analyzed simply because it appears as a link.

| Source | Definition | Data status in this release | How it is used | Source |
| --- | --- | --- | --- | --- |
| NASA FIRMS MODIS C6.1 standard archive (#849825) | Historical active-fire thermal anomaly detections | **Preloaded:** 90,039 Alberta observations, 2023-05-01 to 2023-10-31 | Common 10-km projected grid / UTC day calendar | https://firms.modaps.eosdis.nasa.gov/ |
| NASA FIRMS S-NPP VIIRS C2 standard archive (#849826) | Historical active-fire thermal anomaly detections | **Preloaded:** 456,982 Alberta observations, same window | Compare common grid-days; not a detection-calibration model | https://firms.modaps.eosdis.nasa.gov/ |
| Government of Alberta fire history 2006–2025 | Agency wildfire incident records, fire origins, final size, cause and discovery/report fields | **Importer implemented; records NOT preloaded** | Independently sourced monthly incidents, map overlay and timing where valid | https://open.canada.ca/data/en/dataset/a221e7a0-4f46-4be7-9c5a-e29de9a3447e |
| CWFIS/CWFIF current agency active fires | Agency-reported active-fire WMS | **Opt-in network overlay**, not locally archived or verified here | Separate operational map context, **not** 2023 evidence | https://cwfis.cfs.nrcan.gc.ca/en/ |
| CWFIS Fire Weather Index | Current fire-weather WMS | **Opt-in network overlay**, not locally archived or verified here | Current conditions only, **not** 2023 wildfire prediction | https://cwfis.cfs.nrcan.gc.ca/en/catalogue |
| National Burned Area Composite (NBAC) | Annually mapped burned-area footprint polygons | **Source documented only**, NOT integrated into analysis | Proposed further validation and spatial interpretation | https://cwfis.cfs.nrcan.gc.ca/downloads/nbac/ |

## Critical distinctions

**Do not equate** official incident counts, individual hotspot observations, 10-km active grid-days, burned hectares, or current fire weather. All have different units and coverage.

NASA MODIS/VIIRS both observing a hotspot within a grid-day is **co-occurrence**, not evidence of the same ignition, exact detection, or fully calibrated sensor harmonization. A satellite-only detection does **not** establish that the other sensor missed a fire; orbit time, cloud cover, sensor sensitivity and other coverage differ.

**Agency report timing** uses discovered_date → reported_date where documented and valid. This is not actual ignition → satellite acquisition, satellite acquisition → NASA product publication, or any website posting interval. Timezone is not invented; the source's local timestamp is retained and should be interpreted with agency metadata.

The Government of Alberta historical incident register generally covers the designated Forest Protection Area. Other wildfire datasets may include mutual-aid or cross-jurisdiction events. The agency import includes the full **calendar year**, while the NASA default selection is May–October 2023; therefore **do not compare totals as like-for-like**. The UI explicitly labels the agency year.

## Recommended additions after the core challenge MVP

1. Obtain and ingest NBAC 2023 polygons, inspect geometry and licence, and examine spatial overlap without declaring them point-level satellite truth labels.
2. Expand the FIRMS historical archive beyond one year and implement climatological baselines, seasonal anomaly diagnostics, MODIS/VIIRS overlap by month, and measurement uncertainty across sensor changes.
3. Add observation opportunities / cloud cover / overpass geometry to estimate actual inter-sensor comparability. Without these, avoid claiming sensor detection bias calibration.
4. Only with weather, fuels, official fire history and prospective validation: attempt a genuine fire danger or ignition-probability forecasting model. Keep warnings on predictions and false-positive costs visible.

## Data licences / attribution

NASA FIRMS and Natural Resources Canada CWFIS resources have their own attribution and service conditions. Alberta fire history is distributed under the Open Government Licence — Alberta. Check each publisher's terms and current metadata before public redistribution. BLINDSPOT locally stores original NASA archives, but does not bundle third-party Alberta records until separately downloaded by the user.
