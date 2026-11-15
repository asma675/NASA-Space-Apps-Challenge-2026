'use strict';
/* Experience-only behavior, intentionally separate from all science and map logic. */
(() => {
  window.addEventListener('DOMContentLoaded', () => {
    // Story-page exits use the same cinematic timing as the observatory entrance.
    const reduced=window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    const curtain=document.createElement('div');
    curtain.className='experience-exit';
    curtain.setAttribute('aria-hidden','true');
    curtain.innerHTML='<span>PARALLAX <i>✦</i> BLINDSPOT</span>';
    document.body.appendChild(curtain);
    document.querySelectorAll('a[href="/"],a[href="/observatory"]').forEach(anchor=>{
      anchor.addEventListener('click',event=>{
        if(event.defaultPrevented||event.metaKey||event.ctrlKey||event.shiftKey||event.altKey)return;
        event.preventDefault();
        if(reduced){location.assign(anchor.href);return;}
        curtain.classList.add('is-visible');
        setTimeout(()=>location.assign(anchor.href),530);
      });
    });
    const journey=[...document.querySelectorAll('.explore-journey a')];
    const links=journey.map(a=>({a,section:document.querySelector(a.getAttribute('href'))})).filter(x=>x.section);
    if('IntersectionObserver' in window){
      const io=new IntersectionObserver(entries=>{
        const e=entries.filter(x=>x.isIntersecting).sort((a,b)=>b.intersectionRatio-a.intersectionRatio)[0];
        if(!e)return;
        journey.forEach(a=>a.classList.toggle('on',a.getAttribute('href')==='#'+e.target.id));
      },{rootMargin:'-20% 0px -65% 0px',threshold:[0,.1,.3]});
      links.forEach(x=>io.observe(x.section));
    }
    const hash=location.hash;
    if(hash&&document.querySelector(hash)){
      setTimeout(()=>{document.querySelector(hash).scrollIntoView({behavior:'instant',block:'start'});},1200);
    }
  });
})();
