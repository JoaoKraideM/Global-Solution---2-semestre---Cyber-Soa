/* SombraViva · fotografias documentais vindas de sites externos (com crédito na legenda).
   Se uma foto não carregar, mostra o aviso da própria figura e esconde a imagem quebrada:
   nunca troca uma fotografia do lugar por arte sintética sem identificação. */
(() => {
  'use strict';
  document.querySelectorAll('img.documentary-media').forEach(image => {
    const note = document.getElementById(image.getAttribute('data-credit-id') || '');
    let failed = false;
    const showNote = () => {
      if (failed) return;
      failed = true;
      image.closest('figure')?.classList.add('media-fallback-visible');
      if (note) note.hidden = false;
      image.hidden = true;
      image.removeAttribute('src');
    };
    image.addEventListener('error', showNote);
    if (image.complete && image.naturalWidth === 0) showNote();
  });
})();
