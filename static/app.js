(() => {
'use strict';
const $ = id => document.getElementById(id);
// Mantenha o último estado para interfaces montadas após uma resposta muito rápida da API.
const atlasLatest = window.sombravivaAtlasLatest = window.sombravivaAtlasLatest || {};
function publishAtlas(topic, detail) {
  atlasLatest[topic] = detail;
  window.dispatchEvent(new CustomEvent(`sombraviva:${topic}`, {detail}));
}
let currentLines = [];
const fmt = (v, suffix = '°C') => Number.isFinite(Number(v)) ? Number(v).toFixed(1).replace('.', ',') + suffix : '--';
async function request(url, opts={}) {
  const headers = {...opts.headers};
  const res = await fetch(url, {...opts, headers});
  let data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.detail || `Erro HTTP ${res.status}`);
  return data;
}
function stationCard(station) {
  const wrap = document.createElement('div'); wrap.className = 'station-card';
  const info = document.createElement('div');
  const title = document.createElement('h3'); title.textContent = station.name;
  const desc = document.createElement('p'); desc.textContent = station.setting;
  const badge = document.createElement('span'); badge.className = 'sensor-pill'; badge.textContent = station.simulated ? 'SIMULAÇÃO · NÃO INSTALADO' : 'ESTAÇÃO CADASTRADA';
  const provenance = document.createElement('small'); provenance.className = 'station-provenance';
  const measured = station.latest?.measured_at;
  const at = measured && !Number.isNaN(Date.parse(measured)) ? new Date(measured).toLocaleString('pt-BR') : 'sem leitura registrada';
  provenance.textContent = `ID ${station.code} · ${station.simulated ? 'registro fictício' : 'dispositivo cadastrado, posição não verificada'} · última leitura: ${at}`;
  info.append(title,desc,badge,provenance);
  const temp = document.createElement('strong'); temp.textContent = station.latest ? fmt(station.latest.temperature_c) : '--';
  if (station.simulated && (station.code === 'centro-demo' || station.code === 'verde-demo')) {
    const scenario = document.createElement('a');
    scenario.href = '#mapa'; scenario.className = 'station-atlas-link';
    scenario.textContent = 'Ver contexto urbano hipotético ↗';
    scenario.addEventListener('click', () => window.dispatchEvent(new CustomEvent('sombraviva:select-place', {detail: {id: station.code === 'centro-demo' ? 'calcadao' : 'parque'}})));
    info.append(scenario);
  }
  wrap.append(info,temp); return wrap;
}
async function loadClimate(){
  const stationsNode=$('stations');
  stationsNode?.setAttribute('aria-busy','true');
  if(stationsNode)stationsNode.textContent='Atualizando estações...';
  let data, sets;
  let reason='';
  try {
    data = await request('/api/v1/summary');
    if (!Array.isArray(data.stations) || data.stations.length < 2 || !data.stations.slice(0,2).some(s => s.latest))
      throw new Error('O banco ainda não possui as duas séries de demonstração');
    sets = await Promise.all(data.stations.slice(0,2).map(s => request(`/api/v1/stations/${encodeURIComponent(s.code)}/readings?limit=24`)));
    if(!sets.some(series => series.length))throw new Error('Nenhuma leitura retornada pelo MySQL');
    $('demo-mode-banner')?.classList.add('hidden');
  } catch (err) {
    reason = String(err?.message || 'Falha de conexão');
    try {
      data = await request('/api/v1/demo/summary');
      sets = data.stations.slice(0,2).map(s => data.readings[s.code] || []);
      const banner = $('demo-mode-banner');
      if (banner) {banner.classList.remove('hidden');banner.querySelector('span').textContent =
        `MySQL indisponível ou sem leituras (${reason}). Estes valores são fictícios, gerados em memória e não persistidos. Execute as migrações/seed para obter registros no banco.`;}
    } catch (demoError) {
      $('stations').textContent = `Falha na API e na demonstração. Tente atualizar. Detalhe: ${demoError.message}.`;
      $('stations').setAttribute('aria-busy','false');
      for(const id of ['temp-a','temp-b','temp-diff','readings-count'])$(id).textContent='—';
      currentLines=[];updateSensorEmpty('Sem conexão com API ou base demonstrativa.');
      publishAtlas('stations', {error:'API/DB indisponível'});return;
    }
  }
  $('readings-count').textContent = data.demo ? '0' : String(data.readings_total);
  $('temp-a').textContent = data.stations[0]?.latest ? fmt(data.stations[0].latest.temperature_c) : '—';
  $('temp-b').textContent = data.stations[1]?.latest ? fmt(data.stations[1].latest.temperature_c) : '—';
  $('temp-diff').textContent = data.pairwise_difference_c == null ? '—' : fmt(data.pairwise_difference_c);
  $('stations').replaceChildren(...data.stations.map(stationCard));
  $('stations').setAttribute('aria-busy','false');
  const sourceLabel=$('iot-origin');
  if(sourceLabel){
    const simulatedCount=data.stations.filter(item=>item.simulated).length;
    const label=sourceLabel.querySelector('.source-type');
    label.textContent=data.demo?'SIMULAÇÃO · API DEMO':simulatedCount?'REDE IOT · CENÁRIOS IDENTIFICADOS':'ESTAÇÕES CADASTRADAS · POSIÇÃO NÃO VALIDADA';
    label.className='source-type '+(simulatedCount||data.demo?'source-simulation':'source-hypothesis');
    const note=$('iot-origin-note');
    if(note)note.textContent=simulatedCount?`${simulatedCount} de ${data.stations.length} estações têm leituras fictícias ou de teste. Não são medições comprovadas nos locais selecionados. Consulte ID e horário de cada registro.`:'Não há confirmação de georreferenciamento ou calibração dessas estações. Consulte ID, origem e horário antes de interpretar uma leitura como local.';
  }
  currentLines=sets;
  drawChart();updateSensorEmpty();
  publishAtlas('stations',{stations:data.stations,readings:Object.fromEntries(data.stations.slice(0,2).map((st,i)=>[st.code,sets[i]])),demo:!!data.demo});
}

function updateSensorEmpty(message='Nenhuma leitura disponível ainda. Execute o simulador IoT para preencher este instrumento.') {
  const empty=$('sensor-empty');if(!empty)return;
  const hasReadings=currentLines.some(points=>points.length);
  empty.classList.toggle('hidden',hasReadings);
  empty.querySelector('span').textContent=message;
}
async function loadWeather(){
  const origin=$('weather-origin-chip');
  if(origin){origin.textContent='CONSULTANDO FONTE';origin.className='source-type source-unavailable';}
  $('weather-status').textContent='Consultando fonte meteorológica...';
  try{
    const w = await request('/api/v1/weather/osasco');
    if(origin){origin.textContent='DADO REGIONAL · OPEN-METEO';origin.className='source-type source-regional';}
    $('weather-value').textContent=fmt(w.temperature_c);
    $('weather-status').textContent=`MODELO REGIONAL (Open-Meteo) • ${String(w.time).replace('T',' ')}`;
    $('feels-like').textContent=fmt(w.apparent_temperature_c);
    $('outside-humidity').textContent=fmt(w.humidity_pct,'%');
    $('weather-retry').classList.add('hidden');
  }catch(err){
    try{
      const w=await request('/api/v1/demo/weather');
      if(origin){origin.textContent='SIMULAÇÃO · SEM DADO REAL';origin.className='source-type source-simulation';}
      $('weather-value').textContent=fmt(w.temperature_c);
      $('feels-like').textContent=fmt(w.apparent_temperature_c);
      $('outside-humidity').textContent=fmt(w.humidity_pct,'%');
      $('weather-status').textContent='SIMULAÇÃO · CLIMA FICTÍCIO, NÃO OBSERVADO. A Open-Meteo não respondeu.';
      $('weather-retry').classList.remove('hidden');
    }catch(demoError){
      if(origin){origin.textContent='FONTE INDISPONÍVEL';origin.className='source-type source-unavailable';}
      $('weather-status').textContent='Fonte meteorológica indisponível; sem dados demonstrativos.';
      $('weather-value').textContent='—';$('feels-like').textContent='—';$('outside-humidity').textContent='—';
      $('weather-retry').classList.remove('hidden');
    }
  }
}

function drawChart(){
  const canvas = $('temperature-chart');
  if(!canvas) return;
  const dpr = window.devicePixelRatio || 1;
  const {width,height} = canvas.getBoundingClientRect();
  if(!width||!height)return;
  canvas.width = width*dpr; canvas.height = height*dpr;
  const ctx = canvas.getContext('2d');ctx.scale(dpr,dpr);
  const pad={l:37,r:12,t:13,b:30}; const pw=width-pad.l-pad.r,ph=height-pad.t-pad.b;
  const all=currentLines.flat().map(p=>p.temperature_c);
  if(!all.length){ctx.fillStyle='#62766E';ctx.fillText('Sem medições disponíveis',40,60);return;}
  let min=Math.floor(Math.min(...all)-2),max=Math.ceil(Math.max(...all)+2);if(max===min)max++;
  ctx.lineWidth=1;ctx.font='11px sans-serif';
  for(let i=0;i<=4;i++){const y=pad.t+i*ph/4;ctx.strokeStyle='#D6E2DA';ctx.beginPath();ctx.moveTo(pad.l,y);ctx.lineTo(width-pad.r,y);ctx.stroke();ctx.fillStyle='#62766E';ctx.textAlign='right';ctx.fillText((max-i*(max-min)/4).toFixed(0)+'°',pad.l-8,y+4);}
  const colors=['#BA543C','#28718A'];
  currentLines.forEach((points,k)=>{
    if(!points.length)return;
    ctx.strokeStyle=colors[k];ctx.lineWidth=2.6;ctx.lineJoin='round';ctx.lineCap='round';ctx.beginPath();
    points.forEach((p,i)=>{const x=pad.l+(points.length===1?pw/2:i*pw/(points.length-1));const y=pad.t+(max-p.temperature_c)/(max-min)*ph;if(i===0)ctx.moveTo(x,y);else ctx.lineTo(x,y);});ctx.stroke();
  });
  ctx.fillStyle='#62766E';ctx.textAlign='center';const first=currentLines[0]||[];
  if(first.length){[0,Math.floor((first.length-1)/2),first.length-1].forEach(i=>{let x=pad.l+(first.length===1?pw/2:i*pw/(first.length-1));let date=new Date(first[i].measured_at);ctx.fillText(date.toLocaleTimeString('pt-BR',{hour:'2-digit',minute:'2-digit'}),x,height-8);});}
}
/* Histórico regional: ERA5 via nossa API REST. Não utiliza as leituras IoT simuladas. */
const historyState = {
  main: { name: 'Osasco', state: 'São Paulo', country: 'Brasil', latitude: -23.5329, longitude: -46.7917 },
  compare: null,
  mainData: null,
  compareData: null,
};
const historyDate = d => `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')}`;
const cityName = city => [city.name, city.state, city.country].filter(Boolean).join(', ');
const temp = n => typeof n === 'number' && Number.isFinite(n) ? n.toFixed(1).replace('.', ',') + ' °C' : '—';
const noVal = n => typeof n === 'number' ? n.toFixed(1).replace('.', ',') : '—';
const historyColors = ['#BA543C', '#28718A'];
let historyRequestId = 0;
let historyIsDemo = false;
function markHistorySource(simulated) {
  historyIsDemo = !!simulated;
  const badge=$('history-source-chip'); if(badge){badge.textContent=simulated?'SÉRIE FICTÍCIA · DEMONSTRAÇÃO':'DADOS REGIONAIS REAIS';badge.classList.toggle('demo-data-chip',simulated);}
  const provenance=$('history-provenance-label');
  if(provenance){provenance.textContent=simulated?'SIMULAÇÃO · SÉRIE FICTÍCIA':'DADO REGIONAL · ERA5';provenance.className='source-type '+(simulated?'source-simulation':'source-regional');}
  $('history-demo-banner')?.classList.toggle('hidden',!simulated);
  $('history-source-note')?.classList.toggle('hidden',!!simulated);
  $('history-demo-source-note')?.classList.toggle('hidden',!simulated);
}
function setHistoryStatus(message, isError=false) {
  $('history-status').textContent = message;
  $('history-status').classList.toggle('is-error',isError);
  $('history-status').dataset.state=isError?'error':message.startsWith('Carregando')?'loading':'ready';
  if(isError)$('history-retry').classList.remove('hidden');else $('history-retry').classList.add('hidden');
}
function chooseHistoryDates(preset) {
  const max = new Date(); max.setDate(max.getDate() - 8);
  const start = new Date(max);
  if (preset === 'last-year') {
    const y = new Date().getFullYear() - 1;
    $('history-start').value = `${y}-01-01`;
    $('history-end').value = `${y}-12-31`;
  } else {
    start.setDate(start.getDate() - (preset === '90' ? 89 : 29));
    $('history-start').value = historyDate(start);
    $('history-end').value = historyDate(max);
  }
  $('history-end').max = historyDate(max);
  $('history-start').max = historyDate(max);
}
async function searchHistoryLocation(field) {
  const main = field === 'main';
  const prefix = main ? 'history-city' : 'compare-city';
  const searchField = $(`${prefix}-search`);
  const term = searchField.value.trim();
  const select = $(`${prefix}-results`);
  if(term.length < 2) { setHistoryStatus('Digite pelo menos dois caracteres para pesquisar a cidade.', true);return; }
  setHistoryStatus('Buscando cidades para ' + (main ? 'consulta' : 'comparação') + '...');
  try {
    const data = await request('/api/v1/weather/places?'+ new URLSearchParams({search: term}));
    select.replaceChildren();
    const placeholder = document.createElement('option'); placeholder.value='';placeholder.textContent='Selecione uma cidade da lista';select.appendChild(placeholder);
    data.locations.forEach((city,i) => {const option=document.createElement('option');option.value=String(i);option.textContent=cityName(city);select.appendChild(option);});
    select._results = data.locations;
    select.classList.remove('hidden');
    if(!data.locations.length) setHistoryStatus('Nenhuma cidade encontrada. Tente outro nome.', true);
    else setHistoryStatus('Escolha a cidade na lista de resultados para aplicá-la ao histórico.');
  } catch(err) {
    try {
      const data=await request('/api/v1/demo/places?'+new URLSearchParams({search:term}));
      select.replaceChildren();
      const placeholder=document.createElement('option');placeholder.value='';placeholder.textContent='Escolha cidade (localização aproximada)';select.appendChild(placeholder);
      data.locations.forEach((city,i)=>{const option=document.createElement('option');option.value=String(i);option.textContent=cityName(city)+' · aproximação';select.appendChild(option);});
      select._results=data.locations;select.classList.toggle('hidden',!data.locations.length);
      setHistoryStatus(data.locations.length?'Busca demonstrativa offline: coordenadas aproximadas, não geocodificação oficial.':'Geocodificação indisponível e cidade não incluída na lista de exemplo.',!data.locations.length);
    } catch(demoError){select.classList.add('hidden');setHistoryStatus(err.message,true);}
  }
}
function applyHistoryCity(field) {
  const main = field === 'main';
  const select = $(main ? 'history-city-results' : 'compare-city-results');
  if(select.value==='') return;
  const city = select._results?.[Number(select.value)];
  if(!city)return;
  historyState[main ? 'main' : 'compare']=city;
  $(main ? 'history-city-selected' : 'compare-city-selected').textContent='Selecionada: '+cityName(city);
  $('remove-compare').classList.toggle('hidden', !historyState.compare);
  select.classList.add('hidden');
  queryHistory(); // Atualiza automaticamente o gráfico combinado e os gráficos individuais.
}
function historyDatesValid() {
  const start = $('history-start').value, end = $('history-end').value;
  if(!start||!end)return 'Informe data inicial e final.';
  // Usar UTC evita deslocamentos de calendário no navegador.
  const a=Date.parse(start+'T00:00:00Z'),b=Date.parse(end+'T00:00:00Z');
  if(!Number.isFinite(a)||!Number.isFinite(b)||a>b)return 'A data inicial precisa ser anterior ou igual à data final.';
  if((b-a)/86400000 > 365)return 'Selecione um intervalo de até 366 dias.';
  if(end>$('history-end').max)return 'O arquivo ERA5 ainda não disponibilizou esse dia. Escolha uma data anterior.';
  return null;
}
async function getCityHistorical(city, start, end, demo=false) {
  return request((demo?'/api/v1/demo/history?':'/api/v1/weather/history?') + new URLSearchParams({
    latitude: String(city.latitude), longitude: String(city.longitude), start_date: start, end_date: end,
  }));
}
// Nunca mostrar uma curva de datas que não correspondam ao filtro selecionado.
function historySeriesMatchesPeriod(series, start, end) {
  return Array.isArray(series?.days) && series.days.length > 0 && series.days.length <= 366 &&
    series.days.every((day, i) => /^\d{4}-\d{2}-\d{2}$/.test(day.date || '') && day.date >= start && day.date <= end &&
      (i === 0 || day.date > series.days[i-1].date));
}
async function queryHistory() {
  const requestId = ++historyRequestId;
  const error = historyDatesValid();
  if(error){setHistoryStatus(error,true);return;}
  const start=$('history-start').value,end=$('history-end').value;
  const main = historyState.main, compare=historyState.compare;
  $('history-form').querySelector('button[type="submit"]').disabled = true;
  $('history-results').classList.add('hidden');
  $('history-results').setAttribute('aria-busy','true');
  $('history-demo-banner')?.classList.add('hidden');
  $('history-demo-source-note')?.classList.add('hidden');
  const sourceChip = $('history-source-chip');
  if(sourceChip) sourceChip.textContent = 'CONSULTANDO FONTE';
  const pendingProvenance=$('history-provenance-label');if(pendingProvenance){pendingProvenance.textContent='VERIFICANDO ORIGEM';pendingProvenance.className='source-type source-unavailable';}
  if($('history-source-freshness'))$('history-source-freshness').textContent='Consultando a origem e o período selecionados...';
  publishAtlas('history', {loading: true});
  setHistoryStatus(`Carregando ${compare ? 'as duas cidades' : cityName(main)}...`);
  try {
    let results, isDemo=false;
    try {
      results=await Promise.all([getCityHistorical(main,start,end),compare ? getCityHistorical(compare,start,end):Promise.resolve(null)]);
    } catch(sourceError) {
      if(requestId!==historyRequestId)return;
      results=await Promise.all([getCityHistorical(main,start,end,true),compare ? getCityHistorical(compare,start,end,true):Promise.resolve(null)]);
      isDemo=true;
    }
    // Requisições antigas não podem sobrescrever uma nova cidade ou período.
    if(requestId !== historyRequestId) return;
    if(!historySeriesMatchesPeriod(results[0],start,end) || (compare && !historySeriesMatchesPeriod(results[1],start,end))) {
      throw new Error('A API retornou datas fora do intervalo ou sem ordem cronológica. Tente outro período.');
    }
    historyState.mainData=results[0];historyState.compareData=results[1];
    markHistorySource(isDemo);
    $('history-results').classList.remove('hidden');
    $('history-results').setAttribute('aria-busy','false');
    if($('history-source-freshness'))$('history-source-freshness').textContent=isDemo?'Atenção: série sintética de demonstração; não possui data de observação real.':`Fonte: Open-Meteo/ERA5 · consulta realizada em ${new Date().toLocaleString('pt-BR')} · período ${start} a ${end} · estimativa regional.`;
    if($('history-current-city'))$('history-current-city').textContent=`${cityName(main)} · ${results[0].days.length} dias`;
    if($('history-current-period'))$('history-current-period').textContent=`${cityName(main)} · ${start.split('-').reverse().join('/')} a ${end.split('-').reverse().join('/')} · ${compare?'comparando com '+cityName(compare):'sem cidade de comparação'}`;
    if($('history-filters'))$('history-filters').open=false;
    renderHistoricalData();
    publishAtlas('history', {main, mainData: results[0], compare, compareData: results[1], start, end});
    setHistoryStatus(`${results[0].days.length} dias • ${compare ? '2 cidades: ' : ''}${cityName(main)}${compare?' e '+cityName(compare):''} • ${isDemo?'APENAS DEMONSTRAÇÃO, DADOS INVENTADOS':'dados reais regionais ERA5'}`);
  } catch(err) {
    if(requestId !== historyRequestId) return;
    $('history-results').classList.add('hidden');
    $('history-results').setAttribute('aria-busy','false');
    if($('history-source-freshness'))$('history-source-freshness').textContent='Falha na fonte. Nenhum dado confiável foi carregado; use “Tentar novamente”.';
    if($('history-source-chip')) $('history-source-chip').textContent='FONTE INDISPONÍVEL';
    const provenance=$('history-provenance-label'); if(provenance){provenance.textContent='FONTE INDISPONÍVEL';provenance.className='source-type source-unavailable';}
    publishAtlas('history', {error: 'Consulta ERA5 indisponível'});
    setHistoryStatus('Não foi possível consultar o histórico: '+err.message+' Confira /api/v1/weather/history no Swagger.',true);
  } finally {
    if(requestId === historyRequestId) $('history-form').querySelector('button[type="submit"]').disabled=false;
  }
}
function historyMetric(city, series, color) {
  const section=document.createElement('div');section.className='history-kpi';section.style.borderTop=`3px solid ${color}`;
  const heading=document.createElement('small');heading.textContent=cityName(city);
  const value=document.createElement('strong');value.textContent=temp(series.summary.mean_temperature_c);
  const desc=document.createElement('p');desc.textContent=`Média do período • Máxima ${temp(series.summary.highest_temperature_c)} • Mínima ${temp(series.summary.lowest_temperature_c)}`;
  section.append(heading,value,desc);return section;
}
function renderHistoryInsight(pairs) {
  const target=$('history-insight');if(!target)return;
  const [city, series]=pairs[0];
  const mean=series?.summary?.mean_temperature_c;
  const max=series?.summary?.highest_temperature_c;
  if(!Number.isFinite(mean)) {target.textContent='Não há valores médios suficientes para interpretar o intervalo.';return;}
  const start=$('history-start').value.split('-').reverse().join('/');
  const end=$('history-end').value.split('-').reverse().join('/');
  let heading=`${city.name}: média de ${temp(mean)} no período`;
  let explanation=`Entre ${start} e ${end}, a maior máxima diária da série ${historyIsDemo?'FICTÍCIA de demonstração':'regional'} foi ${temp(max)}. ${historyIsDemo?'NÃO são dados históricos observados.':'Fonte: reanálise ERA5, não medição local.'}`;
  if(pairs.length===2) {
    const mean2=pairs[1][1]?.summary?.mean_temperature_c;
    if(Number.isFinite(mean2)) {
      const diff=Math.abs(mean-mean2);
      const warmer=diff<0.05?'As médias regionais foram equivalentes':(mean>mean2?`${city.name} registrou média ${temp(diff)} acima de ${pairs[1][0].name}`:`${pairs[1][0].name} registrou média ${temp(diff)} acima de ${city.name}`);
      heading=warmer+'.';
      explanation=`Médias do mesmo intervalo (${start} a ${end}). ${historyIsDemo?'SÉRIES FICTÍCIAS para testar a interface.':'Comparação regional, sem inferir diferenças de arborização local.'}`;
    }
  }
  const accessible=$('history-chart-text-summary');
  if(accessible)accessible.textContent=`${historyIsDemo?'Dados sintéticos.':'Dados regionais ERA5.'} ${city.name}: média ${temp(mean)}, maior máxima ${temp(max)}. Tabela diária e exportação CSV disponíveis ao final do histórico.`;
  target.replaceChildren();const label=document.createElement('span');label.textContent=historyIsDemo?'LEITURA DO PERÍODO / SIMULAÇÃO FICTÍCIA':'LEITURA DO PERÍODO / ERA5';
  const h=document.createElement('strong');h.textContent=heading;
  const p=document.createElement('p');p.textContent=explanation;target.append(label,h,p);
}
/* Observações calculadas exclusivamente dos dias retornados pela Open-Meteo.
   "Dias >= 30°C" é limiar exploratório, não diagnóstico de onda de calor. */
function renderHistoryObservations(pairs) {
  const container = $('history-observations');
  if (!container) return;
  container.replaceChildren();
  for (const [city, series] of pairs) {
    const days = Array.isArray(series?.days) ? series.days : [];
    const highs = days.filter(row => Number.isFinite(row.temperature_max_c));
    const lows = days.filter(row => Number.isFinite(row.temperature_min_c));
    const hot = highs.filter(row => row.temperature_max_c >= 30);
    const hottest = highs.length ? highs.reduce((a,b) => b.temperature_max_c > a.temperature_max_c ? b : a) : null;
    const coldest = lows.length ? lows.reduce((a,b) => b.temperature_min_c < a.temperature_min_c ? b : a) : null;
    const dateBR = raw => raw?.split('-').reverse().join('/') || '—';
    const entry = document.createElement('section'); entry.className='history-observation';
    const title=document.createElement('h4');title.textContent=city.name;
    const collection=document.createElement('dl');collection.className='history-observation-list';
    const metrics=[
      ['Dia com maior máxima',hottest?temp(hottest.temperature_max_c):'—',hottest?dateBR(hottest.date):'Dados indisponíveis'],
      ['Dia com menor mínima',coldest?temp(coldest.temperature_min_c):'—',coldest?dateBR(coldest.date):'Dados indisponíveis'],
      ['Dias com máxima ≥ 30 °C',String(hot.length),`${highs.length} dias com máxima disponível`]
    ];
    for (const [name,value,note] of metrics) {
      const item=document.createElement('div');item.className='history-observation-item';
      const term=document.createElement('dt');term.textContent=name;
      const number=document.createElement('dd');number.textContent=value;
      const caption=document.createElement('small');caption.textContent=note;
      item.append(term,number,caption);collection.append(item);
    }
    const footer=document.createElement('p');footer.textContent=(historyIsDemo?'Série FICTÍCIA para prévia.':'Recorte ERA5 · valores diários regionais.')+' O limiar de 30 °C é apenas exploratório e não define uma onda de calor.';
    entry.append(title,collection,footer);container.append(entry);
  }
}

function renderHistoricalData() {
  const pairs=[[historyState.main,historyState.mainData]];
  if(historyState.compare && historyState.compareData)pairs.push([historyState.compare,historyState.compareData]);
  $('history-kpis').replaceChildren(...pairs.map(([c,d],i)=>historyMetric(c,d,historyColors[i])));
  // A comparação não é um segundo gráfico redundante quando só uma cidade foi consultada.
  $('history-comparison').classList.toggle('hidden',pairs.length !== 2);
  renderHistoryInsight(pairs);
  renderHistoryObservations(pairs);
  const legend = pairs.map(([city],i)=>{const span=document.createElement('span');const line=document.createElement('i');line.style.background=historyColors[i];span.append(line,document.createTextNode(cityName(city)));return span;});
  $('history-legend').replaceChildren(...legend);
  const head=$('history-table-head'),body=$('history-table-body');head.replaceChildren();body.replaceChildren();
  const tr=document.createElement('tr');
  const labels=['Dia','Média (°C)','Mín. (°C)','Máx. (°C)'];
  if(pairs.length===2) labels.push('Média 2ª cidade (°C)');
  labels.forEach(v=>{const th=document.createElement('th');th.scope='col';th.textContent=v;tr.appendChild(th);});head.appendChild(tr);
  const comparison=new Map((historyState.compareData?.days || []).map(p=>[p.date,p]));
  for(const p of historyState.mainData.days){
    const row=document.createElement('tr');const second=comparison.get(p.date);
    const vals=[p.date,noVal(p.temperature_mean_c),noVal(p.temperature_min_c),noVal(p.temperature_max_c)];
    if(pairs.length===2)vals.push(noVal(second?.temperature_mean_c));
    vals.forEach(v=>{const cell=document.createElement('td');cell.textContent=v;row.appendChild(cell);});body.appendChild(row);
  }
  renderCityCharts(pairs);
  drawHistoryChart();
}
function drawHistoryChart(){
  const canvas=$('history-chart');if(!canvas||!historyState.mainData)return;
  const r=canvas.getBoundingClientRect();if(!r.width||!r.height)return;
  const dpr=Math.min(window.devicePixelRatio || 1,2),w=r.width,h=r.height;
  canvas.width=w*dpr;canvas.height=h*dpr;
  const ctx=canvas.getContext('2d');ctx.scale(dpr,dpr);
  const pad={left:45,right:14,top:19,bottom:34},pw=w-pad.left-pad.right,ph=h-pad.top-pad.bottom;
  const pairs=[historyState.mainData.days, ...(historyState.compareData ? [historyState.compareData.days] : [])];
  const vals=pairs.flatMap(x=>x.map(p=>p.temperature_mean_c).filter(Number.isFinite));
  if(!vals.length){ctx.fillStyle='#62766E';ctx.fillText('Não há valores para o período',20,40);return;}
  let low=Math.floor(Math.min(...vals)-2),high=Math.ceil(Math.max(...vals)+2);
  if(low===high)high=low+1;
  ctx.font='11px system-ui,sans-serif';ctx.textAlign='right';ctx.lineWidth=1;
  for(let i=0;i<=4;i++){
    const y=pad.top+(ph*i/4),value=high-(high-low)*i/4;
    ctx.strokeStyle='#D6E2DA';ctx.beginPath();ctx.moveTo(pad.left,y);ctx.lineTo(w-pad.right,y);ctx.stroke();
    ctx.fillStyle='#62766E';ctx.fillText(value.toFixed(0)+'°',pad.left-8,y+4);
  }
  const dates=historyState.mainData.days.map(p=>p.date);
  const pos=Object.fromEntries(dates.map((d,i)=>[d, i]));
  pairs.forEach((series,j)=>{
    ctx.beginPath();ctx.lineWidth=2.2;ctx.strokeStyle=historyColors[j];
    let started=false;
    for(const p of series){
      const v=p.temperature_mean_c, index=pos[p.date];
      if(index===undefined || !Number.isFinite(v)){started=false;continue;}
      const x=pad.left+(dates.length===1?pw/2:index/(dates.length-1)*pw);
      const y=pad.top+(high-v)/(high-low)*ph;
      if(!started){ctx.moveTo(x,y);started=true;}else ctx.lineTo(x,y);
    }
    ctx.stroke();
  });
  ctx.textAlign='center';ctx.fillStyle='#62766E';
  const indices=[0,Math.floor((dates.length-1)/2),dates.length-1];
  [...new Set(indices)].forEach(i=>{
    const x=pad.left+(dates.length===1?pw/2:i/(dates.length-1)*pw);
    const d=dates[i]?.split('-');if(!d)return;
    ctx.fillText(d[2]+'/'+d[1]+'/'+d[0],x,h-11);
  });
}
// Gráficos independentes de cada cidade: temperatura mínima, média e máxima.
// Escala compartilhada entre cartões, para evitar comparação visual enganosa.
function renderCityCharts(pairs) {
  const holder = $('history-city-charts');
  const cards = pairs.map(([city, series], i) => {
    const card = document.createElement('article'); card.className='city-chart-card';
    const top=document.createElement('div'); top.className='city-chart-top';
    const info=document.createElement('div');
    const overline=document.createElement('p');overline.className='city-chart-overline';overline.textContent=i===0?'01 · CIDADE PRINCIPAL':'02 · CIDADE DE COMPARAÇÃO';
    const title=document.createElement('h4');title.className='city-chart-name';title.textContent=city.name;
    const meta=document.createElement('p');meta.className='city-chart-meta';meta.textContent=[city.state,city.country].filter(Boolean).join(' · ');
    info.append(overline,title,meta);
    const average=document.createElement('div');average.className='city-chart-average';average.style.color=historyColors[i];
    average.append(document.createTextNode(temp(series.summary.mean_temperature_c)));
    const averageLabel=document.createElement('small');averageLabel.textContent='Média do período';average.append(averageLabel);
    top.append(info,average);card.append(top);
    const chartWrap=document.createElement('div');chartWrap.className='city-chart-canvas';
    const canvas=document.createElement('canvas');canvas.setAttribute('role','img');canvas.setAttribute('aria-label',`Temperaturas mínima, média e máxima de ${cityName(city)} por dia`);
    canvas.id=`history-city-chart-${i}`;chartWrap.append(canvas);card.append(chartWrap);
    const legend=document.createElement('div');legend.className='city-chart-legend';
    [['Mínima','#28718A'],['Média',historyColors[i]],['Máxima','#87A538']].forEach(([label,color])=>{
      const item=document.createElement('span'),swatch=document.createElement('i');swatch.style.background=color;
      item.append(swatch,document.createTextNode(label));legend.append(item);
    });
    const note=document.createElement('p');note.className='city-chart-note';note.textContent=`${series.days.length} dias • Menor mínima: ${temp(series.summary.lowest_temperature_c)} · Maior máxima: ${temp(series.summary.highest_temperature_c)}`;
    card.append(legend,note);return card;
  });
  holder.replaceChildren(...cards);
  drawIndividualCityCharts();
}
function drawIndividualCityCharts() {
  const pairs=[[historyState.main,historyState.mainData]];
  if(historyState.compare && historyState.compareData)pairs.push([historyState.compare,historyState.compareData]);
  const values=pairs.flatMap(([,d])=>d.days.flatMap(p=>[p.temperature_min_c,p.temperature_mean_c,p.temperature_max_c]).filter(Number.isFinite));
  if(!values.length)return;
  const lower=Math.floor(Math.min(...values)-2),upper=Math.ceil(Math.max(...values)+2);
  const range=Math.max(upper-lower,1);
  pairs.forEach(([city,data],i)=>{
    const canvas=$(`history-city-chart-${i}`);if(!canvas)return;
    const rect=canvas.getBoundingClientRect();if(!rect.width || !rect.height)return;
    const dpr=Math.min(window.devicePixelRatio || 1,2),w=rect.width,h=rect.height;
    canvas.width=Math.round(w*dpr);canvas.height=Math.round(h*dpr);
    const ctx=canvas.getContext('2d');ctx.scale(dpr,dpr);
    const pad={left:42,right:14,top:12,bottom:35},pw=w-pad.left-pad.right,ph=h-pad.top-pad.bottom;
    const dates=data.days.map(p=>p.date);
    ctx.font='10px system-ui,sans-serif';ctx.textAlign='right';ctx.lineWidth=1;
    for(let k=0;k<=4;k++){
      const y=pad.top+(k*ph/4),v=upper-k*range/4;
      ctx.strokeStyle='#D6E2DA';ctx.beginPath();ctx.moveTo(pad.left,y);ctx.lineTo(w-pad.right,y);ctx.stroke();
      ctx.fillStyle='#62766E';ctx.fillText(v.toFixed(0)+'°',pad.left-7,y+4);
    }
    [['temperature_min_c','#28718A',1.25],['temperature_max_c','#87A538',1.25],['temperature_mean_c',historyColors[i],2.9]].forEach(([key,color,thickness])=>{
      ctx.strokeStyle=color;ctx.lineWidth=thickness;ctx.lineCap='round';ctx.lineJoin='round';ctx.beginPath();
      let begun=false;
      data.days.forEach((point,index)=>{
        const v=point[key];if(!Number.isFinite(v)){begun=false;return;}
        const x=pad.left+(dates.length===1?pw/2:index/(dates.length-1)*pw);
        const y=pad.top+(upper-v)/range*ph;
        if(!begun){ctx.moveTo(x,y);begun=true;}else ctx.lineTo(x,y);
      });ctx.stroke();
    });
    ctx.textAlign='center';ctx.fillStyle='#62766E';
    [...new Set([0,Math.floor((dates.length-1)/2),dates.length-1])].forEach(index=>{
      const d=dates[index]?.split('-');if(!d)return;
      const x=pad.left+(dates.length===1?pw/2:index/(dates.length-1)*pw);
      ctx.fillText(d[2]+'/'+d[1],x,h-12);
    });
  });
}
function exportHistoryCSV() {
  if(!historyState.mainData)return;
  const rows=[['fonte','data','cidade_1','media_c','minima_c','maxima_c','cidade_2','media_cidade_2_c','minima_cidade_2_c','maxima_cidade_2_c']];
  const comparison=new Map((historyState.compareData?.days || []).map(p=>[p.date,p]));
  for(const day of historyState.mainData.days){
    rows.push([historyIsDemo?'SINTETICO_DEMO':'Open-Meteo ERA5',day.date,cityName(historyState.main),day.temperature_mean_c,day.temperature_min_c,day.temperature_max_c,
      historyState.compare ? cityName(historyState.compare) : '',comparison.get(day.date)?.temperature_mean_c ?? '',comparison.get(day.date)?.temperature_min_c ?? '',comparison.get(day.date)?.temperature_max_c ?? '']);
  }
  // Prefixo de célula impede fórmulas CSV ao abrir em softwares de planilha.
  const safe = v => {let s=String(v??'');if(/^[=+@\-\t\r]/.test(s) && typeof v!=='number')s="'"+s;return '"'+s.replaceAll('"','""')+'"';};
  const csv='\uFEFF'+rows.map(row=>row.map(safe).join(';')).join('\r\n');
  const blob=new Blob([csv],{type:'text/csv;charset=utf-8'}),url=URL.createObjectURL(blob);
  const a=document.createElement('a');a.href=url;a.download=`sombraviva-${historyIsDemo?'DEMO-FICTICIO':'era5'}-${$('history-start').value}-${$('history-end').value}.csv`;
  document.body.appendChild(a);a.click();a.remove();URL.revokeObjectURL(url);
}
$('history-city-search-button').addEventListener('click',()=>searchHistoryLocation('main'));
$('compare-city-search-button').addEventListener('click',()=>searchHistoryLocation('compare'));
$('history-city-results').addEventListener('change',()=>applyHistoryCity('main'));
$('compare-city-results').addEventListener('change',()=>applyHistoryCity('compare'));
$('remove-compare').addEventListener('click',()=>{
  historyState.compare=null;historyState.compareData=null;
  $('compare-city-selected').textContent='Nenhuma comparação selecionada';$('remove-compare').classList.add('hidden');
  queryHistory();
});
$('history-form').addEventListener('submit',ev=>{ev.preventDefault();queryHistory();});
document.querySelectorAll('[data-history-period]').forEach(button=>{
  button.addEventListener('click',()=>{chooseHistoryDates(button.dataset.historyPeriod);queryHistory();});
});
$('history-download').addEventListener('click',exportHistoryCSV);
window.addEventListener('sombraviva:choose-osasco', () => {
  historyState.main = {name:'Osasco',state:'São Paulo',country:'Brasil',latitude:-23.5329,longitude:-46.7917};
  $('history-city-search').value='Osasco';
  $('history-city-selected').textContent='Selecionada: Osasco, São Paulo, Brasil';
  $('history-city-results').classList.add('hidden');
  if (historyState.compare && Math.abs(historyState.compare.latitude+23.5329)<0.001 && Math.abs(historyState.compare.longitude+46.7917)<0.001) {
    historyState.compare=null; historyState.compareData=null;
    $('compare-city-selected').textContent='Nenhuma comparação selecionada';$('remove-compare').classList.add('hidden');
  }
  queryHistory();
});
chooseHistoryDates('30');
queryHistory();

$('weather-retry').addEventListener('click',()=>loadWeather());
$('history-retry').addEventListener('click',()=>queryHistory());
$('refresh').addEventListener('click',()=>{loadClimate();loadWeather();});
$('demo-retry-live')?.addEventListener('click',loadClimate);
window.addEventListener('resize',()=>{drawChart();drawHistoryChart();drawIndividualCityCharts();});
loadClimate();loadWeather();
})();
