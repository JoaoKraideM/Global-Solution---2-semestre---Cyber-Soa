/* Atlas térmico demonstrativo. Valores SINTÉTICOS, sem relação com ERA5/IoT. */
(() => {
'use strict';
const $=id=>document.getElementById(id);
const main=$('heatmap-canvas');
const admin=$('admin-heatmap-canvas');
if(!main&&!admin)return;
let state=null;
function hex(rgb){return `rgb(${rgb.map(v=>Math.round(v)).join(',')})`;}
const stops=[[35,166,143],[193,225,109],[249,198,68],[237,116,58],[174,44,38]];
function color(t){
  t=Math.max(0,Math.min(1,t));const x=t*(stops.length-1),i=Math.min(stops.length-2,Math.floor(x)),f=x-i;
  return hex(stops[i].map((v,k)=>v+(stops[i+1][k]-v)*f));
}
function paint(canvas, data){
  if(!canvas||!data)return;
  const rect=canvas.getBoundingClientRect(),width=rect.width,height=rect.height;
  if(!width||!height)return;
  const pixelRatio=Math.min(devicePixelRatio||1,2);
  canvas.width=Math.round(width*pixelRatio);canvas.height=Math.round(height*pixelRatio);
  const ctx=canvas.getContext('2d');ctx.scale(pixelRatio,pixelRatio);
  ctx.fillStyle='#09282b';ctx.fillRect(0,0,width,height);
  const pad={l:20,r:20,t:24,b:26};const w=width-pad.l-pad.r,h=height-pad.t-pad.b;
  const grid=data.grid, min=data.range.minimum,max=data.range.maximum,span=Math.max(.1,max-min);
  for(let i=0;i<grid.rows;i++)for(let j=0;j<grid.columns;j++){
    const point=grid.points[i*grid.columns+j];
    const x=pad.l+j*w/grid.columns,y=pad.t+i*h/grid.rows;
    const v=(point.temperature_c-min)/span;
    ctx.fillStyle=color(v);ctx.globalAlpha=.89;
    ctx.fillRect(x-.3,y-.3,w/grid.columns+.7,h/grid.rows+.7);
  }
  ctx.globalAlpha=1;
  ctx.lineWidth=.5;ctx.strokeStyle='rgba(241,238,223,.2)';
  for(let j=0;j<=6;j++){const x=pad.l+j*w/6;ctx.beginPath();ctx.moveTo(x,pad.t);ctx.lineTo(x,pad.t+h);ctx.stroke();}
  for(let i=0;i<=5;i++){const y=pad.t+i*h/5;ctx.beginPath();ctx.moveTo(pad.l,y);ctx.lineTo(pad.l+w,y);ctx.stroke();}
  ctx.strokeStyle='rgba(255,255,255,.66)';ctx.lineWidth=1;ctx.strokeRect(pad.l,pad.t,w,h);
  const b=data.bounds;
  for(const place of data.places){
    const x=pad.l+(place.longitude-b.west)/(b.east-b.west)*w;
    const y=pad.t+(b.north-place.latitude)/(b.north-b.south)*h;
    ctx.fillStyle='#062324';ctx.beginPath();ctx.arc(x,y,8,0,Math.PI*2);ctx.fill();
    ctx.fillStyle='#FAF7E7';ctx.beginPath();ctx.arc(x,y,4,0,Math.PI*2);ctx.fill();
    const label=place.code==='calcadao'?'Calçadão':'Parque';
    ctx.font='600 12px system-ui,sans-serif';const metrics=ctx.measureText(label);
    const right=x>width/2;
    const tx=right?x-metrics.width-17:x+15;
    ctx.fillStyle='rgba(4,28,28,.91)';ctx.fillRect(tx-4,y-13,metrics.width+8,19);
    ctx.fillStyle='#F8F0DA';ctx.fillText(label,tx,y+1);
  }
  ctx.fillStyle='#F4F0DA';ctx.font='11px system-ui,sans-serif';
  ctx.fillText(`${b.north.toFixed(3)}°`,pad.l,pad.t-7);
  ctx.textAlign='right';ctx.fillText(`${b.south.toFixed(3)}°`,pad.l+w,pad.t+h+18);
  ctx.textAlign='left';
}
function status(msg,error=false){
  for(const id of ['heatmap-status','admin-heatmap-status']){
    if($(id)){$(id).textContent=msg;$(id).classList.toggle('is-error',error);}
  }
}
async function refresh(){
  const period=$('heatmap-period')?.value||'tarde';
  status('Carregando grade térmica fictícia…');
  try{
    const response=await fetch(`/api/v1/heatmap/demo?period=${encodeURIComponent(period)}`,{cache:'no-store'});
    if(!response.ok)throw new Error(`HTTP ${response.status}`);
    const data=await response.json();
    if(data.simulated!==true||data.source!=='synthetic_demo'||!data.grid?.points?.length)throw new Error('Resposta sem proveniência demonstrativa');
    state=data;paint(main,state);paint(admin,state);
    if($('heatmap-min'))$('heatmap-min').textContent=`${state.range.minimum.toFixed(1).replace('.',',')} °C`;
    if($('heatmap-max'))$('heatmap-max').textContent=`${state.range.maximum.toFixed(1).replace('.',',')} °C`;
    status(`SIMULAÇÃO: ${data.grid.rows*data.grid.columns} células, ${period==='tarde'?'tarde':'noite'} hipotética. Nenhum valor medido.`);
  }catch(error){status('Não foi possível carregar a grade demonstrativa. Verifique se a API está ativa e tente novamente. ('+error.message+')',true);}
}
$('heatmap-refresh')?.addEventListener('click',refresh);
$('heatmap-period')?.addEventListener('change',refresh);
if(typeof ResizeObserver!=='undefined'){
  const ro=new ResizeObserver(()=>{if(state){paint(main,state);paint(admin,state);}});
  for(const c of [main,admin])if(c)ro.observe(c);
}else window.addEventListener('resize',()=>{if(state){paint(main,state);paint(admin,state);}});
refresh();
})();
