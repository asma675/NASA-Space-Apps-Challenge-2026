# BLINDSPOT: NASA FIRMS World datasets (November 2025–November 2026)

## Official NASA archive ZIPs supplied by the project team

| NASA request | Source | ZIP | Member | Dates | Raw observations | Included in grid index | NASA type excluded |
|---|---|---|---|---|---:|---:|---:|
| 850371 | MODIS C6.1 | `DL_FIRE_M-C61_850371.zip` | `fire_archive_M-C61_850371.csv` | 2025-11-12–2026-08-31 | 2,636,501 | 2,476,735 | 159,766 |
| 850371 | MODIS C6.1 NRT | same | `fire_nrt_M-C61_850371.csv` | 2026-09-01–2026-11-13 | 794,182 | 794,182 * | n/a |
| 850372 | VIIRS S-NPP C2 | `DL_FIRE_SV-C2_850372.zip` | `fire_archive_SV-C2_850372.csv` | 2025-11-12–2026-07-31 | 10,626,682 | 9,700,763 | 925,919 |
| 850372 | VIIRS S-NPP C2 NRT | same | `fire_nrt_SV-C2_850372.csv` | 2026-08-01–2026-11-02 | 6,602,259 | 6,602,259 * | n/a |

**Total raw World download records:** 20,659,624. **Eligible for analysis under the stated rules:** 19,573,939. **NASA non-vegetation source-type records excluded (SP only):** 1,085,685. **Unique 10-km Equal Earth projected UTC-day grid cells across World data:** 5,708,602. These figures are verified after reading the CSV members—not fire incident counts.

`*` **NRT provisional warning:** Neither NRT CSV member contains NASA's `type` field. These rows are *unclassified*, included in a **provisional** observation comparison. We cannot assert that every NRT row is a vegetation fire or that it will survive standard reprocessing.

## Separate legacy historical case study

The complete ZIP also includes the **Alberta, Canada, May–October 2023** original NASA archive data: 547,021 raw observations in `data/blindspot.sqlite3`, with MODIS and VIIRS stored individually. The original 2023 ZIPs are retained in `data/raw/`. A 2023 Alberta map does **not** establish worldwide archive coverage for 2023.

## Data storage and reproducibility

- `data/raw/DL_FIRE_M-C61_850371.zip` and `data/raw/DL_FIRE_SV-C2_850372.zip`: **all original global detections**, including their individual latitude, longitude, acquisition date/time, confidence, FRP, and source fields.
- `data/global_grid.sqlite3`: **an exact materialized aggregation for interactive analysis**. Each database row corresponds to one 10-km global Equal Earth (EPSG:8857) cell and one UTC day, with four counts: MODIS SP, MODIS NRT, S-NPP VIIRS SP, S-NPP VIIRS NRT. It does **not** contain every original full-resolution detection row or claim exact ignition locations. The map point is the first source observation within a cell, used only for visualization; the grid/day is the comparison unit.
- `data/global_archive_manifest.json`: auditable source members, dates, raw totals, eligible counts, excluded counts, and processing notes.
- `data/blindspot.sqlite3`: full-resolution 2023 Alberta archive and synthetic demo records, separated by `mode`.

Rebuild the global index (no API key or manual extraction required):

```powershell
py scripts/build_world_grid.py --modis "data/raw/DL_FIRE_M-C61_850371.zip" --viirs "data/raw/DL_FIRE_SV-C2_850372.zip"
```

The importer can be rerun; it tracks processed days per archive member, so a second run won't double-count. The importer does not silently import the two ZIPs' `archive` and `nrt` members as the same product.

## How to demo the World data

1. Run the FastAPI server and open `/explore`.
2. Choose **World · June 2026**, which uses standard-processing observations from both sensors. Click **Analyze region** if needed.
3. Drag **Satellite Blindspot Reveal** to compare MODIS versus VIIRS, then click **Reveal Blindspots**.
4. Change the region to **Amazon**, **Australia** or **Southern Africa** to explore the same month in another geography.
5. Choose **September 2026** to see a newer global provisional NRT period. The UI marks it as **provisional**. NRT does not require an API key once its original downloaded ZIP is bundled.
6. Click **Alberta 2023 case study** to return to the earlier full-resolution dataset and Canada's agency-data comparison area.

## Important limitations for NASA Space Apps

1. **Not a 20-year global archive:** This new World request covers roughly one year. Long-term climatology or validated anomaly detection cannot be computed from this alone. The separate 2023 Alberta case study is not global coverage.
2. **Not a validated sensor calibration:** BLINDSPOT aligns 10-km cell/day sensor presence; it does not correct orbital overpasses, cloud cover or different MODIS/VIIRS detection probabilities.
3. **Not an emergency warning:** NASA hotspots are satellite thermal anomalies, not confirmed individual wildfires, ignition times, evacuation alerts or probabilities of fires occurring tomorrow.
4. **No misleading zeros:** A month with no demonstrated archive coverage is marked unverified, not treated as fire-free.
5. **Scope of provenance:** These archives are user-supplied NASA FIRMS ZIPs. The app has verified their member schemas and processed source counts, not independently validated every detection against official incident records.

Reference: NASA FIRMS archive downloads https://firms.modaps.eosdis.nasa.gov/download/.
