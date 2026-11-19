/* SombraViva · animações de entrada.
   - Abertura: título, texto, botões e foto entram em sequência ao carregar.
   - Ao rolar: cada bloco sobe e aparece quando entra na tela; itens de grades entram em cascata.
   - Respeita "reduzir movimento" do sistema: nesse caso nada é animado.
   Sem JavaScript, ou se o navegador não tiver IntersectionObserver, tudo aparece normalmente. */
(() => {
  'use strict';
  const root = document.documentElement;
  const reduce = window.matchMedia('(prefers-reduced-motion: reduce)');
  if (reduce.matches || !('IntersectionObserver' in window)) return;

  const groups = [
    '.sv-section-head', '.sv-duo-item', '.sv-facts > div', '.sv-archive-head', '.sv-archive-grid > figure',
    '.sv-steps > li', '.sv-howto', '.sv-kpis > *', '.sv-row > *', '.sv-map > *', '.sv-form', '.sv-summary > div',
    '.sv-ods-grid > div', '.sv-purpose h2', '.sv-footer-cols > *', '#history-form + .sv-notice + .sv-chart-card',
  ];
  const targets = new Set();
  groups.forEach(selector => document.querySelectorAll(selector).forEach(el => targets.add(el)));
  if (!targets.size && !document.querySelector('.sv-hero, .sv-login')) return;

  root.classList.add('js-motion');
  targets.forEach(el => {
    el.classList.add('sv-reveal');
    // Atraso em cascata conforme a posição do item dentro do mesmo grupo (CSSOM; a CSP só bloqueia style="").
    const siblings = el.parentElement ? [...el.parentElement.children].filter(c => targets.has(c)) : [el];
    el.style.setProperty('--reveal-delay', `${Math.min(siblings.indexOf(el), 5) * 90}ms`);
  });

  const observer = new IntersectionObserver(entries => {
    entries.forEach(entry => {
      if (!entry.isIntersecting) return;
      entry.target.classList.add('is-visible');
      observer.unobserve(entry.target);
    });
  }, {rootMargin: '0px 0px -8% 0px', threshold: 0.12});
  targets.forEach(el => observer.observe(el));

  // Valores que mudam com os dados (faixa ao vivo e cartões): um pulso discreto a cada atualização.
  const pulse = el => { el.classList.remove('sv-pulse'); void el.offsetWidth; el.classList.add('sv-pulse'); };
  document.querySelectorAll('.sv-strip strong, .sv-hero-card strong, .sv-kpi strong, .sv-duo-label strong, .sv-facts dd').forEach(el => {
    new MutationObserver(() => pulse(el)).observe(el, {childList: true, characterData: true, subtree: true});
  });

  // Se o usuário ativar "reduzir movimento" com a página aberta, mostra tudo na hora.
  reduce.addEventListener?.('change', event => {
    if (!event.matches) return;
    targets.forEach(el => el.classList.add('is-visible'));
    root.classList.remove('js-motion');
  });
})();
