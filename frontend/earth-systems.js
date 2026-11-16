/* Parallax BLINDSPOT Earth Systems · AI assistance disclosed in docs/AI_ASSISTANCE.md
 * All environmental values come from external model services. The interface never substitutes
 * generated numeric data when services are unavailable. Navigation is not emergency routing.
 */
(()=>{'use strict';
const page=document.body.dataset.page;if(!page||page==='earth')return;
const $=s=>document.querySelector(s);
const escapeHtml=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const regions={alberta:{lat:53.55,lon:-113.5,zoom:5,name:'Alberta'},ontario:{lat:49.1,lon:-85.2,zoom:5,name:'Northern Ontario'},california:{lat:40.3,lon:-122.0,zoom:6,name:'Northern California'},amazon:{lat:-4.8,lon:-62.1,zoom:5,name:'Amazon Basin'},australia:{lat:-33.5,lon:148.2,zoom:6,name:'New South Wales'},mediterranean:{lat:38.4,lon:23.5,zoom:7,name:'Greece'},southafrica:{lat:-26.3,lon:27.7,zoom:6,name:'South Africa'},southeastasia:{lat:17.9,lon:101.2,zoom:6,name:'Thailand'}};
let center={lat:regions.alberta.lat,lon:regions.alberta.lon};let map=null,baseLayer=null,ndvi=null,trueColor=null,aerosol=null,pin=null;let airMarkers=null;let routeLine=null;let origin=null,destination=null;let pointMarkers=[];let weatherData=null,airData=null;let reqVersion=0;
const dateToday=new Date().toISOString().slice(0,10);const yesterday=new Date(Date.now()-3*86400000).toISOString().slice(0,10);
const fmt=n=>n===null||n===undefined||!Number.isFinite(Number(n))?'—':Number(n).toLocaleString(undefined,{maximumFractionDigits:1});
const labelDate=v=>{try{return new Date(v+'T12:00:00Z').toLocaleDateString('en',{month:'short',day:'numeric',timeZone:'UTC'});}catch{return v;}};
const loading=(id,msg)=>{const e=$(id);if(e)e.textContent=msg;};
async function getJson(path){const resp=await fetch(path,{headers:{'Accept':'application/json'},cache:'no-store'});let data={};try{data=await resp.json();}catch{}if(!resp.ok)throw new Error(data.detail||'External data service unavailable');return data;}
function url(path){return `${path}?lat=${encodeURIComponent(center.lat.toFixed(4))}&lon=${encodeURIComponent(center.lon.toFixed(4))}`;}
function coords(){const c=$('#map-coords');if(c)c.textContent=`${center.lat.toFixed(3)}°, ${center.lon.toFixed(3)}° · click to inspect another location`;}
function failMessage(target,text){const e=$(target);if(e)e.textContent=text;}
function newPoint(lat,lon){if(pin&&map)map.removeLayer(pin);center={lat,lon};coords();if(map){pin=L.circleMarker([lat,lon],{radius:8,weight:2,color:'#eef8e7',fillColor:'#a8ebc6',fillOpacity:1}).addTo(map).bindPopup(`<b>Selected analysis point</b><br>${lat.toFixed(4)}, ${lon.toFixed(4)}`);}}
const tileAttribution='© OpenStreetMap contributors';
const tileStyles={
 night:{url:'https://tile.openstreetmap.org/{z}/{x}/{y}.png',options:{maxZoom:17,attribution:tileAttribution,className:'night-tiles'}},
 streets:{url:'https://tile.openstreetmap.org/{z}/{x}/{y}.png',options:{maxZoom:17,attribution:tileAttribution}},
 satellite:{url:'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',options:{maxZoom:17,attribution:'Tiles © Esri, Maxar, Earthstar Geographics'}}};
function setBase(name){if(!map)return;if(baseLayer)map.removeLayer(baseLayer);const cfg=tileStyles[name]||tileStyles.streets;baseLayer=L.tileLayer(cfg.url,cfg.options).addTo(map);document.querySelectorAll('[data-base]').forEach(b=>{b.classList.toggle('is-selected',b.dataset.base===name);b.setAttribute('aria-pressed',b.dataset.base===name?'true':'false');});if(ndvi&&map.hasLayer(ndvi))ndvi.bringToFront();if(trueColor&&map.hasLayer(trueColor))trueColor.bringToFront();if(aerosol&&map.hasLayer(aerosol))aerosol.bringToFront();}
function imageryLayer(name,day,opacity=.73){return L.tileLayer.wms('https://gibs.earthdata.nasa.gov/wms/epsg3857/best/wms.cgi',{layers:name,format:'image/png',version:'1.3.0',transparent:true,time:day,opacity,attribution:'NASA Global Imagery Browse Services (GIBS)'});}
function ensureLayer(layer,name,on){if(!map||!layer)return;if(on&&!map.hasLayer(layer))layer.addTo(map);if(!on&&map.hasLayer(layer))map.removeLayer(layer);}
function refreshImagery(){if(!map)return;const date=($('#image-date')||{}).value||yesterday;let old=ndvi;if(old)map.removeLayer(old);old=trueColor;if(old)map.removeLayer(old);old=aerosol;if(old)map.removeLayer(old);
 ndvi=imageryLayer('MODIS_Terra_NDVI_8Day',date,.77);
 trueColor=imageryLayer('MODIS_Terra_CorrectedReflectance_TrueColor',date,.83);
 aerosol=imageryLayer('MODIS_Terra_Aerosol',date,.63);
 for(const [layer,selector] of [[ndvi,'#layer-ndvi'],[trueColor,'#layer-truecolor'],[aerosol,'#layer-aerosol']]){const check=$(selector);if(check&&check.checked)layer.addTo(map);}
 if($('#veg-status')){loading('#veg-status',`NASA GIBS imagery requested for ${date} UTC. If no tiles appear, choose a nearby available day; map is still usable.`);ndvi.on('tileerror',()=>loading('#veg-status',`NDVI tiles unavailable for some views on ${date}; try another date or zoom. No NDVI values are inferred.`));}
}
function initMap(){if(!window.L){$('#earth-map').innerHTML='<div style="padding:30px;color:#efcfa7">Map library unavailable. Please connect to the internet, then reload. Environmental data remain separate from the map.</div>';return;}
 map=L.map('earth-map',{zoomControl:true,scrollWheelZoom:true,worldCopyJump:true,attributionControl:true}).setView([center.lat,center.lon],regions.alberta.zoom);setBase('dark');newPoint(center.lat,center.lon);map.on('click',evt=>{const {lat,lng}=evt.latlng;if(page==='navigation')return routeClick(lat,lng);newPoint(lat,lng);if(page==='air')refreshAir(false);if(page==='forecast')refreshForecast();if(page==='cascades')refreshCascades(false);});
 document.querySelectorAll('[data-base]').forEach(btn=>btn.addEventListener('click',()=>setBase(btn.dataset.base)));
 if(page==='vegetation'||page==='air'||page==='navigation')refreshImagery();
 setTimeout(()=>map.invalidateSize(),120);
}
function regionChange(){const preset=regions[$('#region-select')?.value]||regions.alberta;center={lat:preset.lat,lon:preset.lon};if(map){map.setView([center.lat,center.lon],preset.zoom,{animate:true});newPoint(center.lat,center.lon);}if(page==='air')refreshAir(true);if(page==='forecast')refreshForecast();if(page==='cascades')refreshCascades(true);if(page==='navigation')resetRoute();}
function airColor(n){return n==null?'#729199':n<=50?'#35c68d':n<=100?'#edc75f':n<=150?'#ed955e':'#b9699d';}
function renderAirGrid(samples){if(!map)return;if(airMarkers)airMarkers.remove();airMarkers=L.layerGroup().addTo(map);let count=0;
 for(const s of samples){if(s.aqi===null||s.aqi===undefined||!Number.isFinite(Number(s.aqi)))continue;count++;
  L.circleMarker([s.lat,s.lon],{radius:13,color:'#09202a',weight:2,fillColor:airColor(s.aqi),fillOpacity:.87}).bindPopup(`<b>CAMS/Open-Meteo modeled AQI</b><br>US AQI: ${fmt(s.aqi)}<br>PM2.5: ${fmt(s.pm25)} µg/m³<br>Time: ${escapeHtml(s.time||'not reported')}<br><small>Sample point; not station data or verified wildfire smoke</small>`).addTo(airMarkers);
 }
 if(count===0)throw Error('The provider returned no numeric AQI samples for this region.');
}
async function getAirGrid(){const delta=map&&map.getZoom()>=8?.35:map&&map.getZoom()>=6?.7:1.6;const data=await getJson(url('/api/earth/air-grid')+'&delta='+delta);renderAirGrid(data.samples||[]);return data;}
async function refreshAir(withGrid=true){const mine=++reqVersion;loading('#air-status','Requesting new modeled AQI and PM2.5 values…');
 if(withGrid){getAirGrid().then(()=>{if(reqVersion===mine)loading('#air-status','Nine CAMS model sample points are shown. Click a marker for values.');}).catch(e=>{if(reqVersion===mine)loading('#air-status','Sample grid unavailable: '+e.message)});}
 try{const data=await getJson(url('/api/earth/air'));if(reqVersion!==mine)return;airData=data;
  $('#air-summary').innerHTML=`<div class="metric"><span>SELECTED POINT US AQI</span><strong style="color:${airColor(data.current.us_aqi)}">${fmt(data.current.us_aqi)}</strong><small>model output · ${escapeHtml(data.current.time||'current')}</small></div><div class="metric"><span>PM2.5</span><strong>${fmt(data.current.pm2_5)}</strong><small>µg/m³ · CAMS model</small></div>`;
  $('#air-days').innerHTML=data.days.map(d=>`<div class="outlook-day"><span>${labelDate(d.date)}</span><b style="color:${airColor(d.aqi_max)}">${fmt(d.aqi_max)}</b><small>${fmt(d.pm25_max)} µg/m³ peak PM2.5</small></div>`).join('')||'<span class="soft">No forecast values available</span>';
  loading('#air-status','Forecasts are model estimates, not station readings; PM2.5 may come from sources other than wildfire.');
 }catch(e){if(reqVersion!==mine)return;$('#air-summary').innerHTML='<div class="metric">External provider unavailable; no values shown.</div>';$('#air-days').innerHTML='<span class="soft">Air-quality model unavailable. Retry after reconnecting to the internet.</span>';loading('#air-status',e.message);}}
function scoreColor(n){return n==null?'#7d9c9f':n<35?'#80d6b3':n<65?'#eaca8a':'#efaa8e';}
function maxValid(vals){const arr=vals.filter(x=>typeof x==='number'&&Number.isFinite(x));return arr.length?Math.max(...arr):null;}
async function refreshForecast(){const mine=++reqVersion;loading('#forecast-status','Querying the actual seven-day numerical weather forecast…');$('#forecast-chart').innerHTML='<span class="soft">Loading real forecast…</span>';
 try{const data=await getJson(url('/api/earth/weather'));if(reqVersion!==mine)return;weatherData=data;renderForecast(data);}catch(e){if(reqVersion!==mine)return;weatherData=null;$('#risk-summary').innerHTML='<span>UNAVAILABLE</span><strong>—</strong><p>No model data. Nothing has been simulated as an actual forecast.</p>';$('#forecast-chart').innerHTML='<span class="soft">Forecast unavailable: '+escapeHtml(e.message)+'</span>';$('#forecast-factors').innerHTML='';loading('#forecast-status',e.message);}}
function renderForecast(data){const scene=$('#scenario').value;const items=data.days||[];const valid=items.map(d=>d.attention?.[scene]?.score).filter(x=>x!==null&&x!==undefined);const top=maxValid(valid);const score=top===null?'—':top;const selected=items.find(d=>d.attention?.[scene]?.score===top)||items[0];$('#risk-summary').innerHTML=`<span>PEAK 7-DAY DESCRIPTIVE ATTENTION</span><strong style="color:${scoreColor(top)}">${score} <small>/ 100</small></strong><p>${top===null?'Insufficient forecast data.':`${escapeHtml(scene==='baseline'?'Forecast baseline':scene==='hotter_drier'?'Hypothetical hotter and drier conditions':'Hypothetical stronger wind')} · peak on ${escapeHtml(selected?.date||'unknown')}.`} <b>Not an ignition probability or operational risk rating.</b></p>`;
 $('#forecast-chart').innerHTML=items.map(d=>{const sc=d.attention?.[scene]?.score;return `<div class="forecast-bar" title="${escapeHtml(d.date)} · ${fmt(sc)} /100 · Temp ${fmt(d.temperature_c)} °C · Humidity ${fmt(d.humidity_pct)} % · Wind ${fmt(d.wind_kmh)} km/h"><div class="column"><i style="height:${sc===null||sc===undefined?0:Math.max(4,sc)}%;background:linear-gradient(${scoreColor(sc)},#446f79)"></i></div><strong>${fmt(sc)}</strong><span>${labelDate(d.date)}</span></div>`}).join('')||'<span class="soft">No forecast days received.</span>';
 $('#forecast-factors').innerHTML=selected?`<span>Temperature: ${fmt(selected.temperature_c)}°C</span><span>Humidity: ${fmt(selected.humidity_pct)}%</span><span>Wind: ${fmt(selected.wind_kmh)} km/h</span><span>Rain: ${fmt(selected.rain_mm)} mm</span>`:'';
 loading('#forecast-status','Selected point = weather-model location. Chart shows assumptions, not projected wildfire boundaries.');}
function resetRoute(){origin=destination=null;if(routeLine&&map){map.removeLayer(routeLine);routeLine=null;}for(const m of pointMarkers)if(map)map.removeLayer(m);pointMarkers=[];const a=$('#origin-readout'),b=$('#destination-readout');if(a)a.textContent='Not selected';if(b)b.textContent='Not selected';const stats=$('#route-stats');if(stats)stats.innerHTML='<div><b>—</b><small>distance</small></div><div><b>—</b><small>model travel time</small></div><div><b>Not checked</b><small>closures / fire hazards</small></div>';const status=$('#route-status');if(status)status.innerHTML='<span>ROUTE STATUS</span><strong>Choose two points on the map</strong><p>No wildfire hazard routing or road closure feeds are included.</p>';}
function routeClick(lat,lon){const target=[lat,lon];if(origin&&destination)resetRoute();if(!origin)origin=target;else destination=target;pointMarkers.push(L.circleMarker(target,{radius:9,weight:3,color:'#0c2630',fillColor:pointMarkers.length===0?'#98e8bc':'#f4c68a',fillOpacity:1}).addTo(map).bindTooltip(pointMarkers.length===0?'Origin':'Destination'));
 if(origin)$('#origin-readout').textContent=origin.map(x=>x.toFixed(3)).join(', ');if(destination)$('#destination-readout').textContent=destination.map(x=>x.toFixed(3)).join(', ');coords();}
async function calculateRoute(){if(!origin||!destination){$('#route-status').innerHTML='<span>ROUTE STATUS</span><strong>Select both origin and destination</strong><p>Click once for the starting point, then again for the destination.</p>';return;}
 const btn=$('#calculate-route');btn.disabled=true;$('#route-status').innerHTML='<span>PUBLIC OSRM DEMO</span><strong>Requesting a road route…</strong><p>Does not consider wildfire spread or closures.</p>';
 try{const path=`${origin[1]},${origin[0]};${destination[1]},${destination[0]}`;const data=await getJson(`https://router.project-osrm.org/route/v1/driving/${path}?overview=full&geometries=geojson&steps=false`);const road=data.routes?.[0];if(!road||!road.geometry?.coordinates)throw Error('No route was returned for those points.');if(routeLine)map.removeLayer(routeLine);routeLine=L.geoJSON(road.geometry,{style:{color:'#f2bc82',weight:5,opacity:.95}}).addTo(map);map.fitBounds(routeLine.getBounds(),{padding:[34,34]});const dist=road.distance/1000,mins=Math.round(road.duration/60);$('#route-stats').innerHTML=`<div><b>${fmt(dist)} km</b><small>OSRM route distance</small></div><div><b>${mins} min</b><small>model travel time</small></div><div><b>Not checked</b><small>closures / fire hazards</small></div>`;$('#route-status').innerHTML='<span>ROUTE FOUND</span><strong>Ordinary road network route</strong><p>This line is <b>not</b> a safe evacuation route. Do not rely on it for emergency movement.</p>';
 }catch(e){$('#route-status').innerHTML='<span>ROUTE UNAVAILABLE</span><strong>No route could be verified</strong><p>'+escapeHtml(e.message)+'</p>';}finally{btn.disabled=false;}}
function cascadeSignal(kind,weather,air){const days=weather?.days||[],ad=air?.days||[];const maxGust=maxValid(days.map(d=>d.gust_kmh));const maxScore=maxValid(days.map(d=>d.attention?.baseline?.score));const maxPM=maxValid(ad.map(d=>d.pm25_max));const maxAqi=maxValid(ad.map(d=>d.aqi_max));
 if(kind==='health')return [
 ['MODEL INPUT',maxPM===null?'PM2.5 unavailable':`Peak modeled PM2.5: ${fmt(maxPM)} µg/m³`,'Copernicus CAMS forecast includes multiple pollution sources.'],
 ['POTENTIAL CONCERN',maxPM===null?'Insufficient air model data':maxPM>35?'Elevated particulate exposure warrants review':'Review local air-quality outlook','Not a prediction of wildfire-specific smoke or health outcomes.'],
 ['VERIFY / ACTION','Check public-health advice','Use official EPA AirNow / Environment Canada air quality alerts before changing plans.']];
 if(kind==='mobility')return [
 ['MODEL INPUT',maxGust===null?'Wind forecast unavailable':`Peak forecast gusts: ${fmt(maxGust)} km/h`,'A localized numerical weather model, not verified at every road.'],
 ['POTENTIAL CONCERN',maxGust===null?'Insufficient weather data':maxGust>=50?'Conditions may warrant transport monitoring':'Review transport-weather exposure','This does not establish that roads will close or travel will be disrupted.'],
 ['VERIFY / ACTION','Check transportation agencies','Check road restrictions and weather alerts from provincial/state authorities.']];
 if(kind==='infrastructure')return [
 ['MODEL INPUT',maxScore===null?'Weather indicators unavailable':`Peak attention index: ${fmt(maxScore)}/100`,'Unvalidated descriptive combination of local weather forecast inputs.'],
 ['POTENTIAL CONCERN','Review critical-system exposure','Wind and dry conditions may motivate checks of power, communications and access dependencies, without predicting failures.'],
 ['VERIFY / ACTION','Consult infrastructure operators','No building inventories, utility outage data or validated impact model are integrated.']];
 return [
 ['MODEL INPUT',maxScore===null?'Weather indicators unavailable':`Peak weather attention: ${fmt(maxScore)}/100`,'NDVI visual imagery is available separately in the Vegetation map.'],
 ['POTENTIAL CONCERN','Review vegetation stress questions','Hot, dry conditions may motivate ecological monitoring. No fuel moisture or vegetation loss is predicted.'],
 ['VERIFY / ACTION','Cross-check satellite vegetation','Open NASA NDVI imagery and agency/ecological datasets; check season and land cover.']];}
async function refreshCascades(withGrid=true){const mine=++reqVersion;loading('#cascade-status','Retrieving independent weather and air-quality forecast signals…');$('#cascade-narrative').innerHTML='<span class="soft">Loading real environmental data…</span>';
 if(withGrid)getAirGrid().catch(e=>loading('#cascade-status','AQI map sample unavailable: '+e.message));
 const outputs=await Promise.allSettled([getJson(url('/api/earth/weather')),getJson(url('/api/earth/air'))]);if(reqVersion!==mine)return;
 weatherData=outputs[0].status==='fulfilled'?outputs[0].value:null;airData=outputs[1].status==='fulfilled'?outputs[1].value:null;
 const sector=$('#concern-sector').value;const rows=cascadeSignal(sector,weatherData,airData);
 $('#cascade-narrative').innerHTML=rows.map((r,i)=>`<div class="cascade-box"><span>${escapeHtml(r[0])}</span><b>${escapeHtml(r[1])}</b><p>${escapeHtml(r[2])}</p></div>`).join('');
 const unavailable=[];if(!weatherData)unavailable.push('weather');if(!airData)unavailable.push('air');loading('#cascade-status',unavailable.length?'Unavailable providers: '+unavailable.join(', ')+'. No missing measurements were invented.':'Model signals updated. This map indicates sample inputs, not actual impact or hazard boundaries.');}
function init(){initMap();const rs=$('#region-select');if(rs)rs.addEventListener('change',regionChange);
 if(page==='vegetation'){const di=$('#image-date');di.addEventListener('change',refreshImagery);for(const id of ['#layer-ndvi','#layer-truecolor'])$(id)?.addEventListener('change',refreshImagery);refreshImagery();}
 if(page==='air'){const ac=$('#layer-aerosol');ac?.addEventListener('change',refreshImagery);$('#refresh-air').addEventListener('click',()=>refreshAir(true));refreshAir(true);}
 if(page==='navigation'){$('#layer-aerosol')?.addEventListener('change',refreshImagery);$('#clear-route').addEventListener('click',resetRoute);$('#calculate-route').addEventListener('click',calculateRoute);}
 if(page==='forecast'){$('#scenario').addEventListener('change',()=>weatherData&&renderForecast(weatherData));$('#refresh-forecast').addEventListener('click',refreshForecast);refreshForecast();}
 if(page==='cascades'){$('#refresh-cascades').addEventListener('click',()=>refreshCascades(true));$('#concern-sector').addEventListener('change',()=>refreshCascades(false));refreshCascades(true);}}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',init);else init();
})();
