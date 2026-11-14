'use strict';
/* Parallax BLINDSPOT — MapTiler vector basemaps + free CARTO fallback. */
const $ = id => document.getElementById(id);
const state = { analysis:null, selectedMonth:null, layer:'all', map:null, layers:null, leaflet:false, config:null, baseFallback:null, maptilerLayer:null, mapStyle:'auto', mapRegion:null, mapProvider:null, maptilerPublicKey:'' };
const months=['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
const fmt = n => new Intl.NumberFormat('en-CA').format(n||0);
const params = () => new URLSearchParams({region:$('region').value,start:$('start-date').value,end:$('end-date').value,mode:$('mode').value});
const escapeHTML = s=> String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
let toastTimer;
function toast(message){const el=$('toast');el.textContent=message;el.classList.add('show');clearTimeout(toastTimer);toastTimer=setTimeout(()=>el.classList.remove('show'),4000);}
async function api(url,opts){const resp=await fetch(url,opts);if(!resp.ok){let msg=`HTTP ${resp.status}`;try{const d=await resp.json();msg=d.detail||msg;}catch{}throw new Error(msg);}return resp.json();}
function setTheme(theme){document.body.dataset.theme=theme;$('theme-button').textContent=theme==='dark'?'☀':'☾';localStorage.setItem('blindspot-theme',theme);if(state.map){if(state.mapStyle==='auto') applyBasemap();setTimeout(()=>state.map.invalidateSize(),150);}}
function updateDataBanner(mode,records){const demo=mode==='demo',b=$('data-banner');b.classList.toggle('real',!demo);$('data-title').textContent=demo?'ILLUSTRATIVE DATA — NOT NASA':'REAL-DATA MODE — VERIFY PROVENANCE';$('data-message').textContent=demo?'Synthetic records demonstrate product interactions only. All counts and locations are fictitious.':'Loaded FIRMS API or user-imported records. Alignment is not sensor sensitivity calibration; inspect observation coverage and sources.';if(!records){$('data-message').textContent += ' There are no matching records for the selected region and dates.';}}
function download(kind){window.location.assign('/api/export/'+kind+'?'+params());}
async function load(){const button=$('analyze-button');button.disabled=true;button.textContent='Analyzing…';try{const d=await api('/api/analysis?'+params());state.analysis=d;state.selectedMonth=null;render(d);if(!d.loaded_observations)toast('No matching records. Import NASA data in Data Studio or switch to illustrative mode.');}catch(e){toast('Analysis failed: '+e.message);}finally{button.disabled=false;button.innerHTML='Analyze region <span>↗</span>';}}
function render(d){const s=d.summary;updateDataBanner(d.mode,d.loaded_observations);$('m-combined').textContent=fmt(s.combined);$('m-both').textContent=fmt(s.both);$('m-viirs').textContent=fmt(s.viirs_only);$('m-overlap').textContent=s.sensor_agreement_pct+'%';$('bar-m-value').textContent=fmt(s.modis_only);$('bar-v-value').textContent=fmt(s.viirs_only);$('bar-b-value').textContent=fmt(s.both);const max=Math.max(s.modis_only,s.viirs_only,s.both,1);$('bar-m').style.width=100*s.modis_only/max+'%';$('bar-v').style.width=100*s.viirs_only/max+'%';$('bar-b').style.width=100*s.both/max+'%';$('data-context').textContent=`${d.region.name} · ${d.start} to ${d.end}`;$('brief-headline').textContent=s.headline;$('brief-explanation').textContent=s.explanation;$('brief-months').textContent=s.combined?`Review ${s.peak_months.join(', ')} first, then cross-check with official regional fire history and forecasts.`:'Load more historical observations before prioritizing seasonal monitoring.';$('brief-overlap').textContent=`${fmt(s.modis_only)} MODIS-only, ${fmt(s.viirs_only)} VIIRS-only, and ${fmt(s.both)} matched active grid-days. Overlap is not proof of accuracy.`;renderCalendar(d.timeline);drawFingerprint(d.seasonal);renderMap();}
function cellShade(value,max){if(!value)return '#233047';let p=value/Math.max(1,max);if(p<.15)return '#51446f';if(p<.3)return '#74557d';if(p<.5)return '#a06679';if(p<.75)return '#cc7e69';return '#eda85e';}
function renderCalendar(timeline){const parent=$('calendar-grid');parent.replaceChildren();const max=Math.max(0,...timeline.map(o=>o.combined));const indexed=new Map(timeline.map(t=>[t.month,t]));const years=[...new Set(timeline.map(t=>t.month.slice(0,4)))];const head=document.createElement('div');head.className='calendar-head';head.innerHTML='<span>YEAR</span>'+months.map(m=>`<span>${m.toUpperCase()}</span>`).join('');parent.append(head);for(const year of years){const row=document.createElement('div');row.className='calendar-row';let label=document.createElement('span');label.className='calendar-year';label.textContent=year;row.append(label);for(let i=1;i<=12;i++){const key=year+'-'+String(i).padStart(2,'0');const data=indexed.get(key);const b=document.createElement('button');b.type='button';b.className='cal-cell'+(!data?' empty':'');b.textContent=data?fmt(data.combined):'—';b.style.backgroundColor=data?cellShade(data.combined,max):'var(--panel2)';b.disabled=!data;b.title=data?`${key}: ${data.combined} active grid-days; MODIS-only ${data.modis_only}, VIIRS-only ${data.viirs_only}, matched ${data.both}`:'Outside selected range';b.dataset.month=key;b.setAttribute('aria-label',b.title);b.addEventListener('click',()=>selectMonth(state.selectedMonth===key?null:key));row.append(b);}parent.append(row);}}
function selectMonth(month){state.selectedMonth=month;document.querySelectorAll('.cal-cell').forEach(el=>el.classList.toggle('active',el.dataset.month===month));if(month){const x=state.analysis.timeline.find(t=>t.month===month);$('selected-month').textContent=`${months[Number(month.slice(5))-1]} ${month.slice(0,4)} — ${fmt(x.combined)} active grid-days`;$('selected-detail').textContent=`MODIS-only ${fmt(x.modis_only)} · VIIRS-only ${fmt(x.viirs_only)} · Matched ${fmt(x.both)}. Map shows a sample.`;}else{$('selected-month').textContent='All months selected';$('selected-detail').textContent='Map shows sampled observations across the date range.';}renderMap();}
function drawFingerprint(items){const el=$('fingerprint');el.replaceChildren();const NS='http://www.w3.org/2000/svg',svg=document.createElementNS(NS,'svg');svg.setAttribute('viewBox','0 0 410 312');svg.setAttribute('role','img');svg.setAttribute('aria-label','12 month seasonal burning activity radar');const center=[205,156],outer=112,max=Math.max(...items.map(i=>i.average),1);function point(index,r){const a=index*Math.PI/6-Math.PI/2;return [center[0]+Math.cos(a)*r,center[1]+Math.sin(a)*r];}function shape(tag,attrs){const e=document.createElementNS(NS,tag);Object.entries(attrs).forEach(([k,v])=>e.setAttribute(k,v));svg.append(e);return e;}for(let level=1;level<=4;level++){const ring=[];for(let i=0;i<12;i++){const p=point(i,outer*level/4);ring.push(p.join(','));}shape('polygon',{points:ring.join(' '),fill:'none',stroke:'var(--line)','stroke-width':1});}for(let i=0;i<12;i++){const p=point(i,outer);shape('line',{x1:205,y1:156,x2:p[0],y2:p[1],stroke:'var(--line)','stroke-width':1});const tx=point(i,133),text=shape('text',{x:tx[0],y:tx[1]+3,'font-size':11,'text-anchor':'middle',fill:'var(--muted)','font-family':'DM Sans'});text.textContent=months[i];}const polygon=items.map((m,i)=>point(i,12+(outer-12)*m.average/max).join(',')).join(' ');shape('polygon',{points:polygon,fill:'#8c71f6','fill-opacity':'.22',stroke:'#a493ff','stroke-width':2.7,'stroke-linejoin':'round'});for(let i=0;i<12;i++){const p=point(i,12+(outer-12)*items[i].average/max);shape('circle',{cx:p[0],cy:p[1],r:3.5,fill:'#d7a2ff',stroke:'#7348c9','stroke-width':1});}el.append(svg);}
// Public MapTiler browser keys are intended for client-side mapping. Restrict by allowed domains on MapTiler Cloud.
function maptilerKey(){return (state.config?.maptiler_public_key||'').trim();}
function resolvedStyle(){return state.mapStyle==='auto'?(document.body.dataset.theme==='light'?'light':'dark'):state.mapStyle;}
const BASEMAP_STYLES={dark:'dataviz-dark',light:'dataviz-light',satellite:'satellite-v2',hybrid:'hybrid'};
function updateMapSource(source){state.mapProvider=source;const out=$('map-provider');if(out)out.textContent=source;const detail=$('map-status');if(detail){detail.textContent=source.startsWith('MapTiler')?'MapTiler geography · NASA FIRMS observation overlay':'Open map fallback · NASA FIRMS observation overlay';}}
function applyBasemap(){
  if(!state.leaflet)return;
  const map=state.map,style=resolvedStyle(),key=maptilerKey();
  if(state.maptilerLayer){map.removeLayer(state.maptilerLayer);state.maptilerLayer=null;}
  if(state.baseFallback){map.removeLayer(state.baseFallback);state.baseFallback=null;}
  // OpenStreetMap raster tiles are the no-key fallback. CARTO's basemap API now
  // overlays an API-key-required watermark when no CARTO key is supplied.
  state.baseFallback=L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',{
    subdomains:'abc',maxZoom:19,attribution:'&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
  }).addTo(map);
  updateMapSource('OpenStreetMap fallback');
  if(key){
    // Use MapTiler's raster tiles directly through Leaflet. This avoids depending
    // on the optional MapTiler Leaflet SDK adapter being present on the CDN.
    const tileUrl=`https://api.maptiler.com/maps/${BASEMAP_STYLES[style]}/{z}/{x}/{y}.png?key=${encodeURIComponent(key)}`;
    state.maptilerLayer=L.tileLayer(tileUrl,{maxZoom:20,attribution:'&copy; <a href="https://www.maptiler.com/copyright/">MapTiler</a> &copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'}).addTo(map);
    updateMapSource('MapTiler '+({dark:'Dataviz Dark',light:'Dataviz Light',satellite:'Satellite imagery',hybrid:'Satellite + labels'}[style]));
    let failed=false;
    state.maptilerLayer.once('tileerror',()=>{if(failed)return;failed=true;if(state.maptilerLayer){map.removeLayer(state.maptilerLayer);state.maptilerLayer=null;}updateMapSource('OpenStreetMap fallback · MapTiler tile request failed');});
  }else if(style==='satellite'||style==='hybrid'){$('map-status').textContent='MapTiler key is missing; showing OpenStreetMap.';}
  if($('map-style'))$('map-style').value=state.mapStyle;
}
function initMap(){
  if(!window.L){state.leaflet=false;return;}
  state.leaflet=true;
  const map=L.map('map',{preferCanvas:true,zoomControl:false,attributionControl:true,zoomSnap:.5});
  L.control.zoom({position:'topright'}).addTo(map);
  L.control.scale({position:'bottomright',imperial:false}).addTo(map);
  state.map=map;applyBasemap();
  state.layers=L.layerGroup().addTo(map);
  map.setView([51,-86],5);
}
function resetMapView(){
  if(!state.map||!state.analysis)return;
  const bounds=state.analysis.region.bbox;
  state.map.fitBounds([[bounds[1],bounds[0]],[bounds[3],bounds[2]]],{padding:[22,22],maxZoom:9,animate:true});
}
function changeMapStyle(next){
  if(!['auto','dark','light','satellite','hybrid'].includes(next))return;
  state.mapStyle=next;localStorage.setItem('blindspot-map-style',next);applyBasemap();
}
function saveMapKey(){
  const key=$('maptiler-key').value.trim();
  if(!/^[A-Za-z0-9_-]{6,128}$/.test(key)){toast('Enter a valid MapTiler public API key.');return;}
  sessionStorage.setItem('blindspot-maptiler-key',key);
  $('maptiler-key').value='';updateMapKeyStatus();applyBasemap();toast('MapTiler enabled in this browser tab.');
}
function clearMapKey(){sessionStorage.removeItem('blindspot-maptiler-key');$('maptiler-key').value='';updateMapKeyStatus();applyBasemap();}
function updateMapKeyStatus(){const el=$('maptiler-status');if(!el)return;const browser=!!sessionStorage.getItem('blindspot-maptiler-key'),server=!!state.config?.maptiler_key_configured;el.textContent=browser?'✓ Browser MapTiler key active for this tab':server?'✓ Server MapTiler key configured':'MapTiler key not configured; CARTO maps remain available.';}

function mapPoints(){const d=state.analysis;if(!d)return[];return d.points.filter(p=>(!state.selectedMonth||p.date.startsWith(state.selectedMonth))&&(state.layer==='all'||state.layer===p.family||(state.layer==='exclusive'&&p.category!=='matched')));}
function renderMap(){const d=state.analysis;if(!d)return;const points=mapPoints();$('map-count').textContent=`${fmt(points.length)} sampled observations · ${state.layer==='all'?'MODIS + VIIRS':state.layer}`;if(state.leaflet){const map=state.map;state.layers.clearLayers();if(state.mapRegion!==d.region.name){state.mapRegion=d.region.name;resetMapView();}for(const p of points){const c=p.family==='MODIS'?'#f9a765':'#a98bff';const label=`<strong>${escapeHTML(p.family)} observation</strong><br>UTC date: ${escapeHTML(p.date)}<br>Relationship: ${escapeHTML(p.category.replaceAll('_',' '))}<br>Origin: ${escapeHTML(p.origin)}<br><small>Detection, not verified individual wildfire.</small>`;L.circleMarker([p.latitude,p.longitude],{radius:5.5,color:c,fillColor:c,fillOpacity:.8,weight:1.4}).bindPopup(label,{maxWidth:270}).addTo(state.layers);}return;}
    // Offline map fallback: use an SVG projection of the region, never an invented basemap.
    const el=$('map');el.replaceChildren();el.style.background='radial-gradient(circle at 20% 40%,#234b5a,#12283a 60%,#0e1f30)';let svg=document.createElementNS('http://www.w3.org/2000/svg','svg');svg.setAttribute('viewBox','0 0 600 365');svg.setAttribute('width','100%');svg.setAttribute('height','100%');const [w,s,e,n]=d.region.bbox;const make=(tag,attrs)=>{const x=document.createElementNS('http://www.w3.org/2000/svg',tag);Object.entries(attrs).forEach(([k,v])=>x.setAttribute(k,v));svg.append(x);return x;};for(let i=0;i<12;i++){make('line',{x1:i*55,y1:0,x2:i*55,y2:365,stroke:'#486579','stroke-opacity':'.3'});}for(let i=0;i<8;i++){make('line',{x1:0,y1:i*52,x2:600,y2:i*52,stroke:'#486579','stroke-opacity':'.3'});}for(const p of points){make('circle',{cx:(p.longitude-w)/(e-w)*600,cy:(n-p.latitude)/(n-s)*365,r:3,fill:p.family==='MODIS'?'#f9a765':'#b296ff','fill-opacity':'.8'});}el.append(svg);}
async function refreshConfig(){try{state.config=await api('/api/config');$('api-status').innerHTML='<i></i> API connected';$('api-status').classList.remove('down');if(state.map&&maptilerKey()&&!state.maptilerLayer)applyBasemap();}catch(e){$('api-status').innerHTML='<i></i> API offline';$('api-status').classList.add('down');}}
function studioMessage(str,good){const el=$('studio-message');el.textContent=str;el.className='studio-message '+(good?'good':'error');}
function getToken(){return $('admin-token').value;}
async function ingest(){const b=$('ingest-button');b.disabled=true;studioMessage('Fetching NASA observations — this may take several requests…',true);try{const d=await api('/api/ingest/nasa',{method:'POST',headers:{'Content-Type':'application/json','X-Admin-Token':getToken()},body:JSON.stringify({region:$('region').value,start_date:$('ingest-start').value,end_date:$('ingest-end').value,products:['MODIS_SP','VIIRS_SNPP_SP']})});studioMessage(`Imported ${d.inserted} new observations across ${d.requests} NASA requests. Choose Real FIRMS and matching dates to explore.`,true);$('mode').value='real';$('start-date').value=$('ingest-start').value;$('end-date').value=$('ingest-end').value;await load();}catch(e){studioMessage('Import failed: '+e.message,false);}finally{b.disabled=false;}}
async function upload(){const file=$('upload-file').files[0];if(!file){studioMessage('Choose a CSV file first.',false);return;}if(file.size>9e6){studioMessage('File is over 9MB. Split into smaller files.',false);return;}studioMessage('Importing CSV…',true);try{const data=await file.text();const d=await api('/api/import/csv?product='+encodeURIComponent($('upload-product').value),{method:'POST',headers:{'Content-Type':'text/plain','X-Admin-Token':getToken()},body:data});studioMessage(`Imported ${d.inserted} new rows (parsed ${d.parsed}). Select matching dates and real mode to investigate.`,true);await refreshConfig();}catch(e){studioMessage('Import failed: '+e.message,false);}}
window.addEventListener('DOMContentLoaded',async()=>{
  setTheme(localStorage.getItem('blindspot-theme')==='light'?'light':'dark');
  $('theme-button').addEventListener('click',()=>setTheme(document.body.dataset.theme==='dark'?'light':'dark'));
  $('analyze-button').addEventListener('click',load);
  $('mode').addEventListener('change',load);
  $('clear-selection').addEventListener('click',()=>selectMonth(null));
  document.querySelectorAll('[data-layer]').forEach(b=>b.addEventListener('click',()=>{state.layer=b.dataset.layer;document.querySelectorAll('[data-layer]').forEach(x=>x.classList.toggle('selected',x===b));renderMap();}));
  $('export-brief').addEventListener('click',()=>download('brief.md'));
  $('export-csv').addEventListener('click',()=>download('monthly.csv'));
  state.mapStyle=['auto','dark','light','satellite','hybrid'].includes(localStorage.getItem('blindspot-map-style'))?localStorage.getItem('blindspot-map-style'):'auto';
  $('map-style').value=state.mapStyle;
  $('map-style').addEventListener('change',e=>changeMapStyle(e.target.value));
  $('map-reset').addEventListener('click',resetMapView);
  initMap();await refreshConfig();await load();
});
