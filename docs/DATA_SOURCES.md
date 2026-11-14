# Data provenance and APIs

| Source | Primary purpose | Credentials | Integrated in MVP? |
|---|---|---|---|
| NASA FIRMS Area API | MODIS/VIIRS hotspot date/location observations | Free FIRMS MAP_KEY | Yes; backend ingests valid products |
| NASA FIRMS Archive Download | Multi-year science-quality observations as CSV | Free NASA FIRMS account / archive request | Yes; via user CSV upload after download |
| Natural Resources Canada CWFIS | Historical agency fire history and external evaluation | May have dataset-specific terms | **Reference link only**, not API connected |
| Government of Alberta historic wildfires CSV (2006–2025) | Provincial wildfire reports; external validation candidate | Government of Alberta open data licence | **Reference link only**, not yet mapped to satellite data |
| City of Brampton GeoHub | General municipal GIS context | Public portals | Not used — irrelevant to this specific NASA challenge |

## Required API key

Request free key: https://firms.modaps.eosdis.nasa.gov/api/map_key/

Set `FIRMS_MAP_KEY` on the backend server. API endpoint pattern is:

`https://firms.modaps.eosdis.nasa.gov/api/area/csv/<MAP_KEY>/<SOURCE>/<west,south,east,north>/<1-5>/<YYYY-MM-DD>`

The backend supports products such as `MODIS_SP`, `MODIS_NRT`, `VIIRS_SNPP_SP`, `VIIRS_SNPP_NRT`, `VIIRS_NOAA20_SP`, and chunks dates into <=5 days. Standard-processing availability can lag recent dates. The API requires selecting the right product for the historical date. Check https://firms.modaps.eosdis.nasa.gov/api/data_availability/.

**Historical archive note:** NASA's Archive Download may be processed after a request and deliver a link by email; it is not a simple anonymous 20-year one-click public REST endpoint. Select only the desired region to control file size.

**Canadian science**: CWFIS notes that satellite hotspot products are not official area burned estimates. Use agency-reported data for historical context and validation. See https://cwfis.cfs.nrcan.gc.ca/en/faq and https://cwfis.cfs.nrcan.gc.ca/en/fire-history.

## License and attribution

Use official attribution and comply with each source's terms. No NASA logo is bundled. BLINDSPOT is an independent team project and is not endorsed by NASA or Canadian agencies. The map uses OpenStreetMap tiles with attribution when internet access is available.

## Geographic basemap implementation

- **MapTiler Cloud vector basemap:** Optional public API key; used only for geographical background (Dataviz Dark, Dataviz Light, Satellite, Satellite Hybrid). MapTiler data does not replace NASA active-fire observations. https://docs.maptiler.com/leaflet/examples/vector-tiles-in-leaflet-js/
- **CARTO + OpenStreetMap basemap:** No-key fallback. Attribution shown inside the map. https://carto.com/attributions
- Satellite imagery is generally a multi-date mosaic, **not** satellite fire observation imagery for the selected historical day.
- Web map tiles and SDK require internet access.
