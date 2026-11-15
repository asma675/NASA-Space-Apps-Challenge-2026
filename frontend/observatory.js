'use strict';
/* Original Parallax Observatory storytelling. This visual narrative contains no simulated NASA metrics. */
(() => {
  const reduce=window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  const curtain=document.querySelector('.transition-curtain');
  document.querySelectorAll('a[data-transition]').forEach(anchor=>{
    anchor.addEventListener('click',event=>{
      if(event.defaultPrevented||event.metaKey||event.ctrlKey||event.shiftKey||event.altKey||anchor.target==='_blank')return;
      const url=new URL(anchor.href,location.href);
      if(url.origin!==location.origin)return;
      event.preventDefault();
      if(reduce){location.assign(url.href);return;}
      curtain?.classList.add('is-visible');
      setTimeout(()=>location.assign(url.href),580);
    });
  });
  // Counts are read from the actual server database; never fake the metric.
  const count=document.getElementById('landing-observation-count');
  const proof=document.getElementById('landing-proof-count');
  if(count||proof){
    fetch('/api/config').then(r=>{if(!r.ok)throw Error('Offline');return r.json();}).then(d=>{
      const n=(d.counts||[]).filter(x=>x.mode==='real').reduce((s,x)=>s+Number(x.count||0),0);
      if(count)count.textContent=n?n.toLocaleString('en-CA')+' SOURCE OBSERVATIONS':'No real archive loaded';
      if(proof)proof.textContent=n?n.toLocaleString('en-CA'):'Archive not loaded';
    }).catch(()=>{if(count)count.textContent='Open Explore to verify';if(proof)proof.textContent='Archive offline';});
  }
  const title=document.getElementById('story-title');
  if(!title)return;
  const scenes=[
    {chapter:'SCENE 01 / THE PERSON',title:'Meet Maya.',deck:'A preparedness analyst with a difficult question.',body:'Maya reviews historical burning patterns before her team plans where to focus monitoring. She has a mountain of satellite observations, but a hotspot is not a verified fire—and a single map is only part of the story.',label:'HER QUESTION',evidence:'Where were the historically active periods, and how complete is the evidence?',room:'01 / AN ANALYST AT WORK'},
    {chapter:'SCENE 02 / THE INSTRUMENTS',title:'Two eyes. Two records.',deck:'MODIS and VIIRS both watch Earth—differently.',body:'MODIS offers a longer-running, coarser record. VIIRS can detect smaller thermal features. Because their observations differ, simply adding their hotspot counts together would be misleading. We first compare both on the same place-and-day grid.',label:'THE METHOD',evidence:'A 10-km projected cell on a UTC day counts once for each sensor that reported a hotspot.',room:'02 / SATELLITES DO NOT SEE IDENTICALLY'},
    {chapter:'SCENE 03 / THE REVEAL',title:'Reveal the gap.',deck:'A disagreement is a clue—not a failure verdict.',body:'The evidence desk separates MODIS-only, VIIRS-only and both-sensor cell-days. A draggable map shows the contrast. Different detections may reflect overpass timing, cloud cover, sensitivity or burning activity; missing detections are not proof a satellite missed a wildfire.',label:'THE INVESTIGATION',evidence:'Select a month. Drag the divider. Reveal mismatches. Draw a smaller study area.',room:'03 / COMPARE WHAT WAS ACTUALLY OBSERVED'},
    {chapter:'SCENE 04 / THE DECISION',title:'See beyond the dots.',deck:'Now Maya can act on evidence—with its limits visible.',body:'She investigates the most active months in Alberta’s archived 2023 season, cross-checks independent agency records where available, and exports a readiness brief. The app tells her when several historical years are missing, instead of inventing a trend or a prediction.',label:'THE NEXT STEP',evidence:'Open BLINDSPOT Explore to investigate 547,021 archived observations and their scientific caveats.',room:'04 / OPEN THE EVIDENCE DESK'}
  ];
  const byId=id=>document.getElementById(id);
  let idx=0;
  const next=byId('story-next'),prev=byId('story-prev');
  function render(){
    const s=scenes[idx];
    document.body.dataset.scene=String(idx);
    byId('story-chapter').textContent=s.chapter;
    byId('story-title').textContent=s.title;
    byId('story-deck').textContent=s.deck;
    byId('story-body').textContent=s.body;
    byId('story-exhibit').querySelector('span').textContent=s.label;
    byId('story-exhibit').querySelector('strong').textContent=s.evidence;
    byId('room-annotation').textContent=s.room;
    prev.disabled=idx===0;
    next.innerHTML=idx===scenes.length-1?'Open the evidence desk <span>↗</span>':'Next scene <span>→</span>';
    document.querySelectorAll('[data-scene]').forEach(el=>{
      const active=Number(el.dataset.scene)===idx;
      el.classList.toggle('is-current',active);
      if(active)el.setAttribute('aria-current','step');else el.removeAttribute('aria-current');
    });
  }
  next.addEventListener('click',()=>{if(idx===scenes.length-1){if(reduce){location.assign('/explore#reveal');return;}curtain?.classList.add('is-visible');setTimeout(()=>location.assign('/explore#reveal'),580);}else{idx++;render();}});
  prev.addEventListener('click',()=>{if(idx>0){idx--;render();}});
  document.querySelectorAll('.story-stepper [data-scene]').forEach(el=>el.addEventListener('click',()=>{idx=Number(el.dataset.scene);render();}));
  document.addEventListener('keydown',e=>{
    if(e.target.closest('button,a,input,select,textarea'))return;
    if(e.key==='ArrowRight'&&idx<scenes.length-1){idx++;render();}
    if(e.key==='ArrowLeft'&&idx>0){idx--;render();}
  });
  render();
})();
