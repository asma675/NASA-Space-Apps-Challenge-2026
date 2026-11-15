"""Defensible prototype-level spatial/temporal alignment to one global equal-area grid/day.

We do NOT correct sensor detection probability, cloud coverage, or orbital sampling.
Active grid-days are not individual fires, area burned, or measured hazard.
"""
from __future__ import annotations
from collections import defaultdict
from datetime import date, timedelta
from math import ceil
from pyproj import Transformer

# Projected comparison methods. The global edition uses Equal Earth consistently.
CANADA_TRANSFORMER = Transformer.from_crs("EPSG:4326", "EPSG:3978", always_xy=True)
GLOBAL_TRANSFORMER = Transformer.from_crs("EPSG:4326", "EPSG:8857", always_xy=True) # Equal Earth, global equal-area
TRANSFORMER = GLOBAL_TRANSFORMER  # Backward-compatible alias; new edition uses Equal Earth globally.
CELL_METRES = 10000
MONTH_NAMES = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]


def cell_id(lat: float, lon: float, global_grid: bool=True):
    projection=GLOBAL_TRANSFORMER if global_grid else CANADA_TRANSFORMER
    x,y=projection.transform(lon,lat)
    return (int(x//CELL_METRES),int(y//CELL_METRES))


def month_range(start: str, end: str):
    sy, sm = map(int,start[:7].split("-"))
    ey, em = map(int,end[:7].split("-"))
    while (sy,sm) <= (ey,em):
        yield f"{sy:04d}-{sm:02d}"
        sy,sm = (sy+1,1) if sm==12 else (sy,sm+1)


def analyze(rows, region: dict, start: str, end: str, mode: str):
    # Deduplicates repeated detections within each (cell, UTC-day, sensor family).
    events = defaultdict(set)
    record_counts = defaultdict(lambda: {"MODIS":0,"VIIRS":0})
    representative = {}
    loaded_observations = 0
    global_grid=region.get('grid_projection')=='global'
    for row in rows:
        loaded_observations += 1
        family = row["family"]
        if family not in ("MODIS","VIIRS"):
            continue
        cell = cell_id(row["latitude"],row["longitude"],global_grid)
        key = (row["acq_date"],cell)
        events[key].add(family)
        record_counts[row["acq_date"][:7]][family] += 1
        if (key,family) not in representative:
            representative[(key,family)] = row

    month_stats = {m:{"month":m,"combined":0,"both":0,"modis_only":0,
                     "viirs_only":0,"modis":0,"viirs":0,"records":0} for m in month_range(start,end)}
    for (day,cell),families in events.items():
        stat = month_stats[day[:7]]
        stat["combined"] += 1
        if "MODIS" in families: stat["modis"] += 1
        if "VIIRS" in families: stat["viirs"] += 1
        if len(families)==2: stat["both"] += 1
        elif "MODIS" in families: stat["modis_only"] += 1
        else: stat["viirs_only"] += 1
    for month,cs in record_counts.items():
        if month in month_stats:
            month_stats[month]["records"] = cs["MODIS"]+cs["VIIRS"]

    timeline=list(month_stats.values())
    seasonal=[]
    for i, label in enumerate(MONTH_NAMES,1):
        # Average over the selected calendar years, including zero-detection months.
        sample = [r["combined"] for r in timeline if int(r["month"][5:])==i]
        seasonal.append({"name":label,"month":i,"average":round(sum(sample)/len(sample),2) if sample else 0,
                         "total":sum(sample),"years_in_range":len(sample)})
    total = {k:sum(s[k] for s in timeline) for k in ["combined","both","modis_only","viirs_only","modis","viirs","records"]}
    highest = sorted(seasonal, key=lambda x:x["average"], reverse=True)[:3]
    agreement = round(100*total["both"]/total["combined"],1) if total["combined"] else 0

    # Sample per month, so time travel can show months across the full selected range.
    samples_per_month=max(6,700//max(1,len(timeline)))
    by_month=defaultdict(list)
    for (key,family), row in representative.items():
        category=("matched" if len(events[key])==2 else ("modis_only" if family=="MODIS" else "viirs_only"))
        by_month[key[0][:7]].append((row,category))
    points=[]
    for month in sorted(by_month):
        ordered=sorted(by_month[month], key=lambda el:(el[0]["acq_date"],el[0]["product"]))
        # Evenly sample instead of taking only the first day of every month.
        stride=max(1,ceil(len(ordered)/samples_per_month))
        for p,category in ordered[::stride][:samples_per_month]:
            points.append({"latitude":p["latitude"],"longitude":p["longitude"],
                           "date":p["acq_date"],"family":p["family"],"product":p["product"],
                           "category":category,"origin":p["origin"],"frp":p.get("frp")})
    if total["combined"]:
        headline=f"{', '.join(s['name'] for s in highest)} are the highest observed seasonal months in this selected period."
        explanation=(f"{total['combined']:,} unique 10-km projected grid-days contained at least one hotspot detection. "
                     f"Both sensor families registered a hotspot in {agreement}% of active grid-days.")
    else:
        headline="No hotspots recorded for this region and date window in the selected dataset."
        explanation="No detections in the loaded records does not demonstrate an absence of fires or complete satellite coverage."
    return {
        "region":region,"mode":mode,"start":start,"end":end,
        "loaded_observations":loaded_observations,
        "summary":{**total,"sensor_agreement_pct":agreement,"peak_months":[x["name"] for x in highest],
                   "headline":headline,"explanation":explanation},
        "timeline":timeline,"seasonal":seasonal,"points":points,
        "methodology": {
           "grid":("10-km projected cells in global Equal Earth (EPSG:8857), grouped by UTC day" if global_grid else "10-km cells in Canada Atlas Lambert (EPSG:3978), grouped by UTC day"),
           "harmonization":"Spatial/temporal alignment and per-family de-duplication. NOT calibrated for detection sensitivity.",
           "metric":"Active grid-days (spatial cell x UTC date with >=1 hotspot detection)",
           "agreement":"Percentage of union active grid-days with detections from both MODIS and VIIRS; NOT accuracy or validation",
           "limitations":[
                "A hotspot is not a confirmed wildfire; agricultural burning may be included.",
                "Different satellite overpass times, clouds and sensor sensitivity are NOT corrected by grid alignment.",
                "No detection is not proof of no fire or adequate observation coverage.",
                "One grid-day may include multiple fires; this index is NOT fire counts or area burned.",
                "The common grid gives spatial/temporal alignment but not a validated inter-sensor calibration.",
                "This historical planning prototype is NOT a live alert or operational dispatch tool."
           ]
        }
    }
