> **Global 2026 update:** This live pitch uses the revised *unified Equal Earth 10-km grid* (17,094 union, 9,268 both, 1,084 MODIS-only, 6,742 VIIRS-only, 54.2% co-observation). Demonstrate World Atlas carefully: the historical observations embedded in the app remain Alberta 2023 only; recent global NASA data requires a private key. The formal submission demo is ≤30 seconds video OR ≤7 slides.

# PARALLAX BLINDSPOT — 3-minute judge pitch

**Challenge:** NASA Space Apps Challenge 2026 — Harmonization of MODIS and VIIRS Hot Spots  
**Audience:** Maya, an Alberta wildfire preparedness analyst  
**Value:** Investigate two incomplete satellite stories on common spatial/daily units, explore the burning-activity calendar, see where evidence is missing, and take away an honest readiness brief.

> **Opening hook:** "The danger isn't just a fire no one sees. It's a satellite record that looks complete when it isn't."

### 0:00–0:25 — Human problem

"This is Maya. She plans historical monitoring priorities for Alberta's next fire season. NASA's MODIS and VIIRS satellites both report hotspots—but not the same ones. More points from VIIRS doesn't automatically mean more fires. Which periods should Maya investigate when the sensor records disagree?"

**On screen:** Start on the moving globe. Scroll to **Blindspot Reveal**.

### 0:25–1:13 — THE WOW MOMENT

"We built BLINDSPOT to reveal that difference. I'll slide from MODIS to VIIRS, while viewing the *same place and time*."

**On screen:** Drag the divider; then click **REVEAL BLINDSPOTS**.

"These colours aren't a risk model. Orange represents grid cells dominated by MODIS-exclusive grid-days, lavender by VIIRS-exclusive, and mint by both. Instead of comparing mismatched raw pixel counts, we align detections into common projected 10-kilometre cells and UTC days. Each sensor family counts once per cell-day."

**Show the evidence numbers from the embedded Alberta dataset (May–October 2023, presumed vegetation-fire type 0):**
- 17,094 union active grid-days
- 9,268 co-observed MODIS+VIIRS grid-days
- 6,742 VIIRS-only grid-days
- 1,084 MODIS-only grid-days
- 54.2% co-observation — **NOT sensor accuracy**

"We can see where the records differ. That does *not* prove a sensor missed the same wildfire: clouds, overpass times and detection limits matter."

### 1:13–1:47 — Time travel + real data quality

**On screen:** Select **September 2023** in the Investigation month picker. Scroll to the calendar.

"Maya can now see the burning calendar. September, July and August had the highest observed grid-day activity in this *one archived season*. Our filter also removes 4,246 NASA records tagged as non-vegetation/static/offshore thermal anomalies, while preserving the raw files. We're not calling all 547,021 raw points verified fires."

**On screen:** Point to **Data Provenance / Quality Gate**.

### 1:47–2:15 — Scientific honesty as a feature

**On screen:** Show **Fire Season Detective** and **Calibration Audit**.

"One year isn't enough to say whether September was unusual historically. So rather than invent an anomaly score, our app tells Maya exactly what additional archive coverage is needed. The importer supports multiple real years; after sufficient overlapping coverage, the method evaluates a preliminary sensor-rate scaling on an unseen year. It reports the error even if the model fails. This is a transparent research pathway, not a claim to have calibrated satellite physics."

### 2:15–2:37 — Own the area; cross-check reality

**On screen:** Click **Draw your area**, select two corners over Alberta (or demonstrate the preselected province). Open **Canada Evidence Lab**.

"Maya can focus the analysis on her own geographic area. NASA observations and Alberta's agency-reported wildfire incidents are different kinds of evidence. We keep them separate; if the official history CSV is imported, she can check nearby incident-date coincidences without claiming each hotspot is a verified wildfire."

### 2:37–3:00 — Decision and closing

**On screen:** Download the **Readiness Brief**.

"Maya leaves with the months worth monitoring, an explanation of sensor disagreement, a traceable data-quality filter, and questions she can take to local fire experts. BLINDSPOT does not predict ignition or replace an emergency agency. It helps a planner avoid false certainty.

**A fire map shows dots. BLINDSPOT reveals the difference between what was observed, what was not established, and what a responsible analyst should do next.**"

---

## Demo operator checklist

- [ ] Start the **complete** ZIP, not the GitHub code-only ZIP.
- [ ] Check `http://127.0.0.1:8765/api/config` includes raw real MODIS and VIIRS counts.
- [ ] Select Alberta (province archive), **Real FIRMS records**, May 1–October 31, 2023.
- [ ] Use the drag handle and **Reveal Blindspots** once each.
- [ ] Show 17,094 union, 9,268 both, 6,742 VIIRS-only, 1,084 MODIS-only, 54.2% overlap.
- [ ] Use September 2023 month; demonstrate how the count changes for that period.
- [ ] Optionally draw two corners and reset to the full region.
- [ ] Highlight that **only 2023 is loaded**; multi-year anomaly and holdout calibration deliberately remain unavailable.
- [ ] Mention Alberta official CSV is not embedded yet; don't invent official incident matches.
- [ ] End with Readiness Brief.

**Avoid saying:** "We predict the next fire", "MODIS missed 6,742 fires", "We have 25 years of Alberta data", or "54.2% accuracy". All are unsupported.
