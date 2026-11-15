# Investigation Edition — feature changelog

## Added

- Full-width original **Satellite Blindspot Reveal** interface with two synchronized Leaflet satellite maps and an accessible draggable divider.
- **Reveal Blindspots** mode maps dominant grid-day relationships: MODIS-exclusive, VIIRS-exclusive and both-sensor activity.
- Month selector wired to the existing **Fire Time Travel** calendar, plus month-specific server-side totals.
- **Custom focus area:** draw a rectangular bounding box with two map clicks; region bounds validated server-side. The original calendar, map counts, evidence analysis, and readiness export filter to that area.
- **Data-quality filtering:** NASA type 0 presumed vegetation observations included by default; types 1, 2 and 3 excluded from analysis but preserved in original ZIPs and SQLite. Source counts displayed.
- **NO DATA vs zero:** imported source coverage windows required for complete monthly status; the calendar labels missing observations as unverified rather than measured zero.
- **Fire Season Detective:** descriptive leave-one-year-out median and reference quartiles only after ≥3 other fully covered instances of the calendar month.
- **Calibration Audit:** experimental earlier-years MODIS→VIIRS active-grid-day scale and unseen-year WAPE score, only when ≥3 independent years have ≥3 common fully covered months.
- **Canadian agency cross-check:** if independently imported Alberta history exists, spatial/date co-occurrence of agency fire origins with NASA grid-days (±3 days, ~20 km) can be audited.
- **Mission Brief:** provenance, exclusions, observation disagreement, anomaly availability, calibration availability and recommended analyst next checks.
- **Streaming server analysis:** no 1-million-row cap; cached aggregate results.
- **Multiple-year importer:** original NASA ZIPs, duplicate safe, optional NASA-request date coverage manifest.
- Tests for vegetation exclusion, custom AOI filtering, anomalies, holdout calibration and source-coverage caveats.

## Preserved

- Embedded 2023 Alberta MODIS + VIIRS raw historical archives and source SQLite (complete ZIP only).
- Existing NASA Satellite X-Ray map, Fire Time Travel, Fire DNA, Watchtower, optional CWFIS layers and Canada Evidence Lab.
- Moving 3D globe / CSS fallback, Wildfire Watch satellite imagery and controls, light/dark theme.

## Not claimed

- A validated 25-year harmonized historical series; only Alberta May–Oct 2023 is embedded.
- Cross-year anomaly or calibration scores without real additional years.
- Fire ignition predictions, detection false-negative rates, confirmed agency wildfire events inferred from NASA hotspots, or live agency reporting delays.
- Full feature/code transfer from Zij. All Investigation Theatre source is independently authored.
