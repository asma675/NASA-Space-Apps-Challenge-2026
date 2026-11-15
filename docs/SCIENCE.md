# Scientific method and limitations

## Input

FIRMS active fire hotspot detection records, separated into satellite product names and observation family MODIS vs VIIRS. Input includes acquisition date (UTC), latitude/longitude, optional confidence, FRP, and product. NASA archival science-quality files are preferable for historical analysis.

## Harmonization in this MVP

1. Preserve product/provenance. Validate input coordinates and ISO dates.
2. Transform lat/lon (EPSG:4326) to global Equal Earth (EPSG:8857) via `pyproj`. The projected 10-km cells are used consistently across Canadian and World views; this differs from the earlier Canadian projection and its previous counts.
3. Divide projected x/y coordinates into fixed 10,000-m cells.
4. Make `(UTC day, projected cell, family)` a unique activity record, counting one regardless of duplicate detections.
5. Construct union across both families; mark *matched* if the same cell-day has a MODIS AND a VIIRS detection, *exclusive* otherwise.
6. Summarize union active grid-days by month and show seasonal average per selected year (including months without detections).

## Correct interpretation

- A "matched cell-day" is **NOT necessarily one fire seen by both satellites**. Satellites may pass at different times, and different fires may be present in a 10-km cell.
- A "VIIRS-only cell-day" is **NOT a confirmed fire missed by MODIS**. Overpass, clouds, burn timing, sensitivity and coverage matter.
- A union grid-day index **is NOT scientifically calibrated across sensors**. Raw observational alignment is a reproducible baseline but does not fully harmonize different detection sensitivities.
- The "sensor agreement" fraction is a **recorded spatial/temporal co-detection rate**, not truth, accuracy, recall or ground validation.
- A month showing zero records could mean zero detected hotspots, no data uploaded, or no observation coverage. We have no coverage denominator in the MVP.
- Standard-processed products and NRT products may have different availability windows; avoid comparing them as if equivalent without qualifications.
- Historical satellite-detected active fire is NOT equivalent to burned area products, unique incident counts or early warning probabilities.

## Next science upgrade to compete strongly

**Overpass-aware calibration and validation:** For overlapping multi-year science-quality records, compute per-sensor availability / valid observation coverage (cloud/swatch/time), apply defensible relative observation adjustments, evaluate held-out seasons, and compare with Canadian agency incidents or burned-area products. Publish a before/after error table with uncertainty. This is a research extension, not currently implemented.

**Ground context:** Natural Resources Canada's CWFIS / CNFDB and provincial historical data provide agency-recorded incidents and perimeters, subject to completeness and licensing. They should be used for external validation with matching dates/locations, not naïvely merged into satellite detection counts.
