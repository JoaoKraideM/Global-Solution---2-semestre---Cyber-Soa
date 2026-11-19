/* SombraViva — painel público com Apache ECharts (servido localmente em /static/vendor). */
(() => {
'use strict';
const $ = id => document.getElementById(id);
const C = {ink:'#1E2326', soft:'#5C6569', line:'#EEEBE4', leaf:'#2F7A4F', canopy:'#0F3D3A', brick:'#C2412A', cold:'#4F74A8',
  t1:'#2D2A6E', t2:'#8E2C8E', t3:'#E0533A', t4:'#F59E2B', t5:'#F9D857', ok:'#3E8E5A', warn:'#D9A21B', alert:'#C2412A', danger:'#8A1832'};
const THERMAL = [C.t1, C.t2, C.t3, C.t4, C.t5];
const FONT = '"Public Sans", system-ui, sans-serif';
const charts = {};
const num = v => Number.isFinite(Number(v)) ? Number(v) : null;
const fmt = (v, s = ' °C', d = 1) => num(v) === null ? '--' : num(v).toFixed(d).replace('.', ',') + s;
const esc = v => String(v ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const hhmm = iso => { const d = new Date(iso); return Number.isNaN(d.getTime()) ? '' : d.toLocaleTimeString('pt-BR', {hour:'2-digit', minute:'2-digit'}); };
const day = iso => { const [y, m, d] = String(iso).split('-'); return d && m ? `${d}/${m}` : iso; };
const RISK = {normal:'Normal', atencao:'Atenção', alerta:'Alerta', perigo:'Perigo'};

async function get(url) {
  const res = await fetch(url, {headers: {Accept: 'application/json'}});
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.detail || `HTTP ${res.status}`);
  return data;
}
function chart(id) {
  const el = $(id);
  if (!el || !window.echarts) return null;
  charts[id] = charts[id] || window.echarts.init(el, null, {renderer: 'canvas'});
  return charts[id];
}
window.addEventListener('resize', () => Object.values(charts).forEach(c => c.resize()));
const tip = (title, rows) => `<div class="sv-tip"><b>${esc(title)}</b>${rows.map(r => `<span><i class="${r[0]}"></i>${esc(r[1])}: ${esc(r[2])}</span><br>`).join('')}</div>`;
function setNotice(id, text, kind = '') { const n = $(id); if (!n) return; n.textContent = text; n.className = 'sv-notice' + (kind ? ` is-${kind}` : ''); }

// Índice de calor (NOAA/Rothfusz), o mesmo cálculo do firmware do ESP32.
function heatIndex(t, rh) {
  if (num(t) === null || num(rh) === null) return null;
  const T = t * 9 / 5 + 32;
  let hi = 0.5 * (T + 61 + (T - 68) * 1.2 + rh * 0.094);
  if ((hi + T) / 2 >= 80) {
    hi = -42.379 + 2.04901523*T + 10.14333127*rh - .22475541*T*rh - .00683783*T*T - .05481717*rh*rh + .00122874*T*T*rh + .00085282*T*rh*rh - .00000199*T*T*rh*rh;
    if (rh < 13 && T >= 80 && T <= 112) hi -= ((13 - rh) / 4) * Math.sqrt((17 - Math.abs(T - 95)) / 17);
    else if (rh > 85 && T >= 80 && T <= 87) hi += ((rh - 85) / 10) * ((87 - T) / 5);
  }
  return (hi - 32) * 5 / 9;
}
const riskOf = hi => hi === null ? null : hi >= 41 ? 'perigo' : hi >= 32 ? 'alerta' : hi >= 27 ? 'atencao' : 'normal';

/* ---------- Sombra x sol ---------- */
let stationSeries = {shade: [], sun: []};
async function loadCompare() {
  let shade, sun, total = null, demo = false, reason = '';
  try {
    const sum = await get('/api/v1/summary');
    const byCode = Object.fromEntries((sum.stations || []).map(s => [s.code, s]));
    if (!byCode['verde-demo'] || !byCode['centro-demo']) throw new Error('estações da sombra e do sol não cadastradas');
    [shade, sun] = await Promise.all(['verde-demo', 'centro-demo'].map(c => get(`/api/v1/stations/${c}/readings?limit=24`)));
    if (!shade.length && !sun.length) throw new Error('sem leituras no banco');
    total = sum.readings_total;
  } catch (err) {
    reason = err.message; demo = true;
    const d = await get('/api/v1/demo/summary');
    shade = d.readings['verde-demo'] || []; sun = d.readings['centro-demo'] || [];
  }
  stationSeries = {shade, sun};
  const ls = shade.at(-1), lu = sun.at(-1);
  const deg = v => fmt(v);
  $('temp-shade').textContent = deg(ls?.temperature_c);
  $('temp-sun').textContent = deg(lu?.temperature_c);
  $('live-shade').textContent = deg(ls?.temperature_c);
  $('live-sun').textContent = deg(lu?.temperature_c);
  $('prob-shade').textContent = deg(ls?.temperature_c);
  $('prob-sun').textContent = deg(lu?.temperature_c);
  $('hum-shade').textContent = `Umidade ${fmt(ls?.humidity_pct, '%', 0)}`;
  const hiSun = heatIndex(lu?.temperature_c, lu?.humidity_pct);
  $('hum-sun').textContent = hiSun === null ? `Umidade ${fmt(lu?.humidity_pct, '%', 0)}` : `Índice de calor ${fmt(hiSun)} · ${RISK[riskOf(hiSun)].toLowerCase()}`;
  const delta = ls && lu ? lu.temperature_c - ls.temperature_c : null;
  const signed = delta === null ? '--' : (delta > 0 ? '+' : '') + fmt(delta);
  $('temp-delta').textContent = signed;
  $('live-delta').textContent = signed;
  $('hero-delta').textContent = delta === null ? 'alguns graus' : fmt(Math.abs(delta));
  $('delta-verdict').textContent = delta === null ? 'Sem par de leituras para comparar' : delta >= 3 ? 'Entre as duas zonas na última leitura: ilha de calor' : delta > 0 ? 'Entre as duas zonas na última leitura: o sol aquece mais' : 'Entre as duas zonas na última leitura: sem diferença relevante';
  const n = Math.min(shade.length, sun.length);
  let over = 0; for (let i = 1; i <= n; i++) if (sun.at(-i).temperature_c - shade.at(-i).temperature_c >= 3) over++;
  $('prob-over').textContent = n ? `${over} de ${n}` : '--';
  const when = hhmm(lu?.measured_at || ls?.measured_at);
  $('hero-updated').textContent = when ? `Última leitura · ${when}` : 'Sem leitura recente';
  $('live-updated').textContent = when ? `Atualizado às ${when}` : 'Aguardando leitura';
  drawHowto(ls?.temperature_c, lu?.temperature_c);
  $('readings-total').textContent = demo ? '0' : String(total ?? '--');
  $('readings-meta').textContent = demo ? 'Banco indisponível · prévia em memória' : 'No banco MySQL';
  const simulated = [ls, lu].some(r => r?.simulated !== false);
  setNotice('data-notice', demo
    ? `Sem dados no banco (${reason}). Valores fictícios gerados em memória, apenas para visualização.`
    : simulated ? 'Leituras de estações simuladas e do ESP32 no Wokwi: são medições de teste, não de sensores instalados no Calçadão.' : 'Leituras das estações cadastradas.', demo ? 'demo' : '');
  const labels = (sun.length >= shade.length ? sun : shade).map(r => hhmm(r.measured_at));
  const c = chart('chart-compare'); if (!c) return;
  const area = (color) => ({color: new window.echarts.graphic.LinearGradient(0, 0, 0, 1, [{offset: 0, color: color + '66'}, {offset: 1, color: color + '00'}])});
  c.setOption({
    textStyle: {fontFamily: FONT}, animationDuration: 900,
    grid: {left: 44, right: 16, top: 12, bottom: 28},
    tooltip: {trigger: 'axis', formatter: ps => tip(ps[0]?.axisValue, ps.map(p => [p.seriesName === 'Sombra' ? 'c-shade' : 'c-sun', p.seriesName, fmt(p.value)]))},
    xAxis: {type: 'category', data: labels, boundaryGap: false, axisLine: {lineStyle: {color: C.line}}, axisLabel: {color: C.soft}},
    yAxis: {type: 'value', scale: true, axisLabel: {color: C.soft, formatter: v => `${v}°`}, splitLine: {lineStyle: {color: C.line}}},
    series: [
      {name: 'Sombra', type: 'line', smooth: true, symbol: 'none', lineStyle: {width: 3, color: C.leaf}, itemStyle: {color: C.leaf}, areaStyle: area('#2F7A4F'), data: shade.map(r => r.temperature_c)},
      {name: 'Sol', type: 'line', smooth: true, symbol: 'none', lineStyle: {width: 3, color: C.brick}, itemStyle: {color: C.brick}, areaStyle: area('#C2412A'), data: sun.map(r => r.temperature_c)},
    ],
  });
}

// Régua "Como ler": posiciona sombra, sol e o limite de +3 °C na mesma escala.
function drawHowto(shade, sun) {
  const sh = num(shade), su = num(sun);
  if (sh === null || su === null) return;
  // Escala com no mínimo 14 °C de largura: pontos próximos não se encostam.
  let lo = Math.min(sh, su) - 3, hi = Math.max(sh, su, sh + 3) + 3;
  if (hi - lo < 14) { const pad = (14 - (hi - lo)) / 2; lo -= pad; hi += pad; }
  const x = v => (40 + (v - lo) / (hi - lo) * 560).toFixed(1);
  const xs = x(sh), xu = x(su), xl = x(sh + 3);
  const set = (id, attrs) => { const el = $(id); if (el) Object.entries(attrs).forEach(([k, v]) => el.setAttribute(k, v)); };
  set('howto-shade', {cx: xs}); set('howto-sun', {cx: xu});
  // Rótulos para fora: o da esquerda termina no ponto, o da direita começa nele.
  const shadeLeft = +xs <= +xu;
  set('howto-shade-label', {x: shadeLeft ? +xs + 14 : +xs - 14, 'text-anchor': shadeLeft ? 'end' : 'start'});
  set('howto-sun-label', {x: shadeLeft ? +xu - 14 : +xu + 14, 'text-anchor': shadeLeft ? 'start' : 'end'});
  set('howto-limit', {x1: xl, x2: xl}); set('howto-limit-label', {x: xl});
  set('howto-under', {x: Math.min(xs, xl), width: Math.abs(xl - xs).toFixed(1)});
  const overW = Math.max(0, xu - xl);
  set('howto-over', {x: xl, width: overW.toFixed(1)});
  set('howto-bracket', {d: `M${xs} 118 V128 H${xu} V118`});
  set('howto-verdict', {x: ((+xs + +xu) / 2).toFixed(1)});
  $('howto-shade-label').textContent = `Sombra ${fmt(sh)}`;
  $('howto-sun-label').textContent = `Sol ${fmt(su)}`;
  const d = su - sh;
  $('howto-verdict').textContent = `Diferença ${(d > 0 ? '+' : '') + fmt(d)}: ${d >= 3 ? 'ilha de calor' : 'abaixo do limite'}`;
  $('howto-svg').setAttribute('aria-label', `Como ler: a sombra marca ${fmt(sh)} e o sol ${fmt(su)}; o limite de ilha de calor fica 3 graus acima da sombra; a diferença de ${fmt(d)} ${d >= 3 ? 'passa' : 'não passa'} desse limite`);
}

/* ---------- Clima agora ---------- */
async function loadWeather() {
  let w, demo = false;
  try { w = await get('/api/v1/weather/osasco'); } catch { w = await get('/api/v1/demo/weather'); demo = true; }
  $('weather-temp').textContent = fmt(w.temperature_c);
  $('weather-meta').textContent = `${demo ? 'Exemplo fictício · sensação' : 'Sensação'} ${fmt(w.apparent_temperature_c)} · umidade ${fmt(w.humidity_pct, '%', 0)}`;
}

/* ---------- ESP32 ---------- */
async function loadEsp() {
  let rows = [];
  try { rows = await get('/api/v1/medicoes?limit=60'); } catch { rows = []; }
  $('esp-total').textContent = String(rows.length);
  $('esp-last').textContent = rows.length ? `Última às ${hhmm(rows[0].medido_em)}` : 'Nenhuma recebida';
  const tbody = $('esp-rows');
  if (rows.length) {
    tbody.replaceChildren(...rows.slice(0, 12).map(r => {
      const tr = document.createElement('tr');
      const cells = [hhmm(r.medido_em), r.zona === 'arborizada' ? 'Sombra' : 'Sol', fmt(r.temperatura), fmt(r.umidade, '%', 0), fmt(r.indice_calor), r.luminosidade === null ? '--' : `${Math.round(r.luminosidade).toLocaleString('pt-BR')} lux`];
      cells.forEach(v => { const td = document.createElement('td'); td.textContent = v; tr.append(td); });
      const td = document.createElement('td'); const pill = document.createElement('span');
      pill.className = `sv-pill risk-${r.nivel_risco || 'normal'}`; pill.textContent = RISK[r.nivel_risco] || '--'; td.append(pill); tr.append(td);
      return tr;
    }));
  }
  // Índice de calor do Calçadão: ESP32 quando houver; senão, calculado da estação do sol.
  const lastSun = rows.find(r => r.zona === 'sem_vegetacao');
  const sunStation = stationSeries.sun.at(-1);
  const hi = lastSun ? num(lastSun.indice_calor) : heatIndex(sunStation?.temperature_c, sunStation?.humidity_pct);
  const risk = lastSun?.nivel_risco || riskOf(hi);
  const rn = $('risk-now'); rn.textContent = risk ? RISK[risk] : '--'; rn.className = risk ? `risk-${risk}` : '';
  const lr = $('live-risk'); lr.textContent = `Risco: ${risk ? RISK[risk].toLowerCase() : '--'}`; lr.className = `sv-pill${risk ? ` risk-${risk}` : ''}`;
  $('risk-now-meta').textContent = lastSun ? `Índice de calor ${fmt(hi)} (ESP32)` : `Índice de calor ${fmt(hi)}, calculado da estação do sol`;
  drawGauge(hi);
  // Ilha de calor: pares (sombra, sol) das leituras do ESP32 ou das estações.
  let pairs = [];
  if (rows.length) {
    const ordered = [...rows].reverse(); let lastShade = null;
    for (const r of ordered) {
      if (r.zona === 'arborizada') lastShade = r;
      else if (lastShade) pairs.push({t: hhmm(r.medido_em), d: r.temperatura - lastShade.temperatura});
    }
  }
  if (!pairs.length) {
    const n = Math.min(stationSeries.shade.length, stationSeries.sun.length);
    for (let i = 0; i < n; i++) pairs.push({t: hhmm(stationSeries.sun[i].measured_at), d: stationSeries.sun[i].temperature_c - stationSeries.shade[i].temperature_c});
  }
  drawIsland(pairs.slice(-24));
}
function drawGauge(hi) {
  const c = chart('chart-gauge'); if (!c) return;
  c.setOption({
    textStyle: {fontFamily: FONT},
    series: [{
      type: 'gauge', min: 15, max: 50, startAngle: 210, endAngle: -30, radius: '96%', center: ['50%', '58%'],
      axisLine: {lineStyle: {width: 16, color: [[(27 - 15) / 35, C.ok], [(32 - 15) / 35, C.warn], [(41 - 15) / 35, C.alert], [1, C.danger]]}},
      pointer: {width: 5, length: '62%', itemStyle: {color: C.ink}}, anchor: {show: true, size: 12, itemStyle: {color: C.ink}},
      axisTick: {show: false},
      splitLine: {show: false},
      axisLabel: {distance: 22, color: C.soft, fontSize: 11, formatter: v => [15, 27, 32, 41, 50].includes(v) ? `${v}°` : ''},
      splitNumber: 35, progress: {show: false},
      detail: {valueAnimation: true, offsetCenter: [0, '40%'], fontSize: 30, fontWeight: 600, fontFamily: FONT, fontWeight: 800, color: C.ink, formatter: v => hi === null ? '--' : `${v.toFixed(1).replace('.', ',')} °C`},
      title: {offsetCenter: [0, '68%'], fontSize: 12, color: C.soft},
      data: [{value: hi === null ? 15 : Math.max(15, Math.min(50, hi)), name: hi === null ? 'Sem leitura' : `Faixa de ${RISK[riskOf(hi)].toLowerCase()} (NOAA)`}],
    }],
  });
}
function drawIsland(pairs) {
  const c = chart('chart-island'); if (!c) return;
  c.setOption({
    textStyle: {fontFamily: FONT}, grid: {left: 44, right: 16, top: 16, bottom: 28},
    tooltip: {trigger: 'axis', formatter: ps => tip(ps[0].axisValue, [['c-heat', 'Diferença', (ps[0].value > 0 ? '+' : '') + fmt(ps[0].value)]])},
    xAxis: {type: 'category', data: pairs.map(p => p.t), axisLabel: {color: C.soft}, axisLine: {lineStyle: {color: C.line}}},
    yAxis: {type: 'value', axisLabel: {color: C.soft, formatter: v => `${v}°`}, splitLine: {lineStyle: {color: C.line}}},
    series: [{type: 'bar', barMaxWidth: 22, data: pairs.map(p => ({value: +p.d.toFixed(1), itemStyle: {borderRadius: [4, 4, 0, 0], color: p.d >= 3 ? C.brick : p.d > 0 ? C.warn : C.leaf}})),
      markLine: {symbol: 'none', silent: true, lineStyle: {color: C.canopy, type: 'dashed', width: 1.5}, label: {show: false}, data: [{yAxis: 3}]}}],
  });
}

/* ---------- Mapa térmico (hipotético) ---------- */
async function loadHeatmap(period = 'tarde') {
  let d;
  try { d = await get(`/api/v1/heatmap/demo?period=${encodeURIComponent(period)}`); } catch (err) { $('heatmap-notice').textContent = `Mapa indisponível: ${err.message}`; return; }
  $('heatmap-notice').textContent = d.notice || $('heatmap-notice').textContent;
  const cols = d.grid.columns, rows = d.grid.rows, pts = d.grid.points;
  const lons = [...new Set(pts.map(p => p.longitude))], lats = [...new Set(pts.map(p => p.latitude))].sort((a, b) => a - b);
  const data = pts.map(p => [lons.indexOf(p.longitude), lats.indexOf(p.latitude), p.temperature_c]);
  const temps = pts.map(p => p.temperature_c);
  const c = chart('chart-heatmap'); if (!c) return;
  c.setOption({
    textStyle: {fontFamily: FONT},
    grid: {left: 8, right: 8, top: 8, bottom: 70, containLabel: false},
    tooltip: {formatter: p => tip('Célula hipotética', [['c-heat', 'Temperatura simulada', fmt(p.value[2])], ['c-min', 'Lat/Lon', `${lats[p.value[1]].toFixed(3)}, ${lons[p.value[0]].toFixed(3)}`]])},
    xAxis: {type: 'category', data: lons.map(v => v.toFixed(3)), show: false},
    yAxis: {type: 'category', data: lats.map(v => v.toFixed(3)), show: false},
    visualMap: {min: Math.floor(Math.min(...temps)), max: Math.ceil(Math.max(...temps)), calculable: true, orient: 'horizontal', left: 'center', bottom: 8,
      inRange: {color: THERMAL}, textStyle: {color: 'rgba(255,255,255,.8)'}, formatter: v => `${Math.round(v)} °C`},
    series: [{type: 'heatmap', data, progressive: 0, emphasis: {itemStyle: {borderColor: '#fff', borderWidth: 1}}}],
  });
  void cols; void rows;
}
document.querySelectorAll('[data-period]').forEach(btn => btn.addEventListener('click', () => {
  document.querySelectorAll('[data-period]').forEach(b => b.setAttribute('aria-pressed', String(b === btn)));
  loadHeatmap(btn.dataset.period);
}));

/* ---------- Histórico ERA5 ---------- */
const hist = {main: {name: 'Osasco', label: 'Osasco, São Paulo, Brasil', latitude: -23.5329, longitude: -46.7917}, compare: null, result: null};
function isoDate(d) { return d.toISOString().slice(0, 10); }
(function initDates() {
  const end = new Date(); end.setDate(end.getDate() - 8);
  const start = new Date(end); start.setDate(start.getDate() - 29);
  $('date-start').value = isoDate(start); $('date-end').value = isoDate(end);
  $('date-start').max = $('date-end').max = isoDate(end);
})();
async function searchCity(which) {
  const input = $(which === 'main' ? 'city-main' : 'city-compare');
  const term = input.value.trim(); const list = $('city-results');
  if (term.length < 2) { setNotice('history-status', 'Digite pelo menos duas letras do nome da cidade.', 'error'); return; }
  let found, demo = false;
  try { found = await get(`/api/v1/weather/places?search=${encodeURIComponent(term)}`); }
  catch { found = await get(`/api/v1/demo/places?search=${encodeURIComponent(term)}`); demo = true; }
  const locs = found.locations || [];
  if (!locs.length) { list.replaceChildren(); setNotice('history-status', `Nenhuma cidade encontrada para “${term}”.`, 'error'); return; }
  setNotice('history-status', demo ? 'Busca offline: coordenadas aproximadas de exemplo.' : 'Escolha a cidade certa na lista.', demo ? 'demo' : '');
  list.replaceChildren(...locs.slice(0, 8).map(l => {
    const li = document.createElement('li'); const b = document.createElement('button'); b.type = 'button';
    const label = [l.name, l.state, l.country].filter(Boolean).join(', ');
    b.textContent = label;
    b.addEventListener('click', () => {
      hist[which] = {name: l.name, label, latitude: l.latitude, longitude: l.longitude};
      $(which === 'main' ? 'city-main-picked' : 'city-compare-picked').textContent = label;
      input.value = l.name; list.replaceChildren(); queryHistory();
    });
    li.append(b); return li;
  }));
}
document.querySelectorAll('[data-search]').forEach(b => b.addEventListener('click', () => searchCity(b.dataset.search)));
['city-main', 'city-compare'].forEach(id => $(id).addEventListener('keydown', e => { if (e.key === 'Enter') { e.preventDefault(); searchCity(id === 'city-main' ? 'main' : 'compare'); } }));
$('city-compare').addEventListener('input', e => { if (!e.target.value.trim()) { hist.compare = null; $('city-compare-picked').textContent = 'Sem comparação'; } });

async function fetchHistory(city, start, end) {
  const q = `latitude=${city.latitude}&longitude=${city.longitude}&start_date=${start}&end_date=${end}`;
  try { return {data: await get(`/api/v1/weather/history?${q}`), demo: false}; }
  catch { return {data: await get(`/api/v1/demo/history?${q}`), demo: true}; }
}
async function queryHistory(event) {
  event?.preventDefault();
  const start = $('date-start').value, end = $('date-end').value;
  if (!start || !end || start > end) { setNotice('history-status', 'Confira as datas: o início precisa ser anterior ao fim.', 'error'); return; }
  setNotice('history-status', 'Consultando o histórico…');
  try {
    const main = await fetchHistory(hist.main, start, end);
    const cmp = hist.compare ? await fetchHistory(hist.compare, start, end) : null;
    hist.result = {main, cmp};
    const demo = main.demo || cmp?.demo;
    setNotice('history-status', demo ? 'Open-Meteo indisponível: série fictícia gerada para demonstração. Não use como dado climático.' : `ERA5 · ${main.data.days.length} dias · ${main.data.note || ''}`.trim(), demo ? 'demo' : '');
    drawHistory();
    $('export-csv').disabled = false;
  } catch (err) { setNotice('history-status', `Não foi possível consultar: ${err.message}`, 'error'); }
}
$('history-form').addEventListener('submit', queryHistory);
function drawHistory() {
  const {main, cmp} = hist.result; const days = main.data.days;
  const c = chart('chart-history'); if (!c) return;
  const labels = days.map(d => day(d.date));
  const mins = days.map(d => d.temperature_min_c), maxs = days.map(d => d.temperature_max_c);
  const series = [
    {name: 'mínima', type: 'line', data: mins, stack: 'band', symbol: 'none', lineStyle: {opacity: 0}, areaStyle: {opacity: 0}, tooltip: {show: false}},
    {name: 'amplitude', type: 'line', data: days.map(d => num(d.temperature_max_c) === null || num(d.temperature_min_c) === null ? null : +(d.temperature_max_c - d.temperature_min_c).toFixed(1)), stack: 'band', symbol: 'none', lineStyle: {opacity: 0}, areaStyle: {color: 'rgba(194,65,42,.08)'}, tooltip: {show: false}},
    {name: `Máxima · ${hist.main.name}`, type: 'line', data: maxs, symbol: 'none', smooth: true, lineStyle: {width: 2, color: C.brick}, itemStyle: {color: C.brick}},
    {name: `Média · ${hist.main.name}`, type: 'line', data: days.map(d => d.temperature_mean_c), symbol: 'none', smooth: true, lineStyle: {width: 3, color: C.canopy}, itemStyle: {color: C.canopy}},
    {name: `Mínima · ${hist.main.name}`, type: 'line', data: mins, symbol: 'none', smooth: true, lineStyle: {width: 2, color: C.cold}, itemStyle: {color: C.cold}},
  ];
  if (cmp) series.push({name: `Média · ${hist.compare.name}`, type: 'line', data: cmp.data.days.map(d => d.temperature_mean_c), symbol: 'none', smooth: true, lineStyle: {width: 3, type: 'dashed', color: C.leaf}, itemStyle: {color: C.leaf}});
  const cls = n => n.startsWith('Máx') ? 'c-max' : n.startsWith('Mín') ? 'c-min' : n.includes(hist.compare?.name || '\u0000') && cmp ? 'c-cmp' : 'c-mean';
  c.setOption({
    textStyle: {fontFamily: FONT}, animationDuration: 700,
    grid: {left: 48, right: 20, top: 46, bottom: 64},
    legend: {top: 10, left: 16, data: series.slice(2).map(s => s.name), textStyle: {color: C.soft}},
    tooltip: {trigger: 'axis', formatter: ps => tip(ps[0]?.axisValue, ps.filter(p => p.seriesName !== 'mínima' && p.seriesName !== 'amplitude').map(p => [cls(p.seriesName), p.seriesName, fmt(p.value)]))},
    dataZoom: [{type: 'inside'}, {type: 'slider', height: 18, bottom: 14, borderColor: 'transparent', fillerColor: 'rgba(15,61,58,.12)'}],
    xAxis: {type: 'category', data: labels, boundaryGap: false, axisLabel: {color: C.soft}, axisLine: {lineStyle: {color: C.line}}},
    yAxis: {type: 'value', scale: true, axisLabel: {color: C.soft, formatter: v => `${v}°`}, splitLine: {lineStyle: {color: C.line}}},
    series,
  }, true);
  const s = main.data.summary || {};
  const items = [['Média do período', fmt(s.mean_temperature_c)], ['Maior máxima', fmt(s.highest_temperature_c)], ['Menor mínima', fmt(s.lowest_temperature_c)], ['Dias com média acima de 30 °C', String(s.days_mean_above_30c ?? '--')]];
  if (cmp) items.push([`Média em ${hist.compare.name}`, fmt(cmp.data.summary?.mean_temperature_c)]);
  $('history-summary').replaceChildren(...items.map(([k, v]) => { const d = document.createElement('div'); const dt = document.createElement('dt'); dt.textContent = k; const dd = document.createElement('dd'); dd.textContent = v; d.append(dt, dd); return d; }));
}
$('export-csv').addEventListener('click', () => {
  if (!hist.result) return;
  const {main, cmp} = hist.result;
  const header = ['data', `media_${hist.main.name}`, `minima_${hist.main.name}`, `maxima_${hist.main.name}`];
  if (cmp) header.push(`media_${hist.compare.name}`, `minima_${hist.compare.name}`, `maxima_${hist.compare.name}`);
  const rows = [header, ...main.data.days.map((d, i) => { const r = [d.date, d.temperature_mean_c, d.temperature_min_c, d.temperature_max_c]; const o = cmp?.data.days[i]; if (cmp) r.push(o?.temperature_mean_c, o?.temperature_min_c, o?.temperature_max_c); return r; })];
  // Prefixo neutraliza fórmulas ao abrir o CSV em planilhas (CSV injection).
  const safe = v => { const t = String(v ?? ''); return /^[=+\-@]/.test(t) ? `'${t}` : t; };
  const csv = '﻿' + (main.demo ? 'SERIE FICTICIA - DEMONSTRACAO\r\n' : '') + rows.map(r => r.map(safe).join(';')).join('\r\n');
  const url = URL.createObjectURL(new Blob([csv], {type: 'text/csv;charset=utf-8'}));
  const a = document.createElement('a'); a.href = url; a.download = `sombraviva_historico_${$('date-start').value}_${$('date-end').value}.csv`; a.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
});

/* ---------- Início ---------- */
async function boot() {
  if (!window.echarts) { setNotice('data-notice', 'A biblioteca de gráficos não carregou. Recarregue a página.', 'error'); return; }
  await loadCompare().catch(err => setNotice('data-notice', `Falha ao carregar as leituras: ${err.message}`, 'error'));
  await Promise.all([loadWeather().catch(() => {}), loadEsp().catch(() => {}), loadHeatmap().catch(() => {})]);
  queryHistory();
  setInterval(() => { loadCompare().then(loadEsp).catch(() => {}); }, 30000);
}
if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', boot); else boot();
})();
