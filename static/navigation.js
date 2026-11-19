(() => {
  'use strict';
  // Rolagem suave nos links internos (#secao), animada aqui mesmo quadro a quadro.
  // O "smooth" nativo (CSS ou scrollIntoView) é desligado pelo Chrome e pelo Firefox quando o
  // Windows está com os efeitos de animação desligados; esta animação funciona sempre.
  let frame = null;
  const stop = () => { if (frame) cancelAnimationFrame(frame); frame = null; };
  ['wheel', 'touchstart', 'keydown'].forEach(type => window.addEventListener(type, stop, {passive: true}));
  const ease = t => (t < .5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2);
  function smoothTo(target) {
    stop();
    const offset = parseFloat(getComputedStyle(document.documentElement).scrollPaddingTop) || 0;
    const start = window.scrollY;
    const end = Math.max(0, target.getBoundingClientRect().top + start - offset);
    const distance = end - start;
    const duration = Math.min(1200, 450 + Math.abs(distance) * 0.18);
    let begin = null;
    const step = now => {
      if (begin === null) begin = now;
      const progress = Math.min(1, (now - begin) / duration);
      window.scrollTo({top: start + distance * ease(progress), behavior: 'instant'});
      frame = progress < 1 ? requestAnimationFrame(step) : null;
    };
    frame = requestAnimationFrame(step);
  }
  document.querySelectorAll('a[href^="#"]').forEach(link => link.addEventListener('click', event => {
    const id = decodeURIComponent(link.getAttribute('href').slice(1));
    const target = id && document.getElementById(id);
    if (!target) return;
    event.preventDefault();
    smoothTo(target);
    if (!target.hasAttribute('tabindex')) target.setAttribute('tabindex', '-1');
    target.focus({preventScroll: true});
    history.pushState(null, '', '#' + id);
  }));
  const menu = document.getElementById('menu-toggle');
  const nav = document.getElementById('site-navigation');
  if (!menu || !nav) return;
  const close = () => { menu.setAttribute('aria-expanded','false');menu.setAttribute('aria-label','Abrir menu de navegação');document.body.classList.remove('nav-open'); };
  menu.addEventListener('click', () => {
    const opening=menu.getAttribute('aria-expanded')!=='true';
    menu.setAttribute('aria-expanded',String(opening));
    menu.setAttribute('aria-label',opening?'Fechar menu de navegação':'Abrir menu de navegação');
    document.body.classList.toggle('nav-open',opening);
  });
  nav.querySelectorAll('a').forEach(link=>link.addEventListener('click',close));
  document.addEventListener('keydown',event=>{if(event.key==='Escape')close();});
  document.addEventListener('click',event=>{if(!menu.contains(event.target)&&!nav.contains(event.target))close();});
  const mql=window.matchMedia('(min-width: 961px)');
  mql.addEventListener?.('change',event=>{if(event.matches)close();});
  const links=nav.querySelectorAll('a[href^="#"]');
  if('IntersectionObserver' in window && links.length) {
    const observer=new IntersectionObserver(entries=>{
      entries.forEach(entry=>{
        if(!entry.isIntersecting)return;
        links.forEach(link=>{const selected=link.getAttribute('href')==='#'+entry.target.id;link.classList.toggle('selected',selected);if(selected)link.setAttribute('aria-current','location');else link.removeAttribute('aria-current');});
      });
    },{rootMargin:'-22% 0px -65% 0px',threshold:0});
    links.forEach(link=>{const target=document.querySelector(link.getAttribute('href'));if(target)observer.observe(target);});
  }
})();
