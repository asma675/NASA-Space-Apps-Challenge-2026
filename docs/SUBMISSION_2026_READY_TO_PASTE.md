> **NEW WORLD DATA EDITION:** The previous text below focuses on the earlier Alberta-only case study. For accurate November 2025–November 2026 worldwide data numbers, dates and science limitations, use [GLOBAL_JUDGE_PITCH.md](GLOBAL_JUDGE_PITCH.md) and [WORLD_DATA_2025_2026.md](WORLD_DATA_2025_2026.md).

---

# NASA Space Apps Challenge 2026 — Submission copy for Parallax BLINDSPOT

**Verify all links and team details before submitting.** These are edited drafts, not an actual Space Apps submission. All online judges must be able to open links without login. Team members' names have intentionally not been invented.

## Project name
**Parallax BLINDSPOT — One Planet. Two Satellite Stories.**

**Team:** Parallax Labs — [INSERT ALL REGISTERED TEAM MEMBERS]

**Challenge:** Harmonization of MODIS and VIIRS Hot Spots

## High-level project summary

NASA's MODIS and VIIRS satellites have tracked thermal hotspots for decades, yet their observations cannot be directly compared because their sensors differ in sensitivity, footprint and observation timing. Parallax BLINDSPOT is an interactive satellite fire-history investigator that exposes these differences and helps wildfire preparedness analysts turn incomplete evidence into clearer planning questions. Its signature Satellite Blindspot Reveal compares MODIS and VIIRS side by side, then displays shared and sensor-exclusive 10-km grid-day activity on a historical burning calendar. The shipped Alberta 2023 demonstration processes 547,021 authentic NASA FIRMS observations, separately flags 4,246 nonvegetation thermal-source records, and provides evidence-backed seasonal briefing outputs. A World Atlas supports global geographic exploration and optional recent NASA FIRMS observations when a key is configured; worldwide historical coverage is **not** claimed. BLINDSPOT makes gaps and uncertainty visible rather than presenting missing satellite detections as proof that no fire occurred.

## Problem and intended audience

**Maya**, a wildfire seasonal-preparedness analyst, has two NASA datasets showing different counts for the same region and time. She needs to identify historically busy monitoring periods, know where sensor reports disagree, and provide an explainable evidence brief to her team. Raw pixel counts and ordinary fire maps are not enough: VIIRS and MODIS detect different numbers of hotspots, and a satellite hotspot is not necessarily a validated incident. The application is intended for land managers, scientists, monitoring planners and emergency-preparedness analysts—not active dispatch or evacuation decisions.

## Detailed project description

BLINDSPOT is a FastAPI/Python and SQLite application with an HTML/CSS/JavaScript frontend and Leaflet geographic maps. A lightweight 3D Earth view opens the story. The primary research feature is **Satellite Blindspot Reveal**: two synchronized MODIS and VIIRS satellite maps with a draggable split and a Reveal button that classifies common 10-km Equal Earth (EPSG:8857) × UTC-day cells as MODIS-only, VIIRS-only, or seen by both sensor families. These classes represent *observation co-occurrence*, not accuracy or false-negative rates. The activity calendar, selected-month map, seasonal fingerprint, and custom bounding-box investigation all use the same underlying grid-day analysis, not sampled marker totals. A mission brief exports findings, provenance, and limitations.

The baseline demo includes **547,021 original NASA observations** for Alberta, Canada (May–October 2023): MODIS C6.1 `MODIS_SP` and Suomi NPP VIIRS C2 `VIIRS_SNPP_SP`. For the current presumed-vegetation filter, **542,775** observations contribute to analysis, while **4,246** type-1/2/3 thermal-source records are excluded and separately reported. Under the revised global Equal Earth grid, these yield **17,094** active grid-days, of which **9,268** have both sensor families, **1,084** are MODIS-only and **6,742** are VIIRS-only (**54.2%** co-observation; not sensor accuracy). The science-quality archive is **one regional season**, so the interface does not claim a valid worldwide or multi-year anomaly baseline and does not invent a calibrated MODIS-to-VIIRS conversion.

The World Atlas supports Earth-scale navigation and select regional windows (Amazon Basin, Australia, the Mediterranean, southern Africa, Southeast Asia, western U.S., and Canada), with optional **near-real-time** NASA source selection. A private FIRMS key enables a world-area recent `VIIRS_SNPP_NRT` / other VIIRS / MODIS feed. This separate feed is not mixed into the 2023 calendar and is not a confirmed incident or predictive fire warning. Future country archives can be imported with explicit dates and geographic coverage. The Canada Evidence Lab provides an independent official Alberta incident CSV importer and opt-in NRCan CWFIS current layers, with clear distinctions between thermal detections, agency fires and fire weather. The government CSV is **not included** in the shipped demo.

BLINDSPOT's aim is to convert fragmented satellite observation histories into a more transparent calendar and questions a human planner can act on: *Which months were busiest, which geographic cells had sensor disagreement, where must we check coverage, and which independent agency records could verify our interpretation?*

## Link to project demo

**Add a public, tested URL** for ONE official demo format: a video no longer than 30 seconds, OR `docs/Parallax_BLINDSPOT_Submission_7_Slides.pptx` / PDF version with seven slides maximum. Recommended: seven-slide presentation for formal judging, plus the 30-second video as a supplemental link. [INSERT DEMO URL]

## Link to final project

Public source repository: https://github.com/asma675/NASA-Space-Apps-Challenge-2026

**Important:** ensure the global edition code has actually been pushed to GitHub; the connected repository may still show an older build. Link a live, no-login hosted build if deployed: [INSERT PUBLIC APP URL IF AVAILABLE]. The GitHub code-only ZIP deliberately excludes a >200MB private SQLite database. If relying on GitHub alone, create a public no-login archive artifact or a reproducible data-download/import pathway for judges.

## NASA data used

NASA FIRMS: MODIS Collection 6.1 standard-processing active-fire hotspot archive, request #849825, and VIIRS Suomi-NPP Collection 2 standard-processing active-fire hotspot archive, request #849826, Alberta 2023-05-01–2023-10-31. NASA FIRMS Area API supports recent NRT queries (optional FIRMS_MAP_KEY). Source: https://firms.modaps.eosdis.nasa.gov/ ; https://firms.modaps.eosdis.nasa.gov/download/ ; https://firms.modaps.eosdis.nasa.gov/api/area/ .

## Space agency partner data and other sources

- Government of Canada, Natural Resources Canada Canadian Wildland Fire Information System (CWFIS): optional present-day active-fire and Fire Weather Index layers, NOT 2023 historical observation context. https://cwfis.cfs.nrcan.gc.ca/
- Government of Alberta official historical wildfire records: a separate CSV import pathway, not loaded in the shipped application. https://open.canada.ca/data/en/dataset/a221e7a0-4f46-4be7-9c5a-e29de9a3447e
- European Commission JRC Global Wildfire Information System (GWIS): external global active-fire / fire-danger / historical burned-area references, not embedded as satellite observations. https://gwis.jrc.ec.europa.eu/applications
- Natural Resources Canada National Burned Area Composite: reference only, no integrated polygon analysis. https://cwfis.cfs.nrcan.gc.ca/downloads/nbac/
- Mapping/display tools: Leaflet, Esri World Imagery geographic basemap, OpenStreetMap, Esri reference labels and optional MapTiler, Globe.GL, pyproj/PROJ Equal Earth EPSG:8857. Credits in `docs/ATTRIBUTIONS.md`. A geographical basemap is not the historical source of the FIRMS detections.
- Historical visual feature ideas were researched in public hackathon examples, but BLINDSPOT's code and layout were implemented separately. Credit any later copied code under its license; do not misrepresent third-party work as original.

## Super Intelligence (SI) / AI disclosure — edit if necessary

The concept, audience and challenge solution were directed by the Parallax Labs team. AI coding assistants (ChatGPT/Codex) were used to help draft and debug Python/JavaScript implementation, generate UI and testing scaffolding, and organize source documentation and submission copy. Team members guided the design, inspected the real NASA archives, and are responsible for reviewing and validating their final submission. No AI-generated wildfire locations, satellite observations, calibration scores or agency incidents were inserted into real-data mode. The vector graphics in the attached slide template are programmatically drawn, not generated photographs. If the team uses any separately AI-generated illustrations, videos or audio, label them according to Space Apps SI rules.

## Why it is creative, relevant and valid

**Impact:** helps preparedness analysts interpret fragmented wildfire hotspot history more responsibly; simple evidence-backed seasonal brief.

**Creativity:** interactive spatial wipe, blindspot reveal, geographic custom-focus investigation, planet-to-local storytelling, and visually explicit uncertainty.

**Validity:** the shipped NASA records are real, filter/coverage provenance is reported, one global projected grid is used across all supported regions, with no unsupported prediction or accuracy claims. Automated API and analysis tests are included; live NASA API is not validated with the user's private key in this deliverable.

**Relevance:** answers the actual challenge—historical burning-activity calendar and harmonized observation representation—rather than substituting a generic live hotspot map.

**Presentation:** an identifiable analyst use case and a concise World → Alberta → Satellite Reveal → Calendar → Brief story.

## Official guide compliance checklist

- [ ] Every registered team member confirmed in the same local event / team.
- [ ] All required fields completed in English; correct team members and challenge.
- [ ] One **≤30 second video OR ≤7 slide** public demo linked (NOT a 3-minute official demo).
- [ ] Project source/final artifact linked publicly, no login or access requests.
- [ ] NASA FIRMS use documented; other data and visualization sources attributed.
- [ ] SI/AI usage disclosed; any AI-generated imagery/video visibly marked where required.
- [ ] All figures checked against the exact edition currently uploaded.
- [ ] Formal demo and project links opened successfully in an incognito window.
- [ ] Space Apps Project tab → Submit for Judging, before **Sunday Nov 15, 2026, 11:59 p.m. local event time**. Local in-person pitches may have separate schedules.
- [ ] Final confirmation banner appears; any final edits resubmitted before deadline.

This draft follows the user-supplied NASA Space Apps Challenge 2026 Project Submission Guide dated November 13, 2026. The guide says content must be English, uses a max 30-second video or 7-slide demo, and warns that private links can't be judged. This document is NOT evidence of actual submission.
