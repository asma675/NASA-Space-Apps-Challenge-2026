# Product Brief — Parallax BLINDSPOT

**Product promise:** Understand the historical burning record before making seasonal monitoring decisions.

## Define one customer, one problem, one decision

| | |
|---|---|
| Primary stakeholder | Seasonal wildfire preparedness analyst in a provincial wildfire service or regional land management organization |
| Secondary | Remote sensing scientists, environmental researchers and educational audiences |
| Existing pain | Multiple generations of satellite hotspot data have different sensitivity, resolution, observations and temporal coverage. A raw year-on-year chart may confound sampling changes with actual burning patterns. |
| The job to be done | "Before the season, show me which months and areas were historically active, explain where the records differ, and give me an evidence package to review with my team." |
| Outcome | Historical activity calendar + sensor-comparison map + concise exportable briefing |
| Explicit exclusions | No real-time alerts, evacuation/dispatch guidance, wildfire occurrence forecasts, false claims that satellite hotspots equal fires |

## The product loop

1. A seasonal planner chooses a region and a time interval with actual observations.
2. The platform joins fire hotspot observations onto common projected grid-days and removes repeated within-cell, within-family detections.
3. The planner reviews a month-by-year historical detection calendar and identifies candidate historically active periods.
4. **Satellite X-Ray** reveals MODIS-only, VIIRS-only and overlapping grid-days, with provenance and limitations.
5. The planner exports a **Readiness Brief** to support an expert discussion of monitoring schedules, always checking official forecasts and local agency data.

## The wow factor (not a scientific overclaim)

Open with a question: **"When apparent fire detections rise, do we know if burning increased — or did the satellites observe differently?"**

In one click, change from blended dots to separate sensor perspectives. The scientific X-Ray is immediate and interactive, yet transparently says that sensor-exclusive records do not establish missed fires. Follow with one detailed month and the exportable agency-style briefing.

## One-sentence differentiator

**Not another fire-alert map: BLINDSPOT reveals how sensor differences affect interpretation of historical fire activity, then turns that evidence into a seasonal planning conversation.**

## Measurable acceptance criteria

- A user can select a region and a valid month/year range, and the calendar updates without hardcoded counts.
- Each displayed summary is computed from records in the active data mode; synthetic and real records never mix.
- The same location/date seen by two sensors appears as one **combined grid-day** with a **matched** marker, not two separate fires.
- A user can inspect the original sensor/time provenance for displayed points.
- The app differentiates missing observations from confirmed no-fire days.
- A user can download evidence and scientific limitations in one action.
- Keyboard-accessible, responsive, light/dark interface; API returns informative validation errors.

## NASA Space Apps demo pitch

"We're Parallax Labs. A wildfire planner needs to know *when* to monitor—not just see today's hotspots. But NASA's MODIS and VIIRS satellites don't observe fire in identical ways. BLINDSPOT is a fire-history investigator: we align observations onto common grid-days, reveal where sensors agree and disagree, and build an interactive seasonal calendar and transparent readiness brief. We don't claim to predict fires or magically eliminate sensor bias. We make the record's useful signals and limitations visible so people can make better-informed seasonal decisions."
