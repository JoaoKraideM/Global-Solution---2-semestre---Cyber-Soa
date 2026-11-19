(() => {
'use strict';
const $ = id => document.getElementById(id);
let token = null;
let currentTab = 'alerts';
let eventsOffset = 0;
let eventTotal = 0;
const pageSize = 20;
const labels = {
  category:{login:'Login',iot_auth:'Credencial IoT',taint:'Fluxo de dados'},
  severity:{high:'Alta',medium:'Média',low:'Baixa',info:'Informativa'},
  triage:{new:'Nova',investigating:'Em investigação',resolved:'Resolvida'},
  outcome:{blocked:'Bloqueado',failed:'Recusado',success:'Autorizado'}
};
const nameFor = (type, value) => labels[type]?.[value] || value || '—';
const fmtDate = value => {
  if(!value) return 'Sem registro';
  const d = new Date(value); return Number.isNaN(d.valueOf()) ? 'Sem data válida' : d.toLocaleString('pt-BR');
};
async function request(url, options = {}) {
  const headers = { ...(options.headers || {}) };
  if(token) headers.Authorization = `Bearer ${token}`;
  const response = await fetch(url, { ...options, headers, cache: 'no-store' });
  let result = await response.json().catch(() => ({}));
  if(!response.ok) {
    if(response.status === 401 && token) logout('Sessão expirada. Faça login novamente.');
    const detail = Array.isArray(result.detail) ? 'Confira os campos informados.' : result.detail;
    throw new Error(detail || `Falha HTTP ${response.status}`);
  }
  return result;
}
function status(id, message, isError = false) {
  const element = $(id); if(!element) return;
  element.textContent = message;
  element.classList.toggle('is-error', isError);
}
function add(tag, className, text) {
  const element = document.createElement(tag);
  if(className) element.className = className;
  if(text !== undefined) element.textContent = String(text);
  return element;
}
function badge(message, type = '') { return add('span', `ops-badge ${type}`, message); }
function empty(message) { return add('p', 'ops-main-empty', message); }
function logout(message = 'Sessão encerrada.') {
  token = null;
  lastSocAlerts = [];
  selectedSocAlertId = null;
  alertsRequestSerial += 1;
  document.body.classList.remove('admin-authenticated');
  $('login-section').classList.remove('hidden'); $('admin-section').classList.add('hidden');
  $('admin-pass').value = '';
  // Remova informações da sessão anterior, não apenas esconda os painéis.
  for(const id of ['event-list','event-detail','soc-alert-list','soc-dossier','finding-list',
                   'device-list','attention-list','remediation-result']){
    $(id)?.replaceChildren();
  }
  auditPlaceholder();
  for(const id of ['open-alerts','failed-logins','rejected-devices','stale-stations','didactic-risk']){
    if($(id)) $(id).textContent='—';
  }
  $('audit-text').value='';
  $('admin-status').textContent='Sessão encerrada. Faça login para consultar eventos.';
  $('session-email').textContent='admin';
  $('source-current').textContent='—';
  status('login-status', message);
}
function switchTab(name, loadData = true) {
  if(!['overview','alerts','events','devices','lab'].includes(name)) return;
  currentTab = name;
  if($('admin-section-select')) $('admin-section-select').value = name;
  document.querySelectorAll('.ops-tab').forEach(button => {
    const active = button.dataset.tab === name;
    button.classList.toggle('active',active);
    button.setAttribute('aria-selected',String(active));
    button.tabIndex=active ? 0 : -1;
    if(active) button.setAttribute('aria-current','page'); else button.removeAttribute('aria-current');
  });
  document.querySelectorAll('.ops-pane').forEach(pane => pane.classList.toggle('hidden',pane.id !== `pane-${name}`));
  if(loadData && name === 'events') void loadEvents();
  if(loadData && name === 'alerts') void loadAlerts();
  if(loadData && name === 'lab') { void loadFindings(); void loadDidacticRisk(); }
}
function eventCard(item, compact = false) {
  const card = add('article','ops-event');
  const row = add('div','ops-event-top');
  row.append(add('strong','ops-event-title',`${nameFor('category', item.category)} · #${item.id}`));
  const meta = add('div','ops-event-meta');
  meta.append(badge(nameFor('severity',item.severity),item.severity === 'high' ? 'warning' : ''));
  meta.append(badge(nameFor('outcome',item.outcome)));
  const actionable=item.outcome==='failed'||item.outcome==='blocked';
  if(actionable)meta.append(badge(nameFor('triage',item.triage_status),item.triage_status==='resolved' ? 'resolved' : ''));
  if(item.is_demo)meta.append(badge('Fictício','demo'));
  row.append(meta);
  card.append(row,add('p','',item.summary));
  card.append(add('span','ops-helper',fmtDate(item.created_at)));
  if(!compact && !actionable) {card.append(add('p','soc-small','Registro informativo: autenticação autorizada. Não exige triagem e não é classificado como alerta.'));}
  if(!compact && actionable) {
    const actions = add('div','ops-event-actions');
    const label = add('label','',`Justificativa ou anotação do evento #${item.id}`);
    const textarea = add('textarea'); textarea.maxLength = 300; textarea.rows = 2;
    textarea.value = item.triage_note || '';
    textarea.placeholder = 'Descreva a verificação feita (sem senhas ou dados pessoais)';
    label.append(textarea); actions.append(label);
    const buttons = add('div','ops-button-row');
    const options = [['investigating','Investigar'],['resolved','Resolver'],['new','Reabrir']];
    options.forEach(([value,text]) => {
      if(value === item.triage_status) return;
      const button = add('button',value==='resolved'?'resolve':'',text); button.type='button';
      button.addEventListener('click',async () => {
        const note = textarea.value.trim();
        if(value === 'resolved' && note.length < 8) {
          status('events-status','Para resolver, escreva uma justificativa com pelo menos oito caracteres.',true);textarea.focus();return;
        }
        button.disabled=true;
        try {
          await request(`/api/v1/admin/events/${item.id}/triage`,{
            method:'PATCH',headers:{'Content-Type':'application/json'},
            body:JSON.stringify({status:value,note})
          });
          status('events-status',`Evento #${item.id}: ${nameFor('triage',value)}. Alteração registrada no histórico.`);
          await Promise.all([loadEvents(),loadOperations()]);
        } catch(error) { status('events-status',error.message,true);button.disabled=false; }
      });
      buttons.append(button);
    });
    const historyButton = add('button','','Ver histórico'); historyButton.type='button';
    const history = add('div','ops-history hidden');
    historyButton.addEventListener('click',async () => {
      const hidden = history.classList.contains('hidden');
      history.classList.toggle('hidden',!hidden);
      if(!hidden)return;
      history.textContent='Consultando alterações...';
      try {
        const actions = await request(`/api/v1/admin/events/${item.id}/history`);
        history.textContent = actions.length ? actions.map(entry=>`${fmtDate(entry.created_at)} — ${nameFor('triage',entry.previous_status)} → ${nameFor('triage',entry.next_status)}${entry.note?'\n'+entry.note:''}`).join('\n\n') : 'Nenhuma ação administrativa registrada neste evento.';
      }catch(error){history.textContent=`Falha na consulta: ${error.message}`;}
    });
    buttons.append(historyButton);actions.append(buttons,history);card.append(actions);
  }
  return card;
}
let lastSocAlerts = [];
function hintList(parent, title, entries) {
  const heading=add('strong','soc-mini-heading',title); parent.append(heading);
  const ul=add('ul','soc-list');
  (entries||[]).forEach(value=>{const li=add('li','',value);ul.append(li);});
  parent.append(ul);
}
let selectedSocAlertId = null;
let alertsRequestSerial = 0;
function renderSocAlert(alert) {
  const row=add('button', `sv-case-row severity-${alert.severity} ${alert.is_demo?'is-demo':''}`);
  row.type='button';
  row.id=`soc-alert-${alert.id}`;
  row.dataset.alertId=String(alert.id);
  row.setAttribute('aria-controls','soc-dossier');
  const active=String(selectedSocAlertId)===String(alert.id);
  row.setAttribute('aria-pressed',String(active));
  row.classList.toggle('is-active',active);
  const line=add('span','sv-case-row-meta');
  line.append(add('span',`sv-tag is-${alert.severity}`,nameFor('severity',alert.severity)),
    add('span','',`${nameFor('category',alert.category)} · ${fmtDate(alert.created_at)}`));
  if(alert.is_demo)line.append(add('span','sv-tag','Fictício'));
  row.append(line,add('strong','sv-case-row-title',alert.title),add('span','sv-case-row-asset',`${nameFor('triage',alert.status)} · ${alert.affected_asset}`));
  row.addEventListener('click',()=>selectSocAlert(alert.id,true));
  return row;
}
function selectSocAlert(id, moveToDossier=false) {
  const alert=lastSocAlerts.find(item=>String(item.id)===String(id));
  if(!alert)return;
  selectedSocAlertId=alert.id;
  document.querySelectorAll('.sv-case-row').forEach(row=>{
    const active=row.dataset.alertId===String(alert.id);
    row.classList.toggle('is-active',active);
    row.setAttribute('aria-pressed',String(active));
  });
  const dossier=$('soc-dossier');
  dossier.replaceChildren();
  const state=add('div','sv-dossier-state');
  state.append(add('span',`sv-tag is-${alert.severity}`,`Gravidade ${nameFor('severity',alert.severity).toLowerCase()}`));
  state.append(badge(nameFor('triage',alert.status),alert.status==='resolved'?'resolved':''));
  if(alert.is_demo)state.append(badge('Caso fictício','demo'));
  state.append(add('span','sv-dossier-stamp',`${nameFor('category',alert.category)} · ${fmtDate(alert.created_at)} · ${alert.related_event_count} sinal(is) no intervalo`));
  dossier.append(state,add('h2','sv-dossier-title',alert.title));
  const grid=add('div','sv-dossier-grid');
  const fact=add('section','sv-dossier-block');
  fact.append(add('h3','','Evidências'),add('p','',alert.observed),add('p','sv-dossier-soft',alert.summary));
  const impact=add('section','sv-dossier-block');
  impact.append(add('h3','','Impacto possível'),add('p','',alert.hypothetical_impact));
  grid.append(fact,impact);
  dossier.append(grid);
  const asset=add('section','sv-dossier-asset');
  asset.append(add('h3','','Serviço associado (não confirmado como comprometido)'),add('strong','',alert.affected_asset),add('p','',alert.affected_status));
  dossier.append(asset);
  const steps=add('section','sv-dossier-block');
  steps.append(add('h3','','Próximos passos'));
  const ol=add('ol','sv-dossier-steps');(alert.next_steps||[]).forEach(v=>ol.append(add('li','',v)));steps.append(ol);
  dossier.append(steps);
  if((alert.evidence_gaps||[]).length){
    const more=add('details','sv-dossier-more');
    more.append(add('summary','','Evidências que ainda faltam'));
    const ul=add('ul','soc-list');alert.evidence_gaps.forEach(v=>ul.append(add('li','',v)));more.append(ul);
    dossier.append(more);
  }
  const actions=add('div','sv-dossier-actions');
  const analyze=add('button','outline-btn','Analisar com IA ou regras');analyze.type='button';
  const logs=add('button','primary-btn','Abrir registro e histórico');logs.type='button';
  const report=add('section','soc-report hidden');report.setAttribute('aria-live','polite');
  analyze.addEventListener('click',async()=>{
    analyze.disabled=true;report.classList.remove('hidden');report.replaceChildren(add('p','','Examinando metadados seguros do registro...'));
    try {
      const result=await request(`/api/v1/admin/security/alerts/${alert.id}/analyze`,{method:'POST'});
      report.replaceChildren();
      const heading=add('div','soc-report-title');
      heading.append(add('strong','',result.ai_used?'Hipótese assistida pela OpenAI':'Hipótese local por regras'),badge('Comprometimento não confirmado'));
      report.append(heading,add('p','soc-small','Interpretação automatizada de metadados mínimos. Não é perícia nem comprovação de invasão.'),add('p','',result.summary),add('p','',`Possível impacto: ${result.possible_impact}`),add('p','soc-small',`Serviço relacionado: ${result.affected_asset}`));
      hintList(report,'Próximas verificações',result.next_steps);
      hintList(report,'Evidências ausentes',result.evidence_gaps);
      report.append(add('p','soc-small',result.note));
    }catch(error){report.replaceChildren(add('p','',`A leitura não pôde ser concluída: ${error.message}`));}
    finally{analyze.disabled=false;}
  });
  logs.addEventListener('click',async()=>{
    $('filter-category').value=alert.category;
    $('filter-severity').value='all';$('filter-status').value='all';
    $('include-demo').checked=!!alert.is_demo;
    eventsOffset=0;switchTab('events');
    const detail=$('event-detail');detail.classList.remove('hidden');detail.replaceChildren(add('p','','Abrindo o registro exato...'));
    try {
      const record=await request(`/api/v1/admin/events/${alert.id}`);
      detail.replaceChildren(add('h4','',`Registro original #${alert.id}`),eventCard(record));
      status('events-status',`Registro #${alert.id} localizado. Decisões ficam registradas no histórico.`);
    }catch(error){detail.replaceChildren(empty(`Falha ao carregar #${alert.id}: ${error.message}`));}
    detail.scrollIntoView({behavior:'smooth',block:'start'});
  });
  actions.append(analyze,logs);dossier.append(actions,report);
  if(moveToDossier && window.matchMedia('(max-width: 920px)').matches) {
    dossier.scrollIntoView({behavior:window.matchMedia('(prefers-reduced-motion: reduce)').matches?'auto':'smooth',block:'start'});
  }
}
function displaySocAlerts(){
  const term=($('soc-search')?.value||'').trim().toLocaleLowerCase('pt-BR');
  const visible=lastSocAlerts.filter(item=>[item.title,item.affected_asset,item.summary,item.id,item.category].some(value=>String(value||'').toLocaleLowerCase('pt-BR').includes(term)));
  $('soc-alert-list').replaceChildren(...(visible.length?visible.map(renderSocAlert):[empty(lastSocAlerts.length?'Nenhum registro corresponde à busca. Limpe o texto ou altere os filtros.':'Nenhum sinal acionável neste período. O sistema não monitora a rede ou o sistema operacional.') ]));
  const current=visible.find(item=>String(item.id)===String(selectedSocAlertId));
  const item=current||visible[0];
  if(item)selectSocAlert(item.id);
  else {
    selectedSocAlertId=null;
    $('soc-dossier').replaceChildren(add('div','sv-dossier-placeholder','Sem dossiê para os filtros atuais. A ausência de alerta não significa ausência de risco.'));
  }
  $('soc-status-text').textContent=`${visible.length} de ${lastSocAlerts.length} ocorrência(s) no arquivo visível · ${$('soc-demo').checked?'incluindo estudos simulados':'apenas sinais registrados'}.`;
}
async function loadAlerts(){
  if(!token)return;
  const serial=++alertsRequestSerial;
  $('soc-alert-list').setAttribute('aria-busy','true');
  $('soc-alert-list').replaceChildren(empty('Consultando arquivo de ocorrências...'));
  $('soc-status-text').textContent='Carregando sinais de segurança da API...';
  const params=new URLSearchParams({hours:$('soc-hours').value,status:$('soc-status').value,
    include_demo:String($('soc-demo').checked)});
  try {
    const result=await request(`/api/v1/admin/security/alerts?${params}`);
    if(serial!==alertsRequestSerial)return;
    lastSocAlerts=result.alerts||[];
    $('soc-alert-list').setAttribute('aria-busy','false');
    displaySocAlerts();
  }catch(error){
    if(serial!==alertsRequestSerial)return;
    $('soc-alert-list').setAttribute('aria-busy','false');
    $('soc-status-text').textContent=`Falha na consulta de alertas: ${error.message}`;
    $('soc-alert-list').replaceChildren(empty('Verifique a API e sua sessão de administrador.'));
    $('soc-dossier').replaceChildren(empty('A consulta falhou. Não é possível apresentar um dossiê confiável neste momento.'));
  }
}
async function loadOperations(){
  if(!token)return;
  const result=await request('/api/v1/admin/operations');
  const c=result.counts;
  // O número operacional inclui falhas recusadas/bloqueadas que ainda exigem revisão.
  let recentAlerts=[];
  try {recentAlerts=(await request('/api/v1/admin/security/alerts?hours=24&status=open')).alerts||[];}
  catch(error) {status('admin-status',`Alertas não disponíveis: ${error.message}`,true);}
  $('open-alerts').textContent=recentAlerts.length;
  $('tab-count-alerts').textContent=recentAlerts.length;
  $('tab-count-devices').textContent=(result.stations||[]).length;
  $('failed-logins').textContent=c.failed_logins_24h;
  $('rejected-devices').textContent=c.rejected_devices_24h;
  $('stale-stations').textContent=c.stale_real_stations;
  $('demo-provenance').textContent=`Base demonstrativa separada: ${c.demo_events} eventos e ${c.demo_findings} achados de exemplo. ${c.simulated_stations} de ${c.stations} estações são simuladas.`;
  renderDevices(result.stations);
  void loadDataSource();
  const pending=recentAlerts.slice(0,5);
  const teaser=pending.map(item=>{
    const node=add('button','soc-feed-button');node.type='button';
    node.append(badge(nameFor('severity',item.severity),item.severity==='high'?'warning':''),
      add('strong','',item.title),add('span','soc-small',item.affected_asset+' · '+fmtDate(item.created_at)));
    if(item.is_demo)node.append(badge('Fictício','demo'));
    node.addEventListener('click',()=>{switchTab('alerts');$('pane-alerts').scrollIntoView({behavior:'smooth',block:'start'});});
    return node;
  });
  $('attention-list').replaceChildren(...(teaser.length?teaser:[empty('Sem alerta observado pendente nas últimas 24 horas. Isso indica ausência de sinais registrados, não uma garantia de segurança.') ]));
  void loadDidacticRisk();
  status('admin-status',`Consulta concluída às ${new Date().toLocaleTimeString('pt-BR')}. Atualização manual; ${c.simulated_stations} estações são de demonstração.`);
}
function renderDevices(stations){
  const list=$('device-list');
  if(!stations.length){list.replaceChildren(empty('Nenhuma estação cadastrada. Execute as migrações e o seed ou registre um dispositivo no backend.'));return;}
  list.replaceChildren(...stations.map(station=>{
    const card=add('article','sv-card ops-device');
    const header=add('header');
    const title=add('div');title.append(add('h2','',station.name),add('code','',station.code));
    const state=station.simulated?'Simulada':station.status==='recent'?'Leitura recente':'Sem leitura recente';
    header.append(title,badge(state,station.simulated?'demo':station.status==='stale'?'warning':'resolved'));
    const t=station.latest?.temperature_c;
    const temp=add('div','ops-device-temp');
    const big=add('strong',t===undefined?'':t>=32?'risk-alerta':t>=27?'risk-atencao':'risk-normal',t===undefined?'Sem dados':`${t.toLocaleString('pt-BR')} °C`);
    temp.append(big,add('span','',station.setting||''));
    const dl=add('dl');
    [['Última leitura',fmtDate(station.last_seen_at)],['Umidade',station.latest?`${station.latest.humidity_pct.toLocaleString('pt-BR')}%`:'Sem dados'],['Origem',station.simulated?'Exemplo sintético':'Estação cadastrada']].forEach(([label,value])=>{
      const wrapper=add('div');wrapper.append(add('dt','',label),add('dd','',value));dl.append(wrapper);
    });
    card.append(header,temp,dl);return card;
  }));
}
// Fonte do painel público: estações cadastradas (original) ou ESP32 (Wokwi).
function renderDataSource(data){
  const label=data.label||data.source;
  $('source-current').textContent=`No painel: ${label}`;
  const radio=document.querySelector(`input[name="panel-source"][value="${data.source}"]`);
  if(radio)radio.checked=true;
  for(const key of ['estacoes','esp32']){
    const st=data.stats?.[key];
    $(`source-stats-${key}`).textContent=st?`${st.readings} leitura(s) · última: ${fmtDate(st.last_reading_at)}`:'—';
  }
  const by=data.updated_by?` por ${data.updated_by}`:'';
  status('source-status',data.updated_at?`Definida em ${fmtDate(data.updated_at)}${by}.`:'Usando a fonte padrão do servidor.');
}
async function loadDataSource(){
  if(!token)return;
  try{renderDataSource(await request('/api/v1/admin/data-source'));}
  catch(error){status('source-status',`Não foi possível consultar a fonte: ${error.message}`,true);}
}
function eventParams(){
  return new URLSearchParams({category:$('filter-category').value,severity:$('filter-severity').value,
    status:$('filter-status').value,include_demo:String($('include-demo').checked),offset:String(eventsOffset),limit:String(pageSize)});
}
async function loadEvents(){
  if(!token)return;
  $('event-list').replaceChildren(empty('Carregando eventos...'));
  try {
    const data=await request(`/api/v1/admin/events?${eventParams()}`);
    eventTotal=data.total;
    $('event-count').textContent=`${eventTotal} evento(s) correspondem aos filtros — ${$('include-demo').checked?'incluindo demonstrações':'somente registros observados'}.`;
    $('event-list').replaceChildren(...(data.events.length?data.events.map(item=>eventCard(item)):[empty('Nenhuma ocorrência encontrada para esses filtros. Tente outra categoria ou inclua os exemplos fictícios.') ]));
    $('events-prev').disabled=eventsOffset<=0;$('events-next').disabled=eventsOffset+pageSize>=eventTotal;
    $('events-page').textContent=eventTotal?`${eventsOffset+1}–${Math.min(eventTotal,eventsOffset+pageSize)} de ${eventTotal}`:'0 resultados';
  } catch(error){ $('event-list').replaceChildren(empty(error.message)); }
}
async function loadDidacticRisk(){
  if(!token)return;
  try{const result=await request('/api/v1/admin/overview');
    window.dispatchEvent(new CustomEvent('sombraviva:admin-overview',{detail:result}));
    $('didactic-risk').textContent=`${result.risk_citizen_demo}/100`;
    $('risk-explanation').textContent=`${result.risk_method}. Inclui exemplos de demonstração; não representa probabilidade de invasão ou risco climático.`;
  }catch(error){$('didactic-risk').textContent='—';$('risk-explanation').textContent=`Pontuação indisponível: ${error.message}`;}
}
async function loadFindings(){
  if(!token)return;
  try {
    const data=await request(`/api/v1/admin/findings?include_demo=${$('findings-demo').checked}`);
    $('finding-list').replaceChildren(...(data.length?data.map(f=>{
      const node=add('article','ops-event ops-finding');
      const top=add('div','ops-event-top');top.append(add('strong','ops-event-title',f.category.replace('PII/taint:','Dado pessoal: ')));
      top.append(badge(nameFor('severity',f.severity),f.severity==='high'?'warning':''));
      if(f.is_demo) top.append(badge('Fictício','demo'));
      node.append(top,add('p','',`${f.source} → ${f.sink} · ${f.action}`),add('p','',f.remediation));
      node.append(add('small','ops-helper',fmtDate(f.created_at)));return node;
    }):[empty('Nenhum achado registrado. Execute um teste no laboratório ou marque “Exibir exemplos”.') ]));
  }catch(error){$('finding-list').replaceChildren(empty(`Não foi possível carregar os achados: ${error.message}`));}
}
async function refreshAll(){
  if(!token)return;
  $('admin-refresh').disabled=true;
  status('admin-status','Atualizando indicadores a partir dos eventos reais da API...');
  try{await loadOperations();if(currentTab==='alerts')await loadAlerts();if(currentTab==='events')await loadEvents();if(currentTab==='lab')await Promise.all([loadFindings(),loadDidacticRisk()]);}
  catch(error){
    for(const id of ['open-alerts','failed-logins','rejected-devices','stale-stations'])$(id).textContent='Erro';
    $('attention-list').replaceChildren(empty('A API não respondeu. Nenhum indicador foi confirmado; utilize Atualizar dados para tentar novamente.'));
    status('admin-status',`Falha ao consultar o serviço: ${error.message}`,true);
  }
  finally{$('admin-refresh').disabled=false;}
}
$('login-form').addEventListener('submit',async event=>{
  event.preventDefault();status('login-status','Verificando credenciais...');
  const button=$('login-form').querySelector('button[type="submit"]');button.disabled=true;
  try {
    const result=await request('/api/v1/auth/login',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({email:$('admin-email').value,password:$('admin-pass').value})});
    token=result.access_token;$('session-email').textContent=$('admin-email').value;$('admin-pass').value='';$('login-section').classList.add('hidden');$('admin-section').classList.remove('hidden');
    document.body.classList.add('admin-authenticated');
    button.blur();window.scrollTo({top:0,behavior:'instant'});
    switchTab('alerts', false);await refreshAll();
  }catch(error){status('login-status',`Acesso não autorizado: ${error.message}`,true);}
  finally{button.disabled=false;}
});
$('logout').addEventListener('click',()=>logout());
$('admin-refresh').addEventListener('click',refreshAll);
document.querySelectorAll('.ops-tab').forEach(button=>button.addEventListener('click',()=>switchTab(button.dataset.tab)));
$('admin-section-select')?.addEventListener('change',event=>switchTab(event.target.value));
// Abas operáveis também por teclado: setas, Home e End, sem exigir mouse.
document.querySelector('.ops-tabs')?.addEventListener('keydown',event=>{
  if(!['ArrowRight','ArrowLeft','Home','End'].includes(event.key))return;
  const tabs=[...document.querySelectorAll('.ops-tab')];
  const current=tabs.indexOf(document.activeElement);
  if(current===-1)return;
  event.preventDefault();
  const next=event.key==='Home'?0:event.key==='End'?tabs.length-1:(current+(event.key==='ArrowRight'?1:-1)+tabs.length)%tabs.length;
  switchTab(tabs[next].dataset.tab);
  tabs[next].focus();
});
document.querySelectorAll('[data-go]').forEach(button=>button.addEventListener('click',()=>switchTab(button.dataset.go)));
['filter-category','filter-severity','filter-status','include-demo'].forEach(id=>$(id).addEventListener('change',()=>{eventsOffset=0;void loadEvents();}));
$('events-prev').addEventListener('click',()=>{eventsOffset=Math.max(0,eventsOffset-pageSize);void loadEvents();});
$('events-next').addEventListener('click',()=>{if(eventsOffset+pageSize<eventTotal){eventsOffset+=pageSize;void loadEvents();}});
$('findings-demo').addEventListener('change',loadFindings);
$('source-save').addEventListener('click',async()=>{
  const chosen=document.querySelector('input[name="panel-source"]:checked')?.value;
  if(!chosen){status('source-status','Escolha uma das fontes.',true);return;}
  const button=$('source-save');button.disabled=true;
  status('source-status','Salvando a fonte do painel...');
  try{
    const data=await request('/api/v1/admin/data-source',{method:'PUT',headers:{'Content-Type':'application/json'},body:JSON.stringify({source:chosen})});
    renderDataSource(data);
    const empty=(data.stats?.[chosen]?.readings||0)===0;
    status('source-status',`Painel público agora usa: ${data.label}. ${empty?'Atenção: essa fonte ainda não tem leituras; o painel mostrará valores fictícios identificados até chegar a primeira.':'Recarregue o painel para ver a mudança.'}`,empty);
  }catch(error){status('source-status',`Não foi possível salvar: ${error.message}`,true);}
  finally{button.disabled=false;}
});
['soc-hours','soc-status','soc-demo'].forEach(id=>$(id).addEventListener('change',loadAlerts));
$('soc-search').addEventListener('input',displaySocAlerts);
$('demo-tour').addEventListener('click',()=>{
  $('soc-demo').checked=true;
  $('soc-hours').value='168';
  $('soc-search').value='';
  switchTab('alerts');
});
$('soc-seed').addEventListener('click',async()=>{
  const button=$('soc-seed');button.disabled=true;
  status('soc-status-text','Cadastrando apenas eventos fictícios para demonstração...');
  try{
    const result=await request('/api/v1/admin/security/demo-scenario',{method:'POST'});
    $('soc-demo').checked=true;
    await loadAlerts();
    status('soc-status-text',`${result.notice} Exibindo cenários fictícios junto dos registros observados, devidamente identificados.`);
  }catch(error){status('soc-status-text',error.message,true);}finally{button.disabled=false;}
});
const SINKS={log_bruto:'Log bruto',resposta_publica:'Resposta pública',servico_externo:'Serviço externo',log_redigido:'Log redigido',banco_parametrizado:'Banco parametrizado'};
const PII_NAMES={cpf:'CPF',email:'E-mail',telefone:'Telefone',senha:'Senha',saude:'Dado de saúde',cartao:'Cartão'};
const SVG_NS='http://www.w3.org/2000/svg';
function svgEl(tag,attrs,text){const el=document.createElementNS(SVG_NS,tag);Object.entries(attrs).forEach(([k,v])=>el.setAttribute(k,String(v)));if(text!==undefined)el.textContent=text;return el;}
function auditPlaceholder(){
  const box=$('audit-result'); if(!box)return;
  box.className='sv-card ops-result';
  const empty=add('div','ops-result-empty');
  empty.append(add('h2','','Resultado da auditoria'),add('p','','Escolha um destino e clique em Executar auditoria. O resultado mostra o caminho do dado, a gravidade e o que fazer.'));
  box.replaceChildren(empty);
}
// Card do resultado: cabeçalho de status, diagrama Entrada → Proteção → Destino, dados, prévia e recomendação.
function renderAudit(result){
  const box=$('audit-result');
  const blocked=!!result.blocked;
  const accent=blocked?'#8A1832':'#2F7A4F';
  const sink=SINKS[result.sink]||result.sink;
  box.className=`sv-card ops-result ${blocked?'is-blocked':'is-safe'}`;
  const head=add('div','ops-result-head');
  const icon=svgEl('svg',{viewBox:'0 0 44 44','aria-hidden':'true'});
  icon.append(svgEl('path',{d:'M22 6l14 5v10c0 9-6 15-14 17-8-2-14-8-14-17V11l14-5z',fill:'rgba(255,255,255,.18)',stroke:'#FFFFFF','stroke-width':2.4,'stroke-linejoin':'round'}),
    svgEl('path',{d:blocked?'M16.5 16.5 L27.5 27.5 M27.5 16.5 L16.5 27.5':'M15.5 22.5 L20.5 27.5 L29 17.5',fill:'none',stroke:'#FFFFFF','stroke-width':2.8,'stroke-linecap':'round','stroke-linejoin':'round'}));
  const titles=add('div');
  titles.append(add('span','','Resultado da auditoria'),add('h2','',blocked?`Vazamento bloqueado antes do ${sink.toLowerCase()}`:(result.pii_types.length?'Fluxo seguro: o dado chega protegido':'Nenhum dado pessoal encontrado')));
  head.append(icon,titles);
  const body=add('div','ops-result-body');
  const fig=add('figure','ops-result-flow');
  const svg=svgEl('svg',{viewBox:'0 0 460 108',role:'img','aria-label':blocked?`Fluxo: o texto é redigido e o envio para ${sink.toLowerCase()} é bloqueado`:`Fluxo: o texto passa pela redação e chega protegido ao ${sink.toLowerCase()}`});
  const types=result.pii_types.map(t=>PII_NAMES[t]||t);
  const dash=blocked?'5 4':'0';
  svg.append(
    svgEl('rect',{x:0,y:8,width:100,height:64,rx:12,fill:'#FFFFFF',stroke:'#C9C2B2','stroke-width':1.5}),
    svgEl('text',{x:50,y:36,'text-anchor':'middle','font-size':13,'font-weight':700,fill:'#1E2326'},'Texto'),
    svgEl('text',{x:50,y:53,'text-anchor':'middle','font-size':11.5,fill:'#5C6569'},(types.join(', ')||'Sem PII').slice(0,16)),
    svgEl('path',{d:'M100 40 H124',stroke:'#1E2326','stroke-width':2}),
    svgEl('path',{d:'M123 34 L130 40 L123 46',fill:'none',stroke:'#1E2326','stroke-width':2,'stroke-linecap':'round','stroke-linejoin':'round'}),
    svgEl('rect',{x:132,y:8,width:104,height:64,rx:12,fill:'#0F3D3A'}),
    svgEl('text',{x:184,y:36,'text-anchor':'middle','font-size':13,'font-weight':700,fill:'#FFFFFF'},'Redação'),
    svgEl('text',{x:184,y:53,'text-anchor':'middle','font-size':11.5,fill:'#B9E2B0'},'[REDACTED]'),
    svgEl('path',{d:'M236 40 H284',stroke:accent,'stroke-width':2,'stroke-dasharray':dash}),
    svgEl('path',{d:'M283 34 L290 40 L283 46',fill:'none',stroke:accent,'stroke-width':2,'stroke-linecap':'round','stroke-linejoin':'round'}),
    svgEl('circle',{cx:264,cy:40,r:12,fill:accent}),
    svgEl('path',{d:blocked?'M259.5 35.5 L268.5 44.5 M268.5 35.5 L259.5 44.5':'M258 40 L262 44 L270 35',fill:'none',stroke:'#FFFFFF','stroke-width':2.4,'stroke-linecap':'round','stroke-linejoin':'round'}),
    svgEl('rect',{x:292,y:8,width:168,height:64,rx:12,fill:blocked?'#FBEAEA':'#E4F3E8',stroke:accent,'stroke-width':1.5,'stroke-dasharray':dash}),
    svgEl('text',{x:376,y:36,'text-anchor':'middle','font-size':13,'font-weight':700,fill:blocked?'#8A1832':'#14432A'},sink),
    svgEl('text',{x:376,y:53,'text-anchor':'middle','font-size':11.5,fill:blocked?'#8A1832':'#14432A'},blocked?'Envio bloqueado':'Só a versão redigida'));
  const caps=svgEl('g',{'font-size':12,'font-weight':600,fill:'#5C6569','text-anchor':'middle'});
  caps.append(svgEl('text',{x:50,y:98},'Entrada'),svgEl('text',{x:184,y:98},'Proteção'),svgEl('text',{x:376,y:98},'Destino'));
  svg.append(caps);fig.append(svg);
  const dl=add('dl','ops-result-facts');
  const tile=(label,node,wide)=>{const d=add('div',wide?'is-wide':'');d.append(add('dt','',label));const dd=add('dd');dd.append(node);d.append(dd);return d;};
  const chips=add('span','ops-chips');(types.length?types:['Nenhum']).forEach(t=>chips.append(add('span','sv-tag is-low',t)));
  dl.append(tile('Dados detectados',chips,true),
    tile('Gravidade',add('span',`sv-tag is-${result.severity}`,nameFor('severity',result.severity))),
    tile('Ação',add('span',`sv-tag ${blocked?'is-bad':'is-ok'}`,blocked?'Bloqueado e redigido':'Permitido')));
  const prev=add('div','ops-result-preview');
  prev.append(add('span','','Prévia guardada no servidor'),add('code','',result.redacted_preview),add('small','','O texto original nunca é guardado.'));
  const fix=add('div','ops-result-fix');
  fix.append(add('strong','','O que fazer'),add('p','',result.remediation));
  body.append(fig,dl,prev,fix);
  box.replaceChildren(head,body);
}
$('audit-button').addEventListener('click',async()=>{
  const box=$('audit-result');box.setAttribute('aria-busy','true');$('audit-button').disabled=true;
  const sink=document.querySelector('input[name="audit-sink"]:checked')?.value||'log_bruto';
  try{
    const result=await request('/api/v1/admin/audit',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({sample_text:$('audit-text').value,source:'formulario',sink})});
    renderAudit(result);
    await loadOperations();await loadFindings();
  }catch(error){
    box.className='sv-card ops-result';
    const err=add('div','ops-result-empty');err.append(add('h2','','Resultado da auditoria'),add('p','form-status is-error',error.message));
    box.replaceChildren(err);
  }
  finally{box.setAttribute('aria-busy','false');$('audit-button').disabled=false;}
});
$('remediation-button').addEventListener('click',async()=>{
  status('remediation-result','Preparando explicação...');$('remediation-button').disabled=true;
  try{const result=await request('/api/v1/admin/remediation',{method:'POST'});status('remediation-result',`${result.ai_used?'Explicação por modelo de linguagem':'Orientação por regras locais'}: ${result.message}`);}
  catch(error){status('remediation-result',error.message,true);}
  finally{$('remediation-button').disabled=false;}
});
})();
