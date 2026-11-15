# BLINDSPOT map watermark fix (November 2026)

The diagonal **API KEY REQUIRED** watermarks were coming from CARTO basemap and reference-label tiles, **not NASA FIRMS**. CARTO changed its tile service to require an API key.

**Fixed:** Satellite X-Ray now uses OpenStreetMap (Street / Night) without a key, or Esri satellite imagery. Satellite Blindspot Reveal uses Esri imagery with an Esri reference-label overlay (it auto-removes labels if unavailable). MapTiler's premium styles remain optional. NASA observations and the entire 2023 Alberta SQLite database are unchanged.

## Run

```powershell
cd "C:\Users\asmaa\Downloads\Parallax_BLINDSPOT_Global_Edition"
py -m pip install -r backend/requirements.txt
py -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8765 --reload
```

Stop any older BLINDSPOT server on port 8765 first, then press **Ctrl+Shift+R** in the browser. Select **BASEMAP > Auto** for a no-key dark street map, or **Wildfire Watch** for Esri satellite imagery.

Open `http://127.0.0.1:8765/api/config` and confirm NASA real mode data remains present.

**Provider policies:** OSM map tiles are for normal interactive viewing, not bulk downloads; use an appropriate commercial or self-hosted provider if scaling the app. Esri geographic tiles are subject to Esri licensing and availability.
