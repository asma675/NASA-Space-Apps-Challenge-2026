'use strict';
/* Parallax BLINDSPOT — Wildfire Watch Canada Esri imagery map adapted for historical NASA FIRMS. */
const $ = id => document.getElementById(id);
const state = { analysis:null, selectedMonth:null, layer:'all', map:null, layers:null, leaflet:false, config:null, baseFallback:null, maptilerLayer:null, mapStyle:'illustrated', mapRegion:null, mapProvider:null, maptilerPublicKey:'', mapLabelLayer:null, mapLabels:true, mapGlow:true };
const months=['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
const fmt = n => new Intl.NumberFormat('en-CA').format(n||0);
const params = () => {const p=new URLSearchParams({region:$('region').value,start:$('start-date').value,end:$('end-date').value,mode:$('mode').value});if(window.BLINDSPOT_BBOX)p.set('bbox',window.BLINDSPOT_BBOX.join(','));return p;};
const escapeHTML = s=> String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
let toastTimer;
function toast(message){const el=$('toast');el.textContent=message;el.classList.add('show');clearTimeout(toastTimer);toastTimer=setTimeout(()=>el.classList.remove('show'),4000);}
async function api(url,opts){const resp=await fetch(url,opts);if(!resp.ok){let msg=`HTTP ${resp.status}`;try{const d=await resp.json();msg=d.detail||msg;}catch{}throw new Error(msg);}return resp.json();}
function setTheme(theme){document.body.dataset.theme=theme;$('theme-button').textContent=theme==='dark'?'☀':'☾';localStorage.setItem('blindspot-theme',theme);if(state.map){if(state.mapStyle==='auto') applyBasemap();setTimeout(()=>state.map.invalidateSize(),150);}}
function updateDataBanner(mode,records){const demo=mode==='demo',b=$('data-banner');b.classList.toggle('real',!demo);$('data-title').textContent=demo?'ILLUSTRATIVE DATA — NOT NASA':'REAL-DATA MODE — VERIFY PROVENANCE';$('data-message').textContent=demo?'Synthetic records demonstrate product interactions only. All counts and locations are fictitious.':'Genuine NASA FIRMS records. The bundled archive covers Alberta 2023 only; World searches loaded records, not complete worldwide history. Cell-day alignment is not calibrated sensor sensitivity or a current fire alert.';if(!records){$('data-message').textContent += ' There are no matching records for the selected region and dates.';}}
function download(kind){window.location.assign('/api/export/'+kind+'?'+params());}
async function load(){const button=$('analyze-button');button.disabled=true;button.textContent='Analyzing…';try{const d=await api('/api/analysis?'+params());state.analysis=d;state.selectedMonth=null;render(d);if(!d.loaded_observations)toast('No matching records. Import NASA data in Data Studio or switch to illustrative mode.');}catch(e){toast('Analysis failed: '+e.message);}finally{button.disabled=false;button.innerHTML='Analyze region <span>↗</span>';}}
function render(d){const s=d.summary;updateDataBanner(d.mode,d.loaded_observations);$('m-combined').textContent=fmt(s.combined);$('m-both').textContent=fmt(s.both);$('m-viirs').textContent=fmt(s.viirs_only);$('m-overlap').textContent=s.sensor_agreement_pct+'%';$('bar-m-value').textContent=fmt(s.modis_only);$('bar-v-value').textContent=fmt(s.viirs_only);$('bar-b-value').textContent=fmt(s.both);const max=Math.max(s.modis_only,s.viirs_only,s.both,1);$('bar-m').style.width=100*s.modis_only/max+'%';$('bar-v').style.width=100*s.viirs_only/max+'%';$('bar-b').style.width=100*s.both/max+'%';$('data-context').textContent=`${d.region.name} · ${d.start} to ${d.end}`;$('atlas-coverage-desc').textContent=d.coverage_note||'Archived data need geographical source verification.';$('brief-headline').textContent=s.headline;$('brief-explanation').textContent=s.explanation;$('brief-months').textContent=s.combined?`Review ${s.peak_months.join(', ')} first, then cross-check with official regional fire history and forecasts.`:'Load more historical observations before prioritizing seasonal monitoring.';$('brief-overlap').textContent=`${fmt(s.modis_only)} MODIS-only, ${fmt(s.viirs_only)} VIIRS-only, and ${fmt(s.both)} matched active grid-days. Overlap is not proof of accuracy.`;renderCalendar(d.timeline);drawFingerprint(d.seasonal);renderMap();renderSeasonalWatch(d);renderGlobePoints(d);window.dispatchEvent(new CustomEvent("blindspot:analysis-ready",{detail:d}));}
function cellShade(value,max){if(!value)return '#233047';let p=value/Math.max(1,max);if(p<.15)return '#51446f';if(p<.3)return '#74557d';if(p<.5)return '#a06679';if(p<.75)return '#cc7e69';return '#eda85e';}
function renderCalendar(timeline){const parent=$('calendar-grid');parent.replaceChildren();const max=Math.max(0,...timeline.map(o=>o.combined));const indexed=new Map(timeline.map(t=>[t.month,t]));const years=[...new Set(timeline.map(t=>t.month.slice(0,4)))];const head=document.createElement('div');head.className='calendar-head';head.innerHTML='<span>YEAR</span>'+months.map(m=>`<span>${m.toUpperCase()}</span>`).join('');parent.append(head);for(const year of years){const row=document.createElement('div');row.className='calendar-row';let label=document.createElement('span');label.className='calendar-year';label.textContent=year;row.append(label);for(let i=1;i<=12;i++){const key=year+'-'+String(i).padStart(2,'0');const data=indexed.get(key);const unknown=data&&data.coverage==='unverified'&&!(data.records>0);const b=document.createElement('button');b.type='button';b.className='cal-cell'+((!data||unknown)?' empty':'')+(unknown?' unverified':'');b.textContent=unknown?'NO DATA':data?fmt(data.combined):'—';b.style.backgroundColor=data&&!unknown?cellShade(data.combined,max):'var(--panel2)';b.disabled=!data||unknown;b.title=data?`${key}: ${unknown?'archive coverage not verified':data.combined+' observed active grid-days'}; MODIS-only ${data.modis_only}, VIIRS-only ${data.viirs_only}, matched ${data.both}. Coverage: ${data.coverage||'unknown'}`:'Outside selected range';b.dataset.month=key;b.setAttribute('aria-label',b.title);b.addEventListener('click',()=>selectMonth(state.selectedMonth===key?null:key));row.append(b);}parent.append(row);}}
function selectMonth(month){state.selectedMonth=month;document.querySelectorAll('.cal-cell').forEach(el=>el.classList.toggle('active',el.dataset.month===month));if(month){const x=state.analysis.timeline.find(t=>t.month===month);$('selected-month').textContent=`${months[Number(month.slice(5))-1]} ${month.slice(0,4)} — ${fmt(x.combined)} active grid-days`;$('selected-detail').textContent=`MODIS-only ${fmt(x.modis_only)} · VIIRS-only ${fmt(x.viirs_only)} · Matched ${fmt(x.both)}. Map shows a sample.`;}else{$('selected-month').textContent='All months selected';$('selected-detail').textContent='Map shows sampled observations across the date range.';}renderMap();window.dispatchEvent(new CustomEvent("blindspot:month-selected",{detail:{month}}));}
function drawFingerprint(items){const el=$('fingerprint');el.replaceChildren();const NS='http://www.w3.org/2000/svg',svg=document.createElementNS(NS,'svg');svg.setAttribute('viewBox','0 0 410 312');svg.setAttribute('role','img');svg.setAttribute('aria-label','12 month seasonal burning activity radar');const center=[205,156],outer=112,max=Math.max(...items.map(i=>i.average),1);function point(index,r){const a=index*Math.PI/6-Math.PI/2;return [center[0]+Math.cos(a)*r,center[1]+Math.sin(a)*r];}function shape(tag,attrs){const e=document.createElementNS(NS,tag);Object.entries(attrs).forEach(([k,v])=>e.setAttribute(k,v));svg.append(e);return e;}for(let level=1;level<=4;level++){const ring=[];for(let i=0;i<12;i++){const p=point(i,outer*level/4);ring.push(p.join(','));}shape('polygon',{points:ring.join(' '),fill:'none',stroke:'var(--line)','stroke-width':1});}for(let i=0;i<12;i++){const p=point(i,outer);shape('line',{x1:205,y1:156,x2:p[0],y2:p[1],stroke:'var(--line)','stroke-width':1});const tx=point(i,133),text=shape('text',{x:tx[0],y:tx[1]+3,'font-size':11,'text-anchor':'middle',fill:'var(--muted)','font-family':'DM Sans'});text.textContent=months[i];}const polygon=items.map((m,i)=>point(i,12+(outer-12)*m.average/max).join(',')).join(' ');shape('polygon',{points:polygon,fill:'#8c71f6','fill-opacity':'.22',stroke:'#a493ff','stroke-width':2.7,'stroke-linejoin':'round'});for(let i=0;i<12;i++){const p=point(i,12+(outer-12)*items[i].average/max);shape('circle',{cx:p[0],cy:p[1],r:3.5,fill:'#d7a2ff',stroke:'#7348c9','stroke-width':1});}el.append(svg);}
// Public MapTiler browser keys are intended for client-side mapping. Restrict by allowed domains on MapTiler Cloud.
function maptilerKey(){return (sessionStorage.getItem('blindspot-maptiler-key')||state.config?.maptiler_public_key||'').trim();}
function resolvedStyle(){return state.mapStyle==='auto'?(document.body.dataset.theme==='light'?'light':'dark'):state.mapStyle;}
const BASEMAP_STYLES={dark:()=>L.MaptilerStyle.DATAVIZ.DARK,light:()=>L.MaptilerStyle.DATAVIZ.LIGHT,satellite:()=>L.MaptilerStyle.SATELLITE,hybrid:()=>L.MaptilerStyle.HYBRID};
function updateMapSource(source, detail){
  state.mapProvider=source;
  const out=$('map-provider');if(out)out.textContent=source;
  const msg=$('map-status');if(msg)msg.textContent=detail||'Historical NASA FIRMS hotspot overlay · not live fire alerts';
}
function labelsAvailable(){return state.mapStyle==='watch'||((resolvedStyle()==='satellite'||resolvedStyle()==='hybrid')&&!maptilerKey());}
function updateMapControlLabels(){
  const labelButton=$('map-labels');
  if(labelButton){labelButton.disabled=!labelsAvailable();labelButton.setAttribute('aria-pressed',String(state.mapLabels));labelButton.classList.toggle('is-active',state.mapLabels&&labelsAvailable());labelButton.textContent=state.mapLabels?'◆ Labels on':'◇ Labels off';labelButton.title=labelsAvailable()?'Show or hide the cartographic labels used in Wildfire Watch Canada':'Map labels are built into this selected basemap';}
  const glow=$('map-glow');if(glow){glow.setAttribute('aria-pressed',String(state.mapGlow));glow.classList.toggle('is-active',state.mapGlow);glow.textContent=state.mapGlow?'◉ Glow on':'◯ Glow off';}
}
// Map basemaps must never depend on CARTO's former unauthenticated tiles.
// Keyless OSM for street/dark maps; optional Esri imagery for Wildfire Watch;
// MapTiler styles remain available when a user supplies a public browser key.
function noKeyStreetLayer(dark=false){
  return L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png',{
    maxZoom:19, className:state.mapStyle==='illustrated'?'blindspot-osm-illustrated':dark?'blindspot-osm-dark':'blindspot-osm-light',
    attribution:'&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap contributors</a>'
  });
}
function addSatelliteLabels(map){
  if(!state.mapLabels)return;
  // Esri reference labels; avoid CARTO's key-required label tiles.
  const labels=L.tileLayer('https://services.arcgisonline.com/ArcGIS/rest/services/Reference/World_Boundaries_and_Places/MapServer/tile/{z}/{y}/{x}',{
    maxZoom:19,opacity:.9,attribution:'Reference labels &copy; <a href="https://www.esri.com/">Esri</a>'
  }).addTo(map);
  state.mapLabelLayer=labels;
  let failed=false;
  labels.on('tileerror',()=>{
    if(failed||!map.hasLayer(labels))return;
    failed=true;map.removeLayer(labels);
    if(state.mapLabelLayer===labels)state.mapLabelLayer=null;
    updateMapSource(state.mapProvider,'Reference labels unavailable; satellite imagery and NASA detections remain available.');
  });
}
function applyBasemap(){
  if(!state.leaflet)return;
  const map=state.map,style=resolvedStyle(),key=maptilerKey();
  for(const existing of [state.maptilerLayer,state.baseFallback,state.mapLabelLayer]){
    if(existing&&map.hasLayer(existing))map.removeLayer(existing);
  }
  state.maptilerLayer=null;state.baseFallback=null;state.mapLabelLayer=null;
  const isSatellite=['watch','satellite','hybrid'].includes(style);
  // No-key fallback is always available. The satellite option is geographic
  // context, not a historical image taken at the time of the hotspots.
  if(isSatellite){
    const esri=L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',{
      maxZoom:19,attribution:'Imagery &copy; <a href="https://www.esri.com/">Esri</a>, Vantor, Earthstar Geographics, and the GIS User Community'
    }).addTo(map);
    state.baseFallback=esri;
    updateMapSource('WILDFIRE WATCH · ESRI SATELLITE','Satellite basemap · NASA historical hotspot overlay (not date-matched imagery)');
    addSatelliteLabels(map);
    let imageryFailed=false;
    esri.on('tileerror',()=>{
      if(imageryFailed||!map.hasLayer(esri))return;
      imageryFailed=true;map.removeLayer(esri);
      if(state.mapLabelLayer&&map.hasLayer(state.mapLabelLayer))map.removeLayer(state.mapLabelLayer);
      state.mapLabelLayer=null;
      state.baseFallback=noKeyStreetLayer(false).addTo(map);
      updateMapSource('OpenStreetMap · imagery fallback','Esri tiles unavailable; displaying OpenStreetMap geographic context.');
    });
  }else{
    const dark=(style==='dark');
    state.baseFallback=noKeyStreetLayer(dark).addTo(map);
    updateMapSource(style==='illustrated'?'Illustrated Atlas · OSM':dark?'OpenStreetMap · Night':'OpenStreetMap · Streets',
      'No-key geographic basemap · NASA historical hotspot overlay');
  }
  if(key&&style!=='watch'&&style!=='illustrated'&&window.L.maptiler?.maptilerLayer&&window.L.MaptilerStyle){
    try{
      state.maptilerLayer=L.maptiler.maptilerLayer({apiKey:key,style:BASEMAP_STYLES[style](),language:'en'}).addTo(map);
      updateMapSource('MapTiler '+({dark:'Dataviz Dark',light:'Dataviz Light',satellite:'Satellite',hybrid:'Satellite Hybrid'}[style]),
        'MapTiler geographic basemap · NASA historical hotspot overlay');
      const custom=state.maptilerLayer;
      custom.on?.('error',()=>{
        if(!map.hasLayer(custom))return;
        map.removeLayer(custom);
        if(state.maptilerLayer===custom)state.maptilerLayer=null;
        updateMapSource(isSatellite?'Esri satellite fallback':'OpenStreetMap fallback',
          'MapTiler tiles unavailable; the no-key geographic map is still displayed.');
      });
    }catch(error){state.maptilerLayer=null;console.warn('Optional MapTiler unavailable',error);}
  }
  if($('map-style'))$('map-style').value=state.mapStyle;
  updateMapControlLabels();
}

function initMap(){
  if(!window.L){state.leaflet=false;return;}
  state.leaflet=true;
  const map=L.map('map',{preferCanvas:true,zoomControl:false,attributionControl:true,zoomSnap:.5});
  L.control.zoom({position:'topright'}).addTo(map);
  L.control.scale({position:'bottomright',imperial:false}).addTo(map);
  state.map=map;applyBasemap();
  state.layers=L.layerGroup().addTo(map);
  state.liveLayers=L.layerGroup().addTo(map);
  map.setView([51,-86],5);
}
function resetMapView(){
  if(!state.map||!state.analysis)return;
  const bounds=state.analysis.region.bbox;
  state.map.fitBounds([[bounds[1],bounds[0]],[bounds[3],bounds[2]]],{padding:[22,22],maxZoom:9,animate:true});
}
function changeMapStyle(next){
  if(!['illustrated','watch','auto','dark','light','satellite','hybrid'].includes(next))return;
  state.mapStyle=next;localStorage.setItem('blindspot-map-style',next);applyBasemap();
}
function toggleMapLabels(){state.mapLabels=!state.mapLabels;localStorage.setItem('blindspot-map-labels',String(state.mapLabels));applyBasemap();}
function toggleMapGlow(){state.mapGlow=!state.mapGlow;localStorage.setItem('blindspot-map-glow',String(state.mapGlow));updateMapControlLabels();renderMap();}
function saveMapKey(){
  const key=$('maptiler-key').value.trim();
  if(!/^[A-Za-z0-9_-]{6,128}$/.test(key)){toast('Enter a valid MapTiler public API key.');return;}
  sessionStorage.setItem('blindspot-maptiler-key',key);
  $('maptiler-key').value='';updateMapKeyStatus();applyBasemap();toast('MapTiler enabled in this browser tab.');
}
function clearMapKey(){sessionStorage.removeItem('blindspot-maptiler-key');$('maptiler-key').value='';updateMapKeyStatus();applyBasemap();}
function updateMapKeyStatus(){const el=$('maptiler-status');if(!el)return;const browser=!!sessionStorage.getItem('blindspot-maptiler-key'),server=!!state.config?.maptiler_key_configured;el.textContent=browser?'✓ Browser MapTiler key active for this tab':server?'✓ Server MapTiler key configured':'MapTiler key not configured; OpenStreetMap and Esri maps remain available.';}

function mapPoints(){const d=state.analysis;if(!d)return[];return d.points.filter(p=>(!state.selectedMonth||p.date.startsWith(state.selectedMonth))&&(state.layer==='all'||state.layer===p.family||(state.layer==='exclusive'&&p.category!=='matched')));}
function renderMap(){const d=state.analysis;if(!d)return;const points=mapPoints();$('map-count').textContent=`${fmt(points.length)} sampled observations · ${state.layer==='all'?'MODIS + VIIRS':state.layer}`;if(state.leaflet){const map=state.map;state.layers.clearLayers();if(state.mapRegion!==d.region.name){state.mapRegion=d.region.name;resetMapView();}for(const p of points){const c=p.family==='MODIS'?'#f9a765':'#a98bff';const label=`<strong>${escapeHTML(p.family)} observation</strong><br>UTC date: ${escapeHTML(p.date)}<br>Relationship: ${escapeHTML(p.category.replaceAll('_',' '))}<br>Origin: ${escapeHTML(p.origin)}<br><small>Detection, not verified individual wildfire.</small>`;// Glowing rings echo Wildfire Watch's satellite marker treatment without asserting a verified fire location.
      if(state.mapGlow){L.circleMarker([p.latitude,p.longitude],{radius:10,color:c,fillColor:c,fillOpacity:.17,weight:0,interactive:false}).addTo(state.layers);}
      L.circleMarker([p.latitude,p.longitude],{radius:4.6,color:'#ffffff',fillColor:c,fillOpacity:.92,weight:.65,opacity:.75})
        .bindPopup(label,{maxWidth:270}).addTo(state.layers);}return;}
    // Offline map fallback: use an SVG projection of the region, never an invented basemap.
    const el=$('map');el.replaceChildren();el.style.background='radial-gradient(circle at 20% 40%,#234b5a,#12283a 60%,#0e1f30)';let svg=document.createElementNS('http://www.w3.org/2000/svg','svg');svg.setAttribute('viewBox','0 0 600 365');svg.setAttribute('width','100%');svg.setAttribute('height','100%');const [w,s,e,n]=d.region.bbox;const make=(tag,attrs)=>{const x=document.createElementNS('http://www.w3.org/2000/svg',tag);Object.entries(attrs).forEach(([k,v])=>x.setAttribute(k,v));svg.append(x);return x;};for(let i=0;i<12;i++){make('line',{x1:i*55,y1:0,x2:i*55,y2:365,stroke:'#486579','stroke-opacity':'.3'});}for(let i=0;i<8;i++){make('line',{x1:0,y1:i*52,x2:600,y2:i*52,stroke:'#486579','stroke-opacity':'.3'});}for(const p of points){make('circle',{cx:(p.longitude-w)/(e-w)*600,cy:(n-p.latitude)/(n-s)*365,r:3,fill:p.family==='MODIS'?'#f9a765':'#b296ff','fill-opacity':'.8'});}el.append(svg);}
async function refreshConfig(){try{state.config=await api('/api/config');$('api-status').innerHTML='<i></i> API connected';$('api-status').classList.remove('down');$('key-status').textContent=state.config.firms_key_configured?'✓ FIRMS key is configured server-side.':'⚠ FIRMS key not configured. Add FIRMS_MAP_KEY to .env and restart the server.';updateMapKeyStatus();if(state.map&&maptilerKey()&&!state.maptilerLayer)applyBasemap();}catch(e){$('api-status').innerHTML='<i></i> API offline';$('api-status').classList.add('down');$('key-status').textContent='API unavailable';}}
function studioMessage(str,good){const el=$('studio-message');el.textContent=str;el.className='studio-message '+(good?'good':'error');}
function getToken(){return $('admin-token').value;}
async function ingest(){const b=$('ingest-button');b.disabled=true;studioMessage('Fetching NASA observations — this may take several requests…',true);try{const d=await api('/api/ingest/nasa',{method:'POST',headers:{'Content-Type':'application/json','X-Admin-Token':getToken()},body:JSON.stringify({region:$('region').value,start_date:$('ingest-start').value,end_date:$('ingest-end').value,products:['MODIS_SP','VIIRS_SNPP_SP']})});studioMessage(`Imported ${d.inserted} new observations across ${d.requests} NASA requests. Choose Real FIRMS and matching dates to explore.`,true);$('mode').value='real';$('start-date').value=$('ingest-start').value;$('end-date').value=$('ingest-end').value;await load();}catch(e){studioMessage('Import failed: '+e.message,false);}finally{b.disabled=false;}}
async function upload(){const file=$('upload-file').files[0];if(!file){studioMessage('Choose a CSV file first.',false);return;}if(file.size>9e6){studioMessage('File is over 9MB. Split into smaller files.',false);return;}studioMessage('Importing CSV…',true);try{const data=await file.text();const d=await api('/api/import/csv?product='+encodeURIComponent($('upload-product').value),{method:'POST',headers:{'Content-Type':'text/plain','X-Admin-Token':getToken()},body:data});studioMessage(`Imported ${d.inserted} new rows (parsed ${d.parsed}). Select matching dates and real mode to investigate.`,true);await refreshConfig();}catch(e){studioMessage('Import failed: '+e.message,false);}}
// Judge Edition: the globe is a sample of the SAME historical observations used in the 2D map.
// WebGL/CDN failure falls back to the existing CSS orb; no simulated fire positions.
function initGlobe(){
  const el=$('hero-globe');
  if(!el||!window.Globe)return;
  try{
    const orb=new Globe(el)
      .width(315).height(315)
      .globeImageUrl('https://unpkg.com/three-globe/example/img/earth-night.jpg')
      .bumpImageUrl('https://unpkg.com/three-globe/example/img/earth-topology.png')
      .backgroundColor('rgba(0,0,0,0)')
      .showAtmosphere(true).atmosphereColor('#658df8').atmosphereAltitude(.18)
      .pointLat('latitude').pointLng('longitude')
      .pointColor(p=>p.family==='MODIS'?'#ffae70':'#b9a1ff')
      .pointRadius(.16).pointAltitude(.012).pointsTransitionDuration(400)
      .pointLabel(p=>`<div style="background:#101e31;color:#f4f7ff;border:1px solid #445a77;padding:8px;border-radius:8px;font-size:11px"><strong>${escapeHTML(p.family)} ${p.recent?'recent thermal signal':'historical hotspot'}</strong><br>${escapeHTML(p.date)} UTC<br>Not a verified wildfire</div>`)
      .onPointClick(p=>{if(p.recent){toast('NASA near-real-time thermal observation, not a confirmed wildfire or a historical calendar date.');return;}if(state.analysis){selectMonth(p.date.slice(0,7));$('xray').scrollIntoView({behavior:'smooth',block:'start'});}})
      .pointOfView({lat:54.2,lng:-115,altitude:2.05},900);
    const controls=orb.controls();
    if(controls){controls.autoRotate=!matchMedia('(prefers-reduced-motion: reduce)').matches;controls.autoRotateSpeed=.45;controls.enableDamping=true;}
    state.globe=orb;
    const fallback=el.querySelector('.globe-css-fallback');if(fallback)fallback.classList.add('is-hidden');
  }catch(error){console.warn('WebGL globe unavailable; decorative orbital fallback remains',error);}
}
function bootGlobe(){
  // Load WebGL enhancement asynchronously: never block the core NASA map/dashboard.
  if(window.Globe){initGlobe();return;}
  const script=document.createElement('script');
  script.src='https://cdn.jsdelivr.net/npm/globe.gl';script.async=true;
  script.onload=()=>{initGlobe();if(state.analysis)renderGlobePoints(state.analysis);};
  script.onerror=()=>console.warn('Optional 3D globe CDN failed; CSS globe fallback is shown.');
  document.head.append(script);
}
function renderGlobePoints(d){
  if(!state.globe)return;
  if($('atlas-recent-total').textContent==='Not checked' && state.atlasLayers)state.atlasLayers.clearLayers();
  const filtered=d.points.filter(p=>p.latitude>=-90&&p.latitude<=90&&p.longitude>=-180&&p.longitude<=180);
  // Historical sample only. Full analytical totals remain on the server.
  state.globe.pointsData(filtered.slice(0,260));
  const b=d.region.bbox;
  state.globe.pointOfView({lat:(b[1]+b[3])/2,lng:(b[0]+b[2])/2,altitude:2.1},850);
}
function renderSeasonalWatch(d){
  const box=$('seasonal-watch');if(!box)return;
  const stats=d.summary;
  if(d.mode!=='real'){
    box.innerHTML='<div class="watch-placeholder">Demo mode uses synthetic data. Switch to <strong>Real FIRMS records</strong> for evidence-based seasonal signals.</div>';
    return;
  }
  if(!d.loaded_observations){box.innerHTML='<div class="watch-placeholder">No historical observations match your date and region. Select Alberta 2023 or import NASA data.</div>';return;}
  const peak=d.seasonal.filter(x=>x.total>0).sort((a,b)=>b.total-a.total).slice(0,2);
  const overlap=stats.sensor_agreement_pct;
  const top=peak[0];
  const hot=top?`<div class="watch-alert"><div class="signal-emoji">☼</div><div><strong>Seasonal watch: ${escapeHTML(top.name)} was busiest</strong><span>${fmt(top.total)} active 10-km grid-days in selected ${escapeHTML(top.name)} observations. Consider reviewing preparedness coverage before this season.</span><small>HISTORICAL · NOT A FUTURE FIRE FORECAST</small></div></div>`:'';
  const minority=stats.viirs_only>stats.modis_only?'VIIRS-only':'MODIS-only';
  const gap=`<div class="watch-alert"><div class="signal-emoji">◉</div><div><strong>Sensor difference: investigate the unmatched observations</strong><span>${fmt(stats.viirs_only)} VIIRS-only and ${fmt(stats.modis_only)} MODIS-only active grid-days. Both sensors have detections in ${overlap}% of active grid-days.</span><small>CHECK COVERAGE & OVERPASS TIMES · NOT MISSED-FIRE PROOF</small></div></div>`;
  box.innerHTML=hot+gap;
}
function setWatchBadge(label,kind){const el=$('watch-feed-badge');el.textContent=label;el.className='watch-feed-badge'+(kind?' is-'+kind:'');}
function formatStamp(iso){if(!iso)return'unknown';const dt=new Date(iso);return Number.isNaN(dt.getTime())?'unavailable':dt.toLocaleString('en-CA',{timeZone:'UTC',dateStyle:'medium',timeStyle:'short'})+' UTC';}
function formatDuration(minutes){if(!Number.isFinite(minutes))return'unknown';if(minutes<60)return`${minutes} min`;if(minutes<1440)return`${Math.floor(minutes/60)}h ${minutes%60}m`;return`${Math.floor(minutes/1440)}d ${Math.floor(minutes%1440/60)}h`;}
let notifiedBaseline=null;
function updateLiveMap(alerts){
  if(!state.liveLayers||!state.leaflet)return;
  state.liveLayers.clearLayers();
  const label=$('live-overlay-label');if(label)label.hidden=!alerts.length;
  for(const a of alerts){
    const point=L.circleMarker([a.latitude,a.longitude],{
      radius:8,color:'#fff0d7',fillColor:'#f97953',weight:2,fillOpacity:.91
    });
    point.bindPopup(`<strong>Near-real-time potential hotspot</strong><br>${escapeHTML(a.date)} · ${fmt(a.n_observations)} observations<br>${escapeHTML(formatStamp(a.last_satellite_observation_utc))}<br><small>Not a verified individual wildfire or known ignition time.</small>`);
    point.addTo(state.liveLayers);
  }
}
function renderLiveWatch(d){
  const target=$('live-watch');const time=$('watch-check-time');
  updateLiveMap((d.status==='ok'||d.status==='partial')?d.alerts||[]:[]);
  if(d.status==='not_configured'){
    setWatchBadge('KEY NEEDED','offline');target.innerHTML='<div class="watch-placeholder">Live data is <strong>not connected</strong>. Set <code>FIRMS_MAP_KEY</code> in your local <code>.env</code> and restart the server. No result here means <strong>not checked</strong>, not no fires.</div>';
    time.textContent='Historical Alberta 2023 analysis works without a NASA key. Live status is NOT a verified wildfire or emergency service.';
    return;
  }
  if(d.status==='unavailable'){
    setWatchBadge('FEED UNAVAILABLE','offline');target.innerHTML='<div class="watch-placeholder">NASA near-real-time feeds could not be checked. This does not establish an absence of fires. Verify with your regional wildfire authority.</div>';
    time.textContent=`Attempted ${formatStamp(d.checked_at_utc)}. No verified incident or publishing-delay evidence.`;
    return;
  }
  setWatchBadge(d.status==='partial'?'PARTIAL FEED':'FEED CHECKED',d.status==='partial'?'offline':'live');
  const all=d.alerts||[];
  const known=new Set(all.map(a=>a.id));
  if(notifiedBaseline && localStorage.getItem('blindspot-notify')==='true' && 'Notification' in window && Notification.permission==='granted'){
    const fresh=all.filter(a=>!notifiedBaseline.has(a.id));
    if(fresh.length){new Notification('BLINDSPOT · new satellite signal',{body:`${fresh.length} newly observed grid-day hotspot groups near ${$('region').selectedOptions[0].text}. Confirm with official fire services.`});}
  }
  notifiedBaseline=known;
  if(!all.length){target.innerHTML='<div class="watch-placeholder">No presumed vegetation hotspot detections returned in the latest 48-hour feed checked. <strong>This does not prove there are no active wildfires.</strong></div>';}else{
    target.innerHTML=all.slice(0,3).map(a=>`<div class="watch-alert live-alert"><div class="signal-emoji">✦</div><div><strong>Potential hotspot signal · ${escapeHTML(a.date)}</strong><span>${fmt(a.n_observations)} satellite detections near ${a.latitude.toFixed(2)}°, ${a.longitude.toFixed(2)}°. Last satellite observation ${formatDuration(a.minutes_since_last_observation)} ago.</span><small>First satellite observation: ${escapeHTML(formatStamp(a.first_satellite_observation_utc))}</small><small>BLINDSPOT first fetched: ${escapeHTML(formatStamp(a.first_blindspot_check_utc))} · observation-to-first-site-check gap ${formatDuration(a.minutes_observation_to_first_check)} (NOT official reporting latency)</small></div></div>`).join('')+
      (all.length>3?`<div class="watch-disclosure">Showing 3 of ${fmt(d.total_potential_hotspot_clusters)} grid-day signal groups. These are thermal anomalies, not verified fire incidents.</div>`:'');
  }
  time.textContent=`Last checked ${formatStamp(d.checked_at_utc)} · ${d.source_products.join(' + ')} · 48-hour lookback. ${d.failed_sources?.length?'One source unavailable. ':''}Page must remain open for browser notifications. Ignition and official report times are unknown.`;
}
async function checkLiveWatch(){
  const button=$('watch-refresh');button.disabled=true;button.textContent='Checking NASA…';
  try{
    const result=await api('/api/watch/live?region='+encodeURIComponent($('region').value));
    renderLiveWatch(result);
  }catch(error){setWatchBadge('CHECK FAILED','offline');$('live-watch').textContent='Live feed check failed: '+error.message+'. No current wildfire status can be inferred.';}
  finally{button.disabled=false;button.textContent='↻ Check latest detections';}
}
async function optInWatch(){
  if(localStorage.getItem('blindspot-notify')==='true'){
    localStorage.setItem('blindspot-notify','false');updateWatchNotifyButton();toast('Browser alerts turned off.');return;
  }
  if(!state.config?.firms_key_configured){toast('Set FIRMS_MAP_KEY in .env first to enable actual NASA live checks.');return;}
  if(!('Notification' in window)){toast('This browser does not support notifications.');return;}
  const permission=await Notification.requestPermission();
  if(permission==='granted'){
    localStorage.setItem('blindspot-notify','true');updateWatchNotifyButton();toast('Opted in while this tab is open. Checking the feed…');await checkLiveWatch();
  }else{toast('Browser notification permission not granted.');}
}
function updateWatchNotifyButton(){const on=localStorage.getItem('blindspot-notify')==='true';$('watch-notify').textContent=on?'✓ Browser alerts: on':'♢ Browser alerts: off';}

/* Independent Canadian context — do not blend agency incidents into NASA hotspot totals. */
const canadaLayers={agency:null,active:null,fwi:null,agencyData:null,showAgency:false};
const CWFIS_WMS='https://geoserver.cwfif.nrcan.gc.ca/geoserver/ows';
const CWFIS_LEGACY_WMS='https://cwfis.cfs.nrcan.gc.ca/geoserver/public/wms';
function showCanadaNote(message){const el=$('agency-message');if(el)el.textContent=message;}
function renderAgencyMarkers(){
  if(!state.leaflet||!state.map)return;
  if(!canadaLayers.agency)canadaLayers.agency=L.layerGroup();
  canadaLayers.agency.clearLayers();
  if(!canadaLayers.showAgency||canadaLayers.agencyData?.status!=='loaded'){
    if(state.map.hasLayer(canadaLayers.agency))state.map.removeLayer(canadaLayers.agency);
    return;
  }
  for(const f of canadaLayers.agencyData.points||[]){
    const label=`<b>Agency-recorded wildfire · ${escapeHTML(f.fire_id)}</b><br>Cause: ${escapeHTML(f.cause||'Unknown')}<br>Recorded area: ${f.area_ha===null?'Not reported':escapeHTML(f.area_ha)+' ha'}<br>Agency discovery: ${escapeHTML(f.discovered||'Not recorded')}<br>Agency report: ${escapeHTML(f.reported||'Not recorded')}<br><small>Government of Alberta historical incident — NOT NASA FIRMS; location is the reported origin, not a satellite match.</small>`;
    L.circleMarker([f.latitude,f.longitude],{radius:5,color:'#7bf3cc',fillColor:'#17a77d',fillOpacity:.78,weight:1.2})
      .bindPopup(label,{maxWidth:315}).addTo(canadaLayers.agency);
  }
  if(!state.map.hasLayer(canadaLayers.agency))canadaLayers.agency.addTo(state.map);
}
function renderAgencyContext(data){
  canadaLayers.agencyData=data;
  const has=data.status==='loaded';
  $('agency-badge').textContent=has?'AGENCY RECORDS LOADED':'AGENCY DATA · NOT IMPORTED';
  $('agency-badge').classList.toggle('loaded',has);
  $('agency-count').textContent=has?fmt(data.count):'—';
  $('agency-count-label').textContent=has?`Official recorded fires in ${data.year}, not hotspots`:'Official fire records · import to explore';
  $('agency-map').disabled=!has||!state.leaflet;
  $('agency-message').textContent=data.note;
  const grid=$('agency-months');
  grid.replaceChildren();
  if(!has){grid.innerHTML='<span class="agency-empty">Import the official CSV to see independent monthly wildfire report counts here.</span>';}
  else{
    const max=Math.max(1,...data.monthly.map(x=>x.count));
    for(const t of data.monthly){
      const col=document.createElement('div');col.className='agency-month-col';
      col.title=`${t.month}: ${fmt(t.count)} agency records (discovery / reported / start date as available)`;
      col.innerHTML=`<span class="bar" style="height:${Math.max(2,(t.count/max)*63)}px"></span><em>${months[Number(t.month.slice(5))-1].slice(0,1)}</em>`;
      grid.append(col);
    }
  }
  $('agency-causes').innerHTML=has?data.cause_counts.map(c=>`<span>${escapeHTML(c.cause)} · ${fmt(c.count)}</span>`).join(''):'';
  const lag=data.discovery_to_report;
  $('agency-lag').textContent=lag?.median_minutes!==null&&lag?.median_minutes!==undefined?`${fmt(Math.round(lag.median_minutes))} min median`:'No comparable timestamps';
  $('agency-lag-note').textContent=has&&lag?.sample_size?`Across ${fmt(lag.sample_size)} agency cases with valid timestamps. Agency discovery → agency reporting; NOT NASA detection or website-posting time.`:'Alberta fields discovered_date and reported_date, when available. No estimate or false zero.';
  if(!has){canadaLayers.showAgency=false;$('agency-map').textContent='◉ Show agency locations';}
  renderAgencyMarkers();
}
async function refreshAgencyContext(){
  const year=Number($('start-date').value.slice(0,4))||2023;
  try{renderAgencyContext(await api('/api/context/alberta?year='+encodeURIComponent(year)));}
  catch(e){renderAgencyContext({status:'not_imported',year,note:'Alberta historical service unavailable: '+e.message});}
}
async function uploadAgencyFile(){
  const file=$('agency-file').files[0];if(!file)return;
  if(file.size>50_000_000){showCanadaNote('The official CSV exceeds 50 MB. Use the scripts/import_alberta_history.py command instead.');return;}
  showCanadaNote('Reading official fire history… NASA satellite data will remain unchanged.');
  try{
    const token=$('admin-token').value;
    const r=await api('/api/context/alberta/import-csv',{method:'POST',headers:{'Content-Type':'text/csv','X-Admin-Token':token},body:file});
    showCanadaNote(`Imported/updated ${fmt(r.accepted_or_updated)} official agency rows; ${fmt(r.invalid_or_skipped)} skipped. Records remain separate from NASA.`);
    await refreshAgencyContext();
    toast(`Alberta agency data imported: ${fmt(r.accepted_or_updated)} records accepted/updated.`);
  }catch(e){showCanadaNote('Import failed: '+e.message+' · The satellite analysis remains available.');}
  finally{$('agency-file').value='';}
}
function toggleAgencyOverlay(){
  if(canadaLayers.agencyData?.status!=='loaded')return;
  canadaLayers.showAgency=!canadaLayers.showAgency;
  $('agency-map').textContent=canadaLayers.showAgency?'✓ Hide agency locations':'◉ Show agency locations';
  renderAgencyMarkers();
  toast(canadaLayers.showAgency?'Green points = reported agency wildfire origin, not satellite hotspots.':'Agency locations hidden.');
}
function toggleCWLayer(which){
  const btn=$(which==='active'?'cw-active':'cw-fwi');
  if(!state.leaflet||!state.map){$('cwfis-message').textContent='Map library unavailable; visit the official CWFIS link instead.';return;}
  if(canadaLayers[which]){
    state.map.removeLayer(canadaLayers[which]);canadaLayers[which]=null;
    btn.setAttribute('aria-pressed','false');btn.classList.remove('is-active');btn.textContent='Show';
    $('cwfis-message').textContent='Layer removed. Historical 2023 NASA observations remain unchanged.';return;
  }
  // Canada WMS is a live, independently managed service. Failure MUST remain visible.
  const active=which==='active';
  const wms=L.tileLayer.wms(active?CWFIS_WMS:CWFIS_LEGACY_WMS,{
    layers:active?'public:cwfif_national_activefires':'public:fwi',
    format:'image/png',transparent:true,version:'1.1.1',opacity:active?.78:.5,
    attribution:'Current public data &copy; Natural Resources Canada / CWFIS',
  });
  let sawTile=false;
  wms.on('tileload',()=>{sawTile=true;});
  wms.on('tileerror',()=>{
    $('cwfis-message').textContent='CWFIS map tiles failed to load. This does NOT mean no fires or low danger; use the official CWFIS site. Other app layers still work.';
  });
  canadaLayers[which]=wms;
  wms.addTo(state.map);
  btn.classList.add('is-active');btn.setAttribute('aria-pressed','true');btn.textContent='Hide';
  $('cwfis-message').textContent=`CURRENT ${active?'agency-reported fire':'fire weather index'} overlay selected. This is not ${$('start-date').value.slice(0,4)} historical data, may be approximate, and is unrelated to the displayed NASA dates.`;
}

// Global Atlas is separate from the harmonized historical MODIS/VIIRS calendar.
// It previews recent NASA FIRMS data and never inserts NRT points into historical totals.
let atlasLatest=null;
async function refreshAtlasInventory(region){
  const title=$('atlas-coverage-title'), note=$('atlas-coverage-desc');
  title.textContent='Checking geographic evidence coverage…';
  try{
    const inv=await api('/api/global/coverage?region='+encodeURIComponent(region));
    $('atlas-history-total').textContent=fmt(inv.total_records);
    $('atlas-history-types').textContent=inv.records.length?inv.records.map(x=>`${x.product}: ${fmt(x.count)}`).join(' · '):'No NASA historical records have been imported for this region';
    title.textContent=region==='world'?'Worldwide explorer · Alberta source archive only':inv.total_records?'Historical observations currently held':'Historical archive not yet imported';
    note.textContent=inv.note;
    $('atlas-live-pill').textContent=region==='world'?'NOT GLOBAL HISTORICAL COVERAGE':'REGION SELECTED';
  }catch(e){title.textContent='Unable to verify archive coverage';note.textContent=e.message;}
}
function drawAtlasRecent(result){
  if(!state.leaflet||!state.map)return;
  if(!state.atlasLayers)state.atlasLayers=L.layerGroup().addTo(state.map);
  state.atlasLayers.clearLayers();
  for(const p of result.points||[]){
    const label=`<b>NASA ${escapeHTML(p.source)}</b><br>${escapeHTML(p.date)} UTC ${escapeHTML(p.acq_time)}<br>Lat ${p.lat}, Lon ${p.lon}<br><small>NRT thermal signal · NOT verified fire.</small>`;
    L.circleMarker([p.lat,p.lon],{radius:4.2,color:'#75f7c3',fillColor:'#29dea7',fillOpacity:.75,weight:1})
      .bindPopup(label,{maxWidth:240}).addTo(state.atlasLayers);
  }
  if(state.globe){
    const pts=(result.points||[]).map(p=>({latitude:p.lat,longitude:p.lon,date:p.date,family:p.source.startsWith('MODIS')?'MODIS':'VIIRS',recent:true}));
    state.globe.pointsData(pts);
  }
}
async function checkGlobalFeed(){
  const region=$('atlas-region').value,source=$('atlas-source').value,days=Number($('atlas-days').value);
  const btn=$('atlas-check');btn.disabled=true;btn.textContent='Contacting NASA…';
  $('atlas-check-status').textContent='Checking NASA FIRMS NRT feed; this is not an emergency alert.';
  try{
    const d=await api('/api/global/latest?'+new URLSearchParams({region,source,days:String(days)}));
    if(d.status==='not_configured'){
      $('atlas-recent-total').textContent='Key needed';$('atlas-recent-source').textContent='FIRMS_MAP_KEY in .env';
      $('atlas-check-status').textContent=d.note;return;
    }
    atlasLatest=d;
    $('atlas-recent-total').textContent=fmt(d.presumed_vegetation_rows);
    $('atlas-recent-source').textContent=`${source} · ${d.days} day(s) · ${fmt(d.sampled_points)} mapped of ${fmt(d.presumed_vegetation_rows)} presumed-vegetation observations`;
    $('atlas-check-status').textContent=`NASA query ${d.queried_at_utc}. ${d.note}`;
    drawAtlasRecent(d);
    if(state.map && d.region==='world')state.map.setView([12,0],2);
    toast('NASA recent data preview loaded separately; 2023 historical metrics unchanged.');
  }catch(e){$('atlas-recent-total').textContent='Unavailable';$('atlas-check-status').textContent='NASA check failed: '+e.message+' · Do not infer zero active fires.';}
  finally{btn.disabled=false;btn.textContent='✦ Check NASA now';}
}
function changeAtlasRegion(){
  const region=$('atlas-region').value;
  $('region').value=region;
  // The World FIRMS endpoint supports only one day to reduce resource load.
  if(region==='world')$('atlas-days').value='1';
  if(state.atlasLayers)state.atlasLayers.clearLayers();
  if(state.analysis && state.globe)renderGlobePoints(state.analysis);
  $('atlas-recent-total').textContent='Not checked';
  $('atlas-recent-source').textContent='Choose fire source, then Check NASA now';
  refreshAtlasInventory(region);
}
window.addEventListener('DOMContentLoaded',async()=>{
  setTheme(localStorage.getItem('blindspot-theme')==='light'?'light':'dark');
  $('theme-button').addEventListener('click',()=>setTheme(document.body.dataset.theme==='dark'?'light':'dark'));
  $('analyze-button').addEventListener('click',load);
  $('atlas-region').addEventListener('change',changeAtlasRegion);
  $('atlas-check').addEventListener('click',checkGlobalFeed);
  $('atlas-view').addEventListener('click',()=>{changeAtlasRegion();load();$('reveal').scrollIntoView({behavior:'smooth',block:'start'});});
  $('mode').addEventListener('change',load);
  $('region').addEventListener('change',()=>{$('atlas-region').value=$('region').value;if(state.atlasLayers)state.atlasLayers.clearLayers();$('atlas-recent-total').textContent='Not checked';$('atlas-recent-source').textContent='Choose fire source, then Check NASA now';refreshAtlasInventory($('region').value);updateLiveMap([]);notifiedBaseline=null;setWatchBadge('NOT CHECKED');$('live-watch').innerHTML='<div class="watch-placeholder">Area changed. Click Check latest detections for this region.</div>';});
  $('clear-selection').addEventListener('click',()=>selectMonth(null));
  document.querySelectorAll('[data-layer]').forEach(b=>b.addEventListener('click',()=>{state.layer=b.dataset.layer;document.querySelectorAll('[data-layer]').forEach(x=>x.classList.toggle('selected',x===b));renderMap();}));
  $('export-brief').addEventListener('click',()=>download('brief.md'));
  $('export-csv').addEventListener('click',()=>download('monthly.csv'));
  $('data-studio-open').addEventListener('click',()=>{refreshConfig();$('modal').classList.remove('hidden');});
  $('modal-close').addEventListener('click',()=>$('modal').classList.add('hidden'));
  $('modal').addEventListener('click',e=>{if(e.target===$('modal'))$('modal').classList.add('hidden');});
  document.addEventListener('keydown',e=>{if(e.key==='Escape')$('modal').classList.add('hidden');});
  $('ingest-button').addEventListener('click',ingest);
  $('upload-button').addEventListener('click',upload);
  state.mapStyle=['illustrated','watch','auto','dark','light','satellite','hybrid'].includes(localStorage.getItem('blindspot-map-style'))?localStorage.getItem('blindspot-map-style'):'illustrated';
  state.mapLabels=localStorage.getItem('blindspot-map-labels')!=='false';
  state.mapGlow=localStorage.getItem('blindspot-map-glow')!=='false';
  $('map-style').value=state.mapStyle;
  $('map-style').addEventListener('change',e=>changeMapStyle(e.target.value));
  $('map-reset').addEventListener('click',resetMapView);
  $('map-labels').addEventListener('click',toggleMapLabels);
  $('map-glow').addEventListener('click',toggleMapGlow);
  $('save-map-key').addEventListener('click',saveMapKey);
  $('clear-map-key').addEventListener('click',clearMapKey);
  $('watch-refresh').addEventListener('click',checkLiveWatch);
  $('watch-notify').addEventListener('click',optInWatch);
  updateWatchNotifyButton();
  $('agency-file').addEventListener('change',uploadAgencyFile);
  $('agency-map').addEventListener('click',toggleAgencyOverlay);
  $('cw-active').addEventListener('click',()=>toggleCWLayer('active'));
  $('cw-fwi').addEventListener('click',()=>toggleCWLayer('fwi'));
  initMap();bootGlobe();await refreshConfig();
  // Showcase the bundled *real* archive rather than landing judges on synthetic demo.
  const realCount=(state.config?.counts||[]).filter(x=>x.mode==='real').reduce((sum,x)=>sum+x.count,0);
  if(realCount>0 && state.config?.regions?.alberta_province){
    $('region').value='alberta_province';$('mode').value='real';
    $('start-date').value='2023-05-01';$('end-date').value='2023-10-31';
    $('hero-data-count').textContent=`${fmt(realCount)} archived detections · Alberta 2023`;
  }else{$('hero-data-count').textContent='Data connection needed';}
  await load();
  $('atlas-region').value=$('region').value;await refreshAtlasInventory($('region').value);
  await refreshAgencyContext();
  // Browser notification checks are opt-in, and only work while the page remains open.
  setInterval(()=>{if(localStorage.getItem('blindspot-notify')==='true'&&state.config?.firms_key_configured)checkLiveWatch();},15*60*1000);
});
