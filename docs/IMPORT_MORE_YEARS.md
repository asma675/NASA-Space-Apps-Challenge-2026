# Add real overlapping years — do not fabricate a baseline

The complete BLINDSPOT ZIP already includes May–October 2023 Alberta MODIS C6.1 and S-NPP VIIRS C2. More years require *real NASA archive files for the same selected area*, preferably both sensor products and comparable month windows. A FIRMS MAP_KEY is **not required to import downloaded historical ZIP files**.

## Import additional archives

Place your own ZIP files in `data/raw/other/`. Do not unzip them. From the app root run:

```powershell
py scripts/import_multi_year.py --modis "data/raw/other/MODIS_2020.zip" "data/raw/other/MODIS_2021.zip" --viirs "data/raw/other/VIIRS_2020.zip" "data/raw/other/VIIRS_2021.zip"
```

Replace these **example** filenames with your actual downloaded NASA archive names. The script reads the CSV inside each ZIP, preserves original dates and products, uses stable record IDs to avoid reimports, and conservatively records source coverage from the earliest/latest observation. It accepts multiple paths per sensor.

If NASA explicitly documents the full downloaded archive request intervals, create `data/raw/other/coverage.json`:

```json
[
  {"file":"MODIS_2020.zip","product":"MODIS_SP","start":"2020-05-01","end":"2020-10-31"},
  {"file":"VIIRS_2020.zip","product":"VIIRS_SNPP_SP","start":"2020-05-01","end":"2020-10-31"}
]
```

Use real request windows, **never guessed dates**. Then run `py scripts/import_multi_year.py --manifest "data/raw/other/coverage.json" --modis "data/raw/other/MODIS_2020.zip" --viirs "data/raw/other/VIIRS_2020.zip"`.

**Why coverage matters:** A month with zero detections cannot be counted as truly zero observed burning unless the source archive's product coverage is documented. Otherwise BLINDSPOT marks **NO DATA**.

## What unlocks

- At least **four** fully covered instances of a given calendar month (selected + three independent other years): descriptive anomaly median and P25–P75 reference band.
- At least **three** independent overlapping sensor years with at least three shared fully covered months: an **experimental** earlier-years MODIS-to-VIIRS scaling with the latest year strictly held out. This is a diagnostic, *not* validated sensor harmonization.
- More actual years also grow the interactive calendar and Fire DNA seasonal signature.

## Performance and persistence

`/api/analysis` streams filtered observations and does **not silently cap at 1 million rows**. Caching avoids recomputing identical aggregate queries until the database changes. The full raw database stays excluded from Git by `.gitignore`.

After importing new years, restart the server and refresh the page to discard old in-memory history caches.
