/* Gráficos da central de segurança (Apache ECharts local). Recebe os dados que o admin.js
   já buscou com o token JWT, pelo evento 'sombraviva:admin-overview'; não guarda credenciais. */
(() => {
'use strict';
const C = {ink:'#1E2326', soft:'#5C6569', line:'#EEEBE4', ok:'#3E8E5A', warn:'#D9A21B', alert:'#C2412A', danger:'#8A1832', t1:'#5B4FA0', t2:'#8E2C8E', t4:'#F59E2B', leaf:'#2F7A4F'};
const FONT = '"Public Sans", system-ui, sans-serif';
const charts = {};
let last = null;
const esc = v => String(v ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const CATEGORY = {login: 'Login', iot_auth: 'Dispositivos IoT', taint: 'Fluxo de dados'};
const OUTCOME = {success: 'Sucesso', failed: 'Falha', blocked: 'Bloqueado'};
const SEVERITY = {high: 'Alta', medium: 'Média', low: 'Baixa', info: 'Informativa'};
function chart(id) {
  const el = document.getElementById(id);
  if (!el || !window.echarts || !el.offsetWidth) return null;
  charts[id] = charts[id] || window.echarts.init(el);
  return charts[id];
}
function render() {
  if (!last) return;
  const risk = chart('chart-risk');
  risk?.setOption({
    textStyle: {fontFamily: FONT},
    series: [{type: 'gauge', min: 0, max: 100, startAngle: 210, endAngle: -30, radius: '96%', center: ['50%', '58%'],
      axisLine: {lineStyle: {width: 16, color: [[.3, C.ok], [.6, C.warn], [.8, C.alert], [1, C.danger]]}},
      pointer: {width: 5, length: '62%', itemStyle: {color: C.ink}}, anchor: {show: true, size: 12, itemStyle: {color: C.ink}},
      axisTick: {show: false}, splitLine: {show: false},
      axisLabel: {distance: 22, color: C.soft, fontSize: 11}, splitNumber: 5,
      detail: {valueAnimation: true, offsetCenter: [0, '40%'], fontSize: 30, fontWeight: 800, color: C.ink, formatter: v => `${Math.round(v)}/100`},
      title: {offsetCenter: [0, '68%'], fontSize: 12, color: C.soft},
      data: [{value: last.risk_citizen_demo || 0, name: 'Indicador didático'}]}],
  });
  const events = last.events || [];
  const cats = Object.keys(CATEGORY);
  const outs = Object.keys(OUTCOME);
  const count = (c, o) => events.filter(e => e.category === c && e.outcome === o).length;
  chart('chart-events')?.setOption({
    textStyle: {fontFamily: FONT}, grid: {left: 120, right: 16, top: 34, bottom: 24},
    legend: {top: 0, data: outs.map(o => OUTCOME[o]), textStyle: {color: C.soft}},
    tooltip: {trigger: 'axis', axisPointer: {type: 'shadow'}, formatter: ps => `<div class="sv-tip"><b>${esc(ps[0].axisValue)}</b>${ps.map(p => `<span>${esc(p.seriesName)}: ${esc(p.value)}</span><br>`).join('')}</div>`},
    xAxis: {type: 'value', minInterval: 1, axisLabel: {color: C.soft}, splitLine: {lineStyle: {color: C.line}}},
    yAxis: {type: 'category', data: cats.map(c => CATEGORY[c]), axisLabel: {color: C.ink}},
    series: outs.map((o, i) => ({name: OUTCOME[o], type: 'bar', stack: 'total', barMaxWidth: 26,
      itemStyle: {color: [C.ok, C.warn, C.danger][i]}, data: cats.map(c => count(c, o))})),
  });
  const findings = last.findings || [];
  const sev = Object.keys(SEVERITY).map(k => ({name: SEVERITY[k], value: findings.filter(f => f.severity === k).length})).filter(d => d.value);
  chart('chart-findings')?.setOption({
    textStyle: {fontFamily: FONT},
    tooltip: {formatter: p => `<div class="sv-tip"><b>${esc(p.name)}</b><span>${esc(p.value)} achado(s) · ${esc(p.percent)}%</span></div>`},
    legend: {bottom: 0, textStyle: {color: C.soft}},
    color: [C.danger, C.warn, C.t1, C.leaf],
    series: [{type: 'pie', radius: ['48%', '74%'], center: ['50%', '45%'], label: {formatter: '{c}', color: C.ink, fontWeight: 600},
      itemStyle: {borderColor: '#FFFFFF', borderWidth: 3}, data: sev.length ? sev : [{name: 'Sem achados', value: 0}]}],
  });
}
window.addEventListener('sombraviva:admin-overview', e => { last = e.detail; requestAnimationFrame(render); });
// Os gráficos ficam numa aba oculta: redesenha quando ela aparece ou a janela muda de tamanho.
document.addEventListener('click', e => { if (e.target.closest('[data-tab], [data-go]')) setTimeout(() => { render(); Object.values(charts).forEach(c => c.resize()); }, 60); });
document.getElementById('admin-section-select')?.addEventListener('change', () => setTimeout(() => { render(); Object.values(charts).forEach(c => c.resize()); }, 60));
window.addEventListener('resize', () => Object.values(charts).forEach(c => c.resize()));
})();
