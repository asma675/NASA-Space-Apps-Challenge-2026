"""Independent, transparent contextual environmental services for BLINDSPOT.

AI assistance disclosed in docs/AI_ASSISTANCE.md. No fire ignition predictions,
no validated risk probabilities, no assertion that smoke or routes are safe.
External Open-Meteo weather / CAMS air-quality data are kept separate from FIRMS.
"""
from __future__ import annotations
import asyncio
import math
import time
from dataclasses import dataclass
from typing import Any
import httpx

WEATHER_URL="https://api.open-meteo.com/v1/forecast"
AIR_URL="https://air-quality-api.open-meteo.com/v1/air-quality"
WEATHER_FIELDS="temperature_2m_max,relative_humidity_2m_min,wind_speed_10m_max,wind_gusts_10m_max,precipitation_sum"
AIR_FIELDS="pm2_5,pm10,us_aqi"
_CACHE: dict[tuple,tuple[float,Any]]={}
_TTL=600.0

def check_coords(lat:float,lon:float)->None:
    if not (math.isfinite(lat) and math.isfinite(lon) and -85 <= lat <= 85 and -180 <= lon <=180):
        raise ValueError("Coordinates must be finite and in supported latitude/longitude bounds")

def clamp(value:float, low:float=0, high:float=1)->float:
    return max(low,min(high,value))

def attention_index(temp:float|None, rh:float|None, wind:float|None, rain:float|None, scenario:str="baseline")->dict[str,Any]:
    """Unvalidated descriptive weather-attention heuristic (NOT fire forecast).

    The weights are designed for transparency, not trained or calibrated on fire outcomes.
    Returns 'insufficient_data' rather than manufacturing absent weather input.
    """
    fields=(temp,rh,wind,rain)
    if any(x is None or not isinstance(x,(int,float)) or not math.isfinite(x) for x in fields):
        return {"score":None,"band":"unavailable","status":"insufficient_data"}
    if scenario not in ("baseline","hotter_drier","windier"):
        raise ValueError("Unknown scenario")
    t,h,w,r=map(float,fields)
    if scenario=="hotter_drier": t+=4;h=max(0,h-15)
    elif scenario=="windier": w+=15
    components={
      "humidity":round(35*clamp((55-h)/40),1),
      "wind":round(30*clamp((w-15)/40),1),
      "heat":round(20*clamp((t-18)/22),1),
      "low_rainfall":round(15*(1-clamp(r/7)),1),
    }
    score=int(round(sum(components.values())))
    band="lower" if score<35 else "watch" if score<65 else "elevated"
    return {"score":score,"band":band,"status":"illustrative_not_validated", "components":components,
      "adjusted_inputs":{"temp_c":round(t,1),"humidity_pct":round(h,1),"wind_kmh":round(w,1),"rain_mm":round(r,1)}}

async def _request(url:str, params:dict[str,Any])->Any:
    key=(url,tuple(sorted((str(k),str(v)) for k,v in params.items())))
    now=time.monotonic()
    item=_CACHE.get(key)
    if item and item[0]>now:return item[1]
    async with httpx.AsyncClient(timeout=12,follow_redirects=True) as client:
        result=await client.get(url,params=params,headers={"User-Agent":"Parallax-BLINDSPOT-Earth-Systems/1.0 (educational research)"})
        result.raise_for_status()
        data=result.json()
    if isinstance(data,dict) and data.get("error"):
        raise ValueError(str(data.get("reason","Data provider returned an error")))
    if len(_CACHE)>150:_CACHE.clear()
    _CACHE[key]=(now+_TTL,data)
    return data

async def weather_conditions(lat:float,lon:float)->dict[str,Any]:
    check_coords(lat,lon)
    data=await _request(WEATHER_URL,{"latitude":lat,"longitude":lon,"daily":WEATHER_FIELDS,"timezone":"UTC","forecast_days":7})
    daily=data.get("daily") or {}
    dates=daily.get("time") or []
    days=[]
    for i,when in enumerate(dates):
        def val(field):
            arr=daily.get(field) or []
            return arr[i] if i<len(arr) else None
        record={"date":when,"temperature_c":val("temperature_2m_max"),"humidity_pct":val("relative_humidity_2m_min"),
           "wind_kmh":val("wind_speed_10m_max"),"gust_kmh":val("wind_gusts_10m_max"),"rain_mm":val("precipitation_sum")}
        record["attention"]={scenario:attention_index(record["temperature_c"],record["humidity_pct"],record["wind_kmh"],record["rain_mm"],scenario)
                 for scenario in ("baseline","hotter_drier","windier")}
        days.append(record)
    return {"source":"Open-Meteo weather forecast model aggregation","retrieved_from":"Open-Meteo Forecast API","latitude":lat,"longitude":lon,
            "timezone":"UTC","days":days,"scenario_disclaimer":"Unvalidated descriptive index; scenarios are user-imposed assumptions, not ignition probabilities or validated wildfire forecasts."}

async def air_conditions(lat:float,lon:float)->dict[str,Any]:
    check_coords(lat,lon)
    data=await _request(AIR_URL,{"latitude":lat,"longitude":lon,"hourly":AIR_FIELDS,"current":AIR_FIELDS,"timezone":"UTC","forecast_days":5})
    hourly=data.get("hourly") or {}
    current=data.get("current") or {}
    daily={}
    for i,t in enumerate(hourly.get("time") or []):
        day=t[:10]
        d=daily.setdefault(day,{"date":day,"aqi_max":None,"pm25_max":None,"pm10_max":None,"hours":0})
        d["hours"]+=1
        for field,out in (("us_aqi","aqi_max"),("pm2_5","pm25_max"),("pm10","pm10_max")):
            col=hourly.get(field) or []
            value=col[i] if i<len(col) else None
            if isinstance(value,(int,float)) and math.isfinite(value):
                d[out]=round(max(value,d[out] if d[out] is not None else value),1)
    return {"source":"Copernicus CAMS via Open-Meteo air quality forecast (modeled, not station measurements)",
          "latitude":lat,"longitude":lon,"current":{"time":current.get("time"),"us_aqi":current.get("us_aqi"),"pm2_5":current.get("pm2_5"),"pm10":current.get("pm10")},
          "days":list(daily.values()),"unit_pm25":"µg/m³","disclaimer":"Forecast concentrations include various pollution sources; PM2.5 does not establish the source as wildfire smoke."}

async def sampled_air_grid(lat:float,lon:float,delta:float=1.1)->dict[str,Any]:
    check_coords(lat,lon)
    if not 0.15 <= delta <=3:raise ValueError("Sampling extent must be between 0.15 and 3 degrees")
    pts=[(round(clamp(lat+dy*delta,-84.9,84.9),4),round(clamp(lon+dx*delta,-179.9,179.9),4)) for dy in (-1,0,1) for dx in (-1,0,1)]
    lats=','.join(str(x[0]) for x in pts);lons=','.join(str(x[1]) for x in pts)
    data=await _request(AIR_URL,{"latitude":lats,"longitude":lons,"current":"pm2_5,us_aqi","timezone":"UTC","forecast_days":1})
    if isinstance(data,dict):data=[data]
    if not isinstance(data,list) or len(data)!=len(pts):
        raise ValueError("Air-quality provider returned unexpected sample count")
    samples=[]
    for pt,item in zip(pts,data):
        current=item.get("current") or {}
        samples.append({"lat":pt[0],"lon":pt[1],"aqi":current.get("us_aqi"),"pm25":current.get("pm2_5"),"time":current.get("time")})
    return {"source":"Open-Meteo/CAMS model samples (3×3 points, not a continuous raster)","samples":samples,
            "disclaimer":"Interpolated model sample locations. Marker colors are not direct station measurements or exact smoke boundaries."}
