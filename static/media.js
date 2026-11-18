/* SombraViva · proveniência das imagens do território.
   Falhas de mídia externa mostram aviso legível + fonte: nunca trocam
   uma fotografia do lugar por arte sintética sem identificação. */
(() => {
  'use strict';
  document.querySelectorAll('img.documentary-media').forEach(image => {
    const figure = image.closest('figure');
    const creditId = image.getAttribute('data-credit-id');
    const note = creditId ? document.getElementById(creditId) : null;
    const fallback = image.getAttribute('data-fallback');
    let unavailable = false;
    const showFallback = () => {
      if (unavailable) return;
      unavailable = true;
      figure?.classList.add('media-fallback-visible');
      if (note) note.hidden = false;
      if (fallback) {
        // Este ramo só é usado para material explicitamente identificado.
        image.alt = 'Imagem de referência indisponível; visualização alternativa identificada.';
        image.src = fallback;
      } else {
        image.hidden = true;
        image.removeAttribute('src');
      }
    };
    image.addEventListener('error', showFallback);
    if (image.complete && image.naturalWidth === 0) showFallback();
  });
})();
