'use strict';
/* Original Parallax BLINDSPOT Investigation Theatre.
   Grounded exclusively in the local /api/investigation response, not imagery
   or other teams' code. Never converts hotspot co-occurrence into accuracy. */
(() => {
  const el = id => document.getElementById(id);
  const pretty = n => n == null ? '—' : Number(n).toLocaleString('en-CA');
  const q = { current: null, left: null, right: null, leftMarkers: null, rightMarkers: null,
    revealed: false, pct: 50, sync: false, basemapStyle: 'illustrated', basemapLayers: [], labelLayers: [], ctrl: null, request: 0, fallback: false, drawMode: false, drawStart: null, drawRect: null };
  const colors = { modis: '#ffac73', viirs: '#ba9bff', both: '#68dfbd' };

  function setText(id, value) { if (el(id)) el(id).textContent = value; }
  function loading(on) { el('reveal-loading').hidden = !on; }
  function updateSplit(percent) {
    q.pct = Math.max(4, Math.min(96, Number(percent)));
    el('reveal-slider').value = String(q.pct);
    el('reveal-right-mask').style.clipPath = `inset(0 0 0 ${q.pct}%)`;
    el('reveal-divider').style.left = `${q.pct}%`;
    el('reveal-divider').setAttribute('aria-valuenow', Math.round(q.pct));
    setText('reveal-percent', `${Math.round(q.pct)} / ${100-Math.round(q.pct)}`);
  }
  function initComparisonMaps() {
    if (!window.L) {
      el('reveal-map-fallback').hidden = false;
      setText('reveal-map-fallback','Leaflet could not load. The counts and conclusions remain available.');
      return;
    }
    const options = {center:[54.3,-115],zoom:5,preferCanvas:true,zoomControl:false,
       attributionControl:false,scrollWheelZoom:false,worldCopyJump:false};
    q.left = L.map('reveal-left-map',options);
    q.right = L.map('reveal-right-map',{...options,dragging:false,scrollWheelZoom:false,
      touchZoom:false,doubleClickZoom:false,boxZoom:false,keyboard:false});
    updateComparisonBasemap('illustrated');
    q.leftMarkers=L.layerGroup().addTo(q.left);
    q.rightMarkers=L.layerGroup().addTo(q.right);
    q.left.on('moveend zoomend',()=>{
      if(q.sync)return;
      q.sync=true;
      q.right.setView(q.left.getCenter(),q.left.getZoom(),{animate:false});
      q.sync=false;
    });
    L.control.zoom({position:'bottomright'}).addTo(q.left);
    L.control.attribution({position:'bottomleft',prefix:false}).addTo(q.left)
      .addAttribution('Esri imagery / reference labels · NASA FIRMS observations');
    window.addEventListener('resize',()=>{
      q.left?.invalidateSize({pan:false});q.right?.invalidateSize({pan:false});
    });
  }
  function updateComparisonBasemap(style){
    q.basemapStyle=style;
    for(const layer of q.basemapLayers){ if(layer.map.hasLayer(layer.tile))layer.map.removeLayer(layer.tile); }
    for(const layer of q.labelLayers){ if(layer.map.hasLayer(layer.tile))layer.map.removeLayer(layer.tile); }
    q.basemapLayers=[];q.labelLayers=[];
    const satellite=style==='satellite';
    const source=satellite
      ?'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}'
      :'https://tile.openstreetmap.org/{z}/{x}/{y}.png';
    for(const map of [q.left,q.right]){
      const tile=L.tileLayer(source,{
        maxZoom:18,className:satellite?'':'reveal-atlas-tile',
        attribution:satellite?'Esri World Imagery':'© OpenStreetMap contributors'
      }).addTo(map);
      q.basemapLayers.push({map,tile});
      if(satellite){
        const labels=L.tileLayer('https://services.arcgisonline.com/ArcGIS/rest/services/Reference/World_Boundaries_and_Places/MapServer/tile/{z}/{y}/{x}',
          {maxZoom:18,opacity:.8,attribution:'Esri Reference'}).addTo(map);
        q.labelLayers.push({map,tile:labels});
        labels.on('tileerror',()=>{if(map.hasLayer(labels))map.removeLayer(labels);});
      }
      tile.on('tileerror',()=>{
        if(style==='satellite'&&q.basemapStyle==='satellite'){
          el('reveal-map-style').value='illustrated';updateComparisonBasemap('illustrated');
          setText('reveal-map-fallback','Satellite imagery unavailable; using the accurate OpenStreetMap illustrated style.');
          el('reveal-map-fallback').hidden=false;
          setTimeout(()=>{el('reveal-map-fallback').hidden=true;},3600);
        }
      });
    }
  }
  function marker(map,grp,c,color,days,label) {
    const rad = Math.min(15, 3.3 + 2.15*Math.sqrt(days));
    const mark=L.circleMarker([c.lat,c.lon],{radius:rad,color,
      fillColor:color,fillOpacity:.56,opacity:.9,weight:1.1});
    mark.bindPopup(`<div class="reveal-popup"><b>${label}</b><p>Projected 10-km cell · representative centre</p>
      <strong>${pretty(c.union)} union active grid-days</strong>
      <div>MODIS-only: ${pretty(c.modis_only)}<br>VIIRS-only: ${pretty(c.viirs_only)}<br>Both: ${pretty(c.both)}</div>
      <small>Cell-day co-occurrence does not establish that sensors saw the same fire.</small></div>`);
    grp.addLayer(mark);
  }
  function drawMarkers() {
    if(!q.current || !q.left || !q.right)return;
    q.leftMarkers.clearLayers();q.rightMarkers.clearLayers();
    for (const c of q.current.cells) {
      if(q.revealed) {
        const kind = c.both>=c.viirs_only && c.both>=c.modis_only ? 'both' :
                     c.viirs_only>=c.modis_only ? 'viirs' : 'modis';
        marker(q.left,q.leftMarkers,c,colors[kind],c.union,
          kind==='both'?'Shared grid-day evidence':kind==='viirs'?'VIIRS-exclusive activity dominates':'MODIS-exclusive activity dominates');
      } else {
        if(c.modis)marker(q.left,q.leftMarkers,c,colors.modis,c.modis,'MODIS observation presence');
        if(c.viirs)marker(q.right,q.rightMarkers,c,colors.viirs,c.viirs,'VIIRS observation presence');
      }
    }
    el('reveal-interactive').classList.toggle('is-revealed',q.revealed);
    setText('reveal-label-left',q.revealed?'BLINDSPOT MAP · OBSERVATION RELATIONSHIPS':'MODIS · 1 KM');
    setText('reveal-label-right',q.revealed?'':'VIIRS · 375 M');
    setText('reveal-map-note',q.revealed?'Orange: MODIS-dominant · Lavender: VIIRS-dominant · Mint: shared-dominant':'Slide to compare MODIS and VIIRS historical satellite records');
    if(q.revealed)el('reveal-right-mask').style.clipPath='inset(0 0 0 100%)';
    else updateSplit(q.pct);
  }
  function setRevealed(on) {
    q.revealed=on;
    const btn=el('reveal-action');
    btn.setAttribute('aria-pressed',String(on));
    btn.textContent=on?'↩ RETURN TO SENSOR WIPE':'✦ REVEAL BLINDSPOTS';
    el('reveal-slider').disabled=on;
    el('reveal-divider').hidden=on;
    drawMarkers();
  }
  function renderNumbers(d) {
    const t=d.totals;
    setText('reveal-modis',pretty(t.modis_only));
    setText('reveal-viirs',pretty(t.viirs_only));
    setText('reveal-both',pretty(t.both));
    setText('reveal-overlap',d.overlap_pct===null?'—':`${d.overlap_pct}%`);
    setText('reveal-cell-count',`${pretty(d.total_cells)} distinct spatial grid cells · ${pretty(d.displayed_cells)} shown`);
    const total=t.union||1;
    el('reveal-bar-modis').style.width=(100*t.modis_only/total)+'%';
    el('reveal-bar-both').style.width=(100*t.both/total)+'%';
    el('reveal-bar-viirs').style.width=(100*t.viirs_only/total)+'%';
    const period=d.selected_month||`${d.start} → ${d.end}`;
    setText('reveal-impact-title',`${period} · ${pretty(t.union)} active grid-days`);
    setText('reveal-insight', t.union ?
      `${pretty(t.viirs_only)} grid-days had VIIRS detections without a MODIS record in the same projected cell/day. That is an observable mismatch worth investigating—not a count of missed wildfires. The calendar and mission brief use the full selected period, not the ${pretty(d.displayed_cells)} displayed cells.`:
      'No eligible detections found in this selected window. Check archive coverage before treating this as an absence of fire.');
  }
  function renderEvidence(d) {
    const quality=d.quality;
    setText('detective-filter-count', `${pretty(quality.included_in_analysis)} eligible observations · ${pretty(quality.excluded_other_types)} classified thermal anomalies excluded`);
    setText('detective-filter-note',`${pretty(quality.raw_records)} original rows for the selected period. ${pretty(quality.presumed_vegetation)} are NASA type 0 (presumed vegetation); ${pretty(quality.unclassified)} have no classification. Type 0 does not confirm a real wildfire.`);
    const years=d.historical_years||[];
    setText('detective-years',years.length?`${years.length} ${years.length===1?'season':'seasons'}`:'NO BASELINE');
    const anomalies=(d.anomalies||[]).filter(a=>a.status==='comparable');
    if(anomalies.length){
      const strong=anomalies.filter(x=>x.change_pct!==null).sort((a,b)=>Math.abs(b.change_pct)-Math.abs(a.change_pct))[0];
      setText('detective-anomaly',strong?
        `${strong.month}: ${pretty(strong.observed)} observed grid-days versus ${pretty(strong.baseline_median)} median in ${strong.comparison_years} other covered seasons (${strong.change_pct>0?'+':''}${strong.change_pct}%). Descriptive, not forecast.`:
        'Historical peers are available, but baseline values are zero for the selected month.');
      const samples=anomalies.slice(-8);const max=Math.max(...samples.map(x=>x.observed),1);
      el('detective-anomaly-bars').innerHTML=samples.map(x=>`<div title="${x.month} · ${x.observed}"><i style="height:${Math.max(5,x.observed/max*100)}%"></i><small>${x.month.slice(2)}</small></div>`).join('');
    } else {
      setText('detective-anomaly',`${years.length} fully covered overlapping year${years.length===1?'':'s'} available: ${years.join(', ')||'none'}. A credible anomaly needs the same month in at least three *other* archived years. We will not call 2023 “unusual” without that reference.`);
      el('detective-anomaly-bars').innerHTML='<div class="detective-empty-chart">+ Add multi-year NASA archives to unlock the historical baseline</div>';
    }
    const v=d.calibration;
    if(v.status==='experimental_holdout') {
      setText('detective-calibration',`${v.multiplier}×`);
      setText('detective-calibration-note',`A preliminary sensor-rate scale fit on ${v.train_years.join(', ')} was evaluated on unseen ${v.heldout_year} data. Holdout WAPE: raw ${v.heldout_wape_raw_pct}% → scaled ${v.heldout_wape_scaled_pct}%. Not an orbital or cloud correction.`);
      setText('detective-calibration-pill',`EXPERIMENTAL HOLDOUT · ${v.heldout_year}`);
    } else {
      setText('detective-calibration','NOT VALIDATED');
      setText('detective-calibration-note',`Aligned observations are not calibrated sensor sensitivities. Historical calibration needs ≥3 overlapping full years for a holdout test. ${v.years_available?.length||0} currently available.`);
      setText('detective-calibration-pill','No invented calibration factor or confidence interval');
    }
  }
  async function agencyCheck(year) {
    try {
      const r=await fetch(`/api/investigation/agency-match?year=${encodeURIComponent(year)}`);
      if(!r.ok) throw new Error(`HTTP ${r.status}`);
      const a=await r.json();
      if(a.status!=='loaded') {
        setText('detective-agency','NOT IMPORTED');
        setText('detective-agency-note','Alberta’s official incident CSV is not in the local database. Import it in Canada Evidence Lab to run real spatial/date coincidence checks. No matching percentage is claimed yet.');
      } else {
        setText('detective-agency',`${pretty(a.nearby_satellite_cell_days)} / ${pretty(a.with_dates)}`);
        setText('detective-agency-note',`${a.nearby_satellite_cell_days} agency incidents with dated records had a NASA hotspot grid-day nearby (±3 days, ~20 km). This is a spatial/date coincidence, NOT proof of the same fire. ${a.missing_dates} agency records lacked usable dates.`);
      }
    } catch(e) {
      setText('detective-agency','UNAVAILABLE');
      setText('detective-agency-note',`Official source comparison currently unavailable (${e.message}).`);
    }
  }
  async function refresh(month='') {
    const request=++q.request;
    if(q.ctrl)q.ctrl.abort();
    q.ctrl=new AbortController();
    loading(true);
    setText('reveal-map-note','Loading spatial grid-day evidence…');
    const params=new URLSearchParams({region:el('region').value,start:el('start-date').value,
      end:el('end-date').value,mode:el('mode').value});
    if(window.BLINDSPOT_BBOX)params.set('bbox',window.BLINDSPOT_BBOX.join(','));
    if(month)params.set('month',month);
    try {
      const response=await fetch(`/api/investigation?${params}`,{signal:q.ctrl.signal});
      if(!response.ok)throw new Error(`HTTP ${response.status}`);
      const d=await response.json();
      if(request!==q.request)return;
      q.current=d;
      renderNumbers(d);renderEvidence(d);
      drawMarkers();
      if(q.left) {
        const key=el('region').value;
        const bounds=state?.analysis?.region?.bbox;
        if(bounds) {
          const newKey=`${key}:${el('start-date').value}:${el('end-date').value}:${window.BLINDSPOT_BBOX?.join(',')||''}`;
          if(q.lastKey!==newKey) {
            q.lastKey=newKey;
            q.left.fitBounds([[bounds[1],bounds[0]],[bounds[3],bounds[2]]],
                {padding:[16,16],maxZoom:8,animate:false});
          }
        }
      }
      const year=Number((month||el('start-date').value).slice(0,4));
      if(!q.agencyYear || q.agencyYear!==year){q.agencyYear=year;agencyCheck(year);}
    } catch(e) {
      if(e.name==='AbortError')return;
      setText('reveal-insight',`Investigation unavailable: ${e.message}. The original calendar remains usable.`);
      setText('reveal-map-note','Investigation API unavailable');
    } finally {if(request===q.request)loading(false);}
  }
  function populateMonths(d) {
    const select=el('reveal-month');
    select.replaceChildren(new Option('Entire selected season',''));
    for(const row of d.timeline) {
      const period=row.month;
      const monthName=new Date(period+'-02T12:00:00Z').toLocaleString('en-CA',{month:'short',year:'numeric',timeZone:'UTC'});
      select.add(new Option(`${monthName} · ${pretty(row.combined)} grid-days`,period));
    }
    select.value='';
  }
  function startFocusDraw() {
    if(!q.left){setText('reveal-focus-status','Leaflet map is unavailable: custom area drawing needs map tiles.');return;}
    q.drawMode=!q.drawMode;
    q.drawStart=null;
    el('reveal-draw').classList.toggle('is-active',q.drawMode);
    if(q.drawMode){
      q.left.dragging.disable();
      el('reveal-left-map').style.cursor='crosshair';
      setText('reveal-focus-status','DRAW MODE: Click the first corner, then click the opposite corner.');
    }else{
      q.left.dragging.enable();
      el('reveal-left-map').style.cursor='';
      setText('reveal-focus-status','Drawing cancelled. Your previous selection remains active.');
    }
  }
  function chooseFocusPoint(event) {
    if(!q.drawMode)return;
    if(!q.drawStart){
      q.drawStart=event.latlng;
      if(q.drawRect)q.left.removeLayer(q.drawRect);
      q.drawRect=L.rectangle([q.drawStart,q.drawStart],{color:'#a3f0d9',weight:2,dashArray:'6 5',fillOpacity:.13}).addTo(q.left);
      setText('reveal-focus-status','Click the opposite corner to complete the focus rectangle.');
      return;
    }
    const b=state?.config?.regions?.[el('region').value]?.bbox ||
        state?.analysis?.region?.bbox;
    if(!b){setText('reveal-focus-status','Region boundaries not available.');return;}
    const start=q.drawStart,end=event.latlng;
    const west=Math.max(b[0],Math.min(start.lng,end.lng));
    const east=Math.min(b[2],Math.max(start.lng,end.lng));
    const south=Math.max(b[1],Math.min(start.lat,end.lat));
    const north=Math.min(b[3],Math.max(start.lat,end.lat));
    if(east-west<.08 || north-south<.08){
      setText('reveal-focus-status','Selection is too small. Choose a rectangle at least 0.08° wide and tall.');return;
    }
    window.BLINDSPOT_BBOX=[west,south,east,north].map(x=>+x.toFixed(5));
    q.drawRect.setBounds([[south,west],[north,east]]);
    q.drawMode=false;q.drawStart=null;
    q.left.dragging.enable();
    el('reveal-left-map').style.cursor='';
    el('reveal-draw').classList.remove('is-active');
    setText('reveal-focus-status',`CUSTOM FOCUS: ${west.toFixed(2)}, ${south.toFixed(2)} → ${east.toFixed(2)}, ${north.toFixed(2)} · Calendar, comparison and brief now use this area.`);
    if(window.load)load();
  }
  function resetFocus() {
    window.BLINDSPOT_BBOX=null;
    q.drawMode=false;q.drawStart=null;
    if(q.drawRect&&q.left){q.left.removeLayer(q.drawRect);q.drawRect=null;q.left.dragging.enable();}
    el('reveal-draw').classList.remove('is-active');
    el('reveal-left-map').style.cursor='';
    setText('reveal-focus-status','Full region restored. Draw a rectangle for a custom analysis.');
    if(window.load)load();
  }
  function init() {
    initComparisonMaps();updateSplit(50);
    el('reveal-map-style').addEventListener('change',ev=>updateComparisonBasemap(ev.target.value));
    el('reveal-draw').addEventListener('click',startFocusDraw);
    el('reveal-reset').addEventListener('click',resetFocus);
    if(q.left){
      q.left.on('click',chooseFocusPoint);
      q.left.on('mousemove',event=>{if(q.drawMode&&q.drawStart&&q.drawRect)q.drawRect.setBounds([q.drawStart,event.latlng]);});
    }
    el('region').addEventListener('change',()=>{
      if(window.BLINDSPOT_BBOX)resetFocus();
    });
    el('reveal-slider').addEventListener('input',event=>updateSplit(event.target.value));
    el('reveal-action').addEventListener('click',()=>setRevealed(!q.revealed));
    el('reveal-month').addEventListener('change',event=>{
      if(window.selectMonth)selectMonth(event.target.value||null);
      else refresh(event.target.value);
    });
    let dragging=false;
    el('reveal-divider').addEventListener('pointerdown',event=>{
      dragging=true;event.preventDefault();el('reveal-divider').setPointerCapture(event.pointerId);
    });
    el('reveal-divider').addEventListener('pointermove',event=>{
      if(!dragging)return;
      const b=el('reveal-map-window').getBoundingClientRect();
      updateSplit(100*(event.clientX-b.left)/b.width);
    });
    el('reveal-divider').addEventListener('pointerup',()=>{dragging=false;});
    el('reveal-divider').addEventListener('pointercancel',()=>{dragging=false;});
    el('reveal-divider').addEventListener('keydown',event=>{
      if(event.key==='ArrowLeft'||event.key==='ArrowRight'){
        event.preventDefault();updateSplit(q.pct+(event.key==='ArrowRight'?5:-5));
      }
    });
    window.addEventListener('blindspot:analysis-ready',event=>{
      populateMonths(event.detail);
      refresh('');
    });
    window.addEventListener('blindspot:month-selected',event=>{
      const month=event.detail.month||'';
      if([...el('reveal-month').options].some(x=>x.value===month))el('reveal-month').value=month;
      refresh(month);
    });
  }
  window.addEventListener('DOMContentLoaded',init);
})();
