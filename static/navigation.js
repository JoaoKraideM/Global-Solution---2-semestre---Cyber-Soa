(() => {
  'use strict';
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
