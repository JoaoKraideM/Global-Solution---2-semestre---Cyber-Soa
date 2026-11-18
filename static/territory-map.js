/* Painel integrado do atlas: contexto territorial, cenários IoT e ERA5.
   Não associa as estações fictícias a endereços físicos. */
(() => {
  'use strict';
  const locations = {
    calcadao: {
      name: 'Calçadão da Rua Antônio Agú',
      type: 'INTERVENÇÃO DOCUMENTADA',
      detail: 'Rua Antônio Agú, Centro, Osasco. Ponto de referência aproximado do trecho central do Calçadão, conforme dados geográficos públicos.',
      context: 'Intervenção urbana no Centro de Osasco: estudo documental da retirada de coqueiros e da cobertura artificial.',
      stationCode: 'centro-demo',
      scenario: 'Cenário de área exposta, apenas demonstrativo. O dispositivo não está instalado no Calçadão.',
      lat: -23.5333671, lon: -46.7790848, zoom: 17
    },
    parque: {
      name: 'Parque Ana Luiza Moura Freitas',
      type: 'PARQUE MUNICIPAL / VEGETAÇÃO',
      detail: 'Rua David da Silva, 111, Piratininga, Osasco. Localização de referência do Parque Ecológico e Borboletário Municipal.',
      context: 'Área verde em Piratininga: referência territorial para discutir sombra, permeabilidade e arborização.',
      stationCode: 'verde-demo',
      scenario: 'Cenário de área arborizada, apenas demonstrativo. O dispositivo não está instalado no parque.',
      lat: -23.5163255, lon: -46.7852783, zoom: 16
    }
  };
  const $ = id => document.getElementById(id);
  const frame = $('territory-map-frame');
  if (!frame) return;
  const buttons = [...document.querySelectorAll('[data-map-location]')];
  const placeholder = $('territory-map-placeholder');
  const load = $('load-territory-map');
  const external = $('map-open-external');
  const status = $('map-availability');
  const statusText = $('map-availability-text');
  const retry = $('map-retry');
  const stationValue = $('atlas-sensor-value');
  const stationContext = $('atlas-sensor-context');
  const stationTime = $('atlas-sensor-timestamp');
  const eraValue = $('atlas-era5-value');
  const eraContext = $('atlas-era5-context');
  const eraPeriod = $('atlas-era5-period');
  let selected = 'calcadao';
  let isLoaded = false;
  let loadTimer = null;
  let stationData = null;
  let historyData = null;

  function placeUrl(place) {
    const delta = place.zoom === 17 ? 0.006 : 0.009;
    const params = new URLSearchParams({
      bbox: [place.lon - delta, place.lat - delta * .65, place.lon + delta, place.lat + delta * .65].join(','),
      layer: 'mapnik', marker: [place.lat, place.lon].join(',')
    });
    return `https://www.openstreetmap.org/export/embed.html?${params}`;
  }
  function openExternalUrl(place) {
    return `https://www.openstreetmap.org/?mlat=${place.lat}&mlon=${place.lon}#map=${place.zoom}/${place.lat}/${place.lon}`;
  }
  function setMapStatus(message) {
    if (!status) return;
    status.hidden = false;
    statusText.textContent = message;
  }
  function showMap() {
    const place = locations[selected];
    isLoaded = true;
    placeholder.hidden = true;
    frame.hidden = false;
    frame.title = `Mapa OpenStreetMap: ${place.name} — posição geográfica aproximada`;
    setMapStatus('Solicitando o mapa. Se não aparecer, utilize “Abrir no OpenStreetMap” abaixo.');
    frame.src = placeUrl(place);
    if (loadTimer !== null) window.clearTimeout(loadTimer);
    // Por restrições de origem, o load de um iframe não confirma se o provedor exibiu o mapa.
    loadTimer = window.setTimeout(() => setMapStatus('O mapa pode estar indisponível. Abra o endereço diretamente no OpenStreetMap ou tente recarregar.'), 12000);
  }
  frame.addEventListener('load', () => {
    if (loadTimer !== null) window.clearTimeout(loadTimer);
    if (isLoaded) setMapStatus('Mapa solicitado. Caso o conteúdo esteja vazio, abra a localização no OpenStreetMap.');
  });
  frame.addEventListener('error', () => setMapStatus('Não foi possível carregar o mapa incorporado. Use o link externo ou recarregue.'));

  const temp = value => typeof value === 'number' && Number.isFinite(value) ? value.toFixed(1).replace('.', ',') + ' °C' : 'Sem valor';
  const date = text => {
    const d = new Date(text);
    return Number.isFinite(d.getTime()) ? d.toLocaleString('pt-BR', {dateStyle: 'short', timeStyle: 'short', timeZone: 'America/Sao_Paulo'}) : 'Horário não disponível';
  };
  const shortDay = raw => /^\d{4}-\d{2}-\d{2}$/.test(raw || '') ? raw.split('-').reverse().join('/') : '—';
  const isOsasco = city => !!city && city.name?.toLocaleLowerCase('pt-BR') === 'osasco' &&
    Math.abs(Number(city.latitude) + 23.5329) < .06 && Math.abs(Number(city.longitude) + 46.7917) < .06;

  function renderStation() {
    if (stationData?.error) {
      stationValue.textContent = 'Dados indisponíveis';
      stationContext.textContent = 'Não foi possível consultar as estações. Verifique API e MySQL.';
      stationTime.textContent = 'Atualize a página ou use o botão de recarga de sensores.';
      return;
    }
    const place = locations[selected];
    const st = stationData?.stations?.find(item => item.code === place.stationCode);
    if (!st) {
      stationValue.textContent = stationData ? 'Cenário não cadastrado' : 'Aguardando API';
      stationContext.textContent = place.scenario;
      stationTime.textContent = stationData ? 'Cadastre os sensores demonstrativos no seed.' : 'Consultando /api/v1/summary';
      return;
    }
    if (!st.simulated) {
      stationValue.textContent = 'Localização não cadastrada';
      stationContext.textContent = 'Este dispositivo não está marcado como simulado; a base não informa coordenadas. Nenhuma associação física com este endereço é feita.';
      stationTime.textContent = 'Para instalar sensores, cadastre coordenadas reais em uma futura etapa.';
      return;
    }
    stationValue.textContent = st.latest ? temp(st.latest.temperature_c) : 'Sem leitura de teste';
    stationContext.textContent = place.scenario;
    stationTime.textContent = st.latest ? `Estação ${st.code} · leitura simulada em ${date(st.latest.measured_at)}` : `Estação ${st.code} · nenhuma leitura`;
  }
  function renderHistory() {
    if (historyData?.loading) {
      eraValue.textContent = 'Consultando…';
      eraContext.textContent = 'Obtendo os dados regionais pelo histórico da Open-Meteo.';
      eraPeriod.textContent = 'A consulta pode depender de conexão externa.';
      return;
    }
    if (historyData?.error) {
      eraValue.textContent = 'Histórico indisponível';
      eraContext.textContent = 'O provedor meteorológico não respondeu. Os dados IoT seguem independentes.';
      eraPeriod.textContent = 'Use “Consultar Osasco no histórico” para tentar novamente.';
      return;
    }
    if (!historyData?.mainData) {
      eraValue.textContent = 'Aguardando consulta';
      eraContext.textContent = 'Os dados ERA5 são regionais e não medem a temperatura deste endereço.';
      eraPeriod.textContent = 'Período selecionado na seção Arquivo climático.';
      return;
    }
    if (!isOsasco(historyData.main)) {
      eraValue.textContent = 'Outra cidade selecionada';
      eraContext.textContent = `O histórico principal está em ${historyData.main.name}. Para relacionar este território, consulte Osasco.`;
      eraPeriod.textContent = 'Nenhum dado de outra cidade foi atribuído aos locais de Osasco.';
      return;
    }
    const mean = historyData.mainData?.summary?.mean_temperature_c;
    eraValue.textContent = Number.isFinite(mean) ? temp(mean) : 'Sem média disponível';
    eraContext.textContent = historyData.mainData.simulated ? 'SÉRIE HISTÓRICA FICTÍCIA para prévia, NÃO é ERA5 nem medição local.' : 'Média diária do período consultado no ERA5 para Osasco. O valor regional não corresponde à rua nem ao sensor simulado.';
    eraPeriod.textContent = `${historyData.mainData.simulated?'SIMULAÇÃO · ':'ERA5 · '}${shortDay(historyData.start)} a ${shortDay(historyData.end)} · ${historyData.mainData.days?.length || 0} dias`;
  }
  function updateSelection() {
    const p = locations[selected];
    buttons.forEach(button => {
      const on = button.dataset.mapLocation === selected;
      button.classList.toggle('is-active', on);
      button.setAttribute('aria-pressed', String(on));
    });
    $('map-place-name').textContent = p.name;
    $('map-place-type').textContent = p.type;
    $('map-place-description').textContent = p.detail;
    $('atlas-selected-place').textContent = p.name;
    $('atlas-place-context').textContent = p.context;
    $('atlas-announcement').textContent = `${p.name} selecionado. Contexto dos dados atualizado. As estações são cenários, não sensores instalados.`;
    external.href = openExternalUrl(p);
    renderStation();
    // A troca de local altera somente o endereço de referência. NÃO altera o dado ERA5 regional.
    renderHistory();
    if (isLoaded) showMap();
  }
  buttons.forEach(button => button.addEventListener('click', () => {
    if (!locations[button.dataset.mapLocation]) return;
    selected = button.dataset.mapLocation;
    updateSelection();
  }));
  load?.addEventListener('click', showMap);
  retry?.addEventListener('click', showMap);
  window.addEventListener('sombraviva:select-place', event => {
    if (!locations[event.detail?.id]) return;
    selected = event.detail.id;
    updateSelection();
  });
  window.addEventListener('sombraviva:stations', event => {
    stationData = event.detail;
    renderStation();
  });
  window.addEventListener('sombraviva:history', event => {
    historyData = event.detail;
    renderHistory();
  });
  $('atlas-open-history')?.addEventListener('click', () => {
    window.dispatchEvent(new CustomEvent('sombraviva:choose-osasco'));
    $('historico')?.scrollIntoView({behavior: window.matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth'});
  });
  // Reidrata o painel se alguma chamada assíncrona terminou antes de este módulo carregar.
  stationData = window.sombravivaAtlasLatest?.stations ?? null;
  historyData = window.sombravivaAtlasLatest?.history ?? null;
  updateSelection();
})();
