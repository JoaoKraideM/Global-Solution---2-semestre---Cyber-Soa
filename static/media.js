/* Arquivo territorial — falha de mídia não pode gerar uma superfície vazia.
   As imagens documentais são carregadas de Wikimedia Commons. O fallback local
   é uma ilustração cartográfica, nunca uma fotografia simulada de Osasco. */
(() => {
  'use strict';
  document.querySelectorAll('img.documentary-media[data-fallback]').forEach(image => {
    const figure = image.closest('figure');
    const noteId = image.getAttribute('data-credit-id');
    const note = noteId ? document.getElementById(noteId) : null;
    const fallback = image.getAttribute('data-fallback');
    let triedFallback = false;
    const showFallback = () => {
      if (triedFallback) return;
      triedFallback = true;
      figure?.classList.add('media-fallback-visible');
      if (note) note.hidden = false;
      image.alt = 'Cartografia ilustrativa do observatório climático; a fotografia documental não está disponível.';
      image.removeAttribute('referrerpolicy');
      image.src = fallback;
    };
    image.addEventListener('error', showFallback);
    if (image.complete && image.naturalWidth === 0) showFallback();
  });
})();
