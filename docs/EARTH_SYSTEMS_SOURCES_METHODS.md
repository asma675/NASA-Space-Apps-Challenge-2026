# BLINDSPOT Earth Systems — sources, layering, limitations

New edition: five **separate** maps, preserving all the original World 2025–26 and Alberta 2023 FIRMS analysis and Observatory features. **No new global wildfire observations** have been imported into the underlying FIRMS archive by adding these environmental contextual layers.

| Workspace | Source / service | Implemented, live behavior | Limitations |
|---|---|---|---|
| `/vegetation` | [NASA GIBS](https://gibs.earthdata.nasa.gov/); `MODIS_Terra_NDVI_8Day`, `MODIS_Terra_CorrectedReflectance_TrueColor` via public EPSG:3857 WMS | Real NASA time-selectable satellite raster imagery over geographic basemap | NDVI means greenness / photosynthetic activity, **not** a quantitative vegetation-health diagnosis, fuel moisture estimate or fire-risk prediction; product dates may be unavailable. We do not sample NDVI values into numeric risk scores. |
| `/air-quality` | [Open-Meteo Air Quality API](https://open-meteo.com/en/docs/air-quality-api), Copernicus Atmospheric Monitoring Service (CAMS); optional `MODIS_Terra_Aerosol` NASA GIBS WMS | Actual model forecasts for PM2.5/PM10/US AQI at selected point + **3×3 independently modeled sample locations**, and a five-day forecast strip | Model estimates, **not** ground monitor measurements. 9 point circles **are not a continuous pollutant raster**. Wildfire origin of particulate pollution unconfirmed. Aerosol optical depth **is not** surface PM2.5. |
| `/navigation` | [OpenStreetMap](https://www.openstreetmap.org/) raster basemap; [OSRM](https://project-osrm.org/) demo routing API; NASA GIBS optional aerosol WMS | Click first and second map points and request ordinary driving route geometry, distance and nominal time | **Not a safe evacuation route**, does not account for closures, incident boundaries, fires, smoke or current traffic. Public OSRM demo has usage and availability limits and is inappropriate for production. Consult official transport authorities. |
| `/forecast` | [Open-Meteo Forecast API](https://open-meteo.com/en/docs) 7-day daily temperature, RH, wind, gusts, precipitation | **Transparent illustration only**: descriptive 0–100 weather *monitoring attention* index with baseline and hypothetical hotter/drier/windier perturbations | **NOT a calibrated wildfire ignition forecast or fire risk probability.** No fuel moisture, land-cover numeric data, causal ignition, exposure model, skill assessment or validation against fire occurrence. |
| `/cascades` | Open-Meteo weather + CAMS air model, OSM, user-selected sector | Links live model conditions to hypothetical *concern pathways* for communities, mobility, infrastructure and ecosystems with explicit verification steps | **No predictions of outages, displaced persons, road closures, health outcomes, smoke plume transport, fire spread or economic damages.** Marker locations are sampled weather/air points, not impact boundaries. |

## Index calculation (forecast page only)

```
component                         points
max(0,min(1,(55-RH%)/40))*35       0–35
max(0,min(1,(wind_kmh-15)/40))*30  0–30
max(0,min(1,(temp_C-18)/22))*20    0–20
(1-max(0,min(1,rain_mm/7)))*15     0–15
TOTAL                              0–100
```

The inputs are daily maximum 2m air temperature, daily minimum 2m relative humidity, daily maximum 10m wind speed and daily precipitation total from weather **forecast models**, at a single point (UTC). The resulting **index is an illustrative heuristic only**, not an operational fire-weather rating, a quantified probability or a trained predictive model. It was neither fitted to nor validated against a fire-outcome dataset. Values merely help a user compare how the same *chosen formula* reacts when assumptions are changed. Scenario perturbations change temperature +4 °C and minimum RH −15 percentage points (floor 0), or wind +15 km/h respectively; these are **not** external weather forecasts. The bar chart shows index by future day, the headline the maximum across seven days. Bands (lower under 35, watch under 65, elevated otherwise) are **internal descriptive thresholds with no physical wildfire probability interpretation**.

## About future risk / cascading effects

A forecast of meteorological conditions is not a fire ignition forecast. Future ignition likelihood, spread, suppression constraints, smoke plume movement, and confirmed damage require dedicated input datasets, model calibration, validation, independent verification and possibly licensed official government data. This prototype provides a **scenario analysis of environmental attention and potential planning questions** rather than a hazard-prediction system. Do not rely on it for any public safety decisions.

## Data provider requirements

- Open-Meteo endpoints are requested **at runtime** by the FastAPI backend; a working internet connection is required. The app never replaces unavailable forecasts with simulated numbers. API parameters are checked; brief in-memory caching limits repeated provider calls.
- NASA GIBS WMS imagery is loaded directly by the Leaflet client; product/day availability varies and an unavailable tile may show transparency or an error. No hidden MapTiler or CARTO key is required. `epsg3857` WMS works on the map's Web Mercator projection.
- OpenStreetMap standard raster tiles require internet connectivity and compliance with the OSM tile-use policy. Esri provides the optional satellite basemap, subject to its usage terms.
- Public OSRM routing is demonstration-only. For any sustained deployment, host your own OSRM or use a properly licensed and maintained directions service. **Do not build an evacuation application on the demo server.**
- Time ranges are distinct: the original local NASA FIRMS index (2025–26 World + 2023 Alberta) is historical; NASA vegetation imagery is selected by imagery date; Open-Meteo supplies **current forecast** outputs. **Do not overlay these time periods as if simultaneous.**

## More authoritative hazard/health resources (external links only)

- [NASA GIBS API access documentation](https://nasa-gibs.github.io/gibs-api-docs/access-basics/)
- [EPA AirNow Fire & Smoke Map](https://www.airnow.gov/fire-and-smoke-map/) (US, monitored and modeled air context)
- [Environment and Climate Change Canada FireWork smoke](https://weather.gc.ca/firework/) (Canadian smoke dispersion; source not ingested in this edition)
- [Natural Resources Canada CWFIS](https://cwfis.cfs.nrcan.gc.ca/en/catalogue) (independent wildfire information; old Explore page has optional context)
- [OSRM demo usage policy](https://github.com/Project-OSRM/osrm-backend/wiki/Demo-server)

## AI assistance disclosure

The Earth Systems application modules, styling, backend service wrappers, tests, descriptions and documentation were prepared with OpenAI ChatGPT assistance and should be attributed as AI-assisted source code. The text, icons and CSS illustrations in these modules are original within this edition and are **not** NASA artwork or NASA branding. Numeric NASA hotspot data and remote model data are provided by their respective publishers, not fabricated by the AI. The application is designed and directed by Parallax Labs, Asma Ahmed and Ayaan Ahmed.
