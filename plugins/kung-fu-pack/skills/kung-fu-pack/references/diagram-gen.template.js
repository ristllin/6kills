/*
 * Kung-Fu Pack diagram generator (template).
 *
 * Copy this to the pack's assets/gen.js, set OUT to that assets dir, replace the example
 * diagram(s) with your own, then:  node gen.js   ->  writes <name>.html (+ .min.html).
 * Render each to PNG with headless Chrome (see render-and-publish.md).
 *
 * House rules: dark-mode dataviz palette below; information-carrying diagrams only; NO em or en
 * dashes in any label (use hyphens, "->", middots). Helpers: box(), pill(), arrow()+marker().
 */
const fs = require('fs');
const OUT = __dirname; // set to the pack's assets/ dir

// ---- shared palette (dataviz dark-mode instance) ----
const P = {
  surface: '#1a1a19', plane: '#0d0d0d',
  ink: '#ffffff', ink2: '#c3c2b7', muted: '#898781',
  grid: '#2c2c2a', axis: '#383835',
  blue: '#3987e5',   // platform / neutral
  green: '#199e70',  // live / shipped
  red: '#e66767',    // risk / offensive / gap
  amber: '#d9a441',  // in-flight
  violet: '#9b8cf0', // foundation / external
  border: 'rgba(255,255,255,0.10)',
};
const FONT = "system-ui,-apple-system,'Segoe UI',Roboto,Helvetica,Arial,sans-serif";
function esc(s){return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');}

function fitScript(W,H){
  return `<script>function fit(){var w=document.documentElement.clientWidth||window.innerWidth;var s=w/${W};var el=document.querySelector('.viz');el.style.transform='scale('+s+')';document.body.style.height=(${H}*s)+'px';document.body.style.width=w+'px';}window.addEventListener('resize',fit);fit();</script>`;
}
function shell(W,H,inner){
  return `<!doctype html><html><head><meta charset="utf-8"><style>
*{margin:0;padding:0;box-sizing:border-box}
html,body{margin:0;padding:0;background:${P.plane};overflow:hidden}
.viz{width:${W}px;height:${H}px;background:${P.surface};font-family:${FONT};color:${P.ink};transform-origin:top left;position:relative}
text{font-family:${FONT}}
</style></head><body><div class="viz"><svg width="${W}" height="${H}" viewBox="0 0 ${W} ${H}" xmlns="http://www.w3.org/2000/svg">${inner}</svg></div>${fitScript(W,H)}</body></html>`;
}
function write(name,W,H,inner){
  const html = shell(W,H,inner);
  fs.writeFileSync(`${OUT}/${name}.html`, html);
  fs.writeFileSync(`${OUT}/${name}.min.html`, html.replace(/\n/g,' '));
}

// ---- helpers ----
function box(x,y,w,h,opt){
  opt=opt||{};
  const fill=opt.fill||'rgba(255,255,255,0.04)', stroke=opt.stroke||P.border;
  const sw=opt.sw||1.5, rx=opt.rx!=null?opt.rx:14;
  const dash=opt.dash?`stroke-dasharray="${opt.dash}"`:'';
  return `<rect x="${x}" y="${y}" width="${w}" height="${h}" rx="${rx}" fill="${fill}" stroke="${stroke}" stroke-width="${sw}" ${dash}/>`;
}
function pill(x,y,label,color){
  const w=14+label.length*9.2;
  return `<g><rect x="${x}" y="${y}" width="${w}" height="30" rx="15" fill="${color}22" stroke="${color}" stroke-width="1.4"/>`+
         `<text x="${x+w/2}" y="${y+20}" fill="${color}" font-size="15" font-weight="700" text-anchor="middle">${esc(label)}</text></g>`;
}
function marker(color){
  const id=`ah-${color.replace('#','mk')}`;
  return `<marker id="${id}" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M 0 0 L 10 5 L 0 10 z" fill="${color}"/></marker>`;
}
function arrow(x1,y1,x2,y2,color,opt){
  opt=opt||{};
  const sw=opt.sw||2.6, dash=opt.dash?`stroke-dasharray="${opt.dash}"`:'';
  return `<path d="M ${x1} ${y1} L ${x2} ${y2}" stroke="${color}" stroke-width="${sw}" fill="none" ${dash} marker-end="url(#ah-${color.replace('#','mk')})"/>`;
}

/* ============================================================
   EXAMPLE - a layered stack. Replace with your target's diagrams.
============================================================ */
(function(){
  const W=1600,H=760;
  const layers=[
    { t:'Top layer (value)',   accent:P.blue,  d:'what the reader ultimately cares about',  badge:'delivery', bc:P.blue },
    { t:'Middle layer',        accent:P.amber, d:'the thing that produces the value',        badge:'in-flight', bc:P.amber },
    { t:'Foundation layer',    accent:P.green, d:'the substrate everything is built on',     badge:'LIVE', bc:P.green },
  ];
  const x=60,w=1480,top=150,lh=150,gap=16;
  let svg=`<defs>${marker(P.muted)}</defs>
<text x="60" y="58" fill="${P.ink}" font-size="36" font-weight="800">Example: layered stack</text>
<text x="60" y="94" fill="${P.muted}" font-size="20">Replace this with your target. Each layer builds on the one below.</text>`;
  layers.forEach((L,i)=>{
    const y=top+i*(lh+gap);
    svg+=`${box(x,y,w,lh,{fill:'rgba(255,255,255,0.03)'})}
<rect x="${x}" y="${y}" width="8" height="${lh}" rx="4" fill="${L.accent}"/>
<text x="${x+34}" y="${y+56}" fill="${P.ink}" font-size="27" font-weight="800">${esc(L.t)}</text>
<text x="${x+34}" y="${y+96}" fill="${P.ink2}" font-size="18.5">${esc(L.d)}</text>
${pill(x+w-20-(14+L.badge.length*9.2), y+24, L.badge, L.bc)}`;
    if(i>0) svg+=`<path d="M ${x+w-70} ${y+2} L ${x+w-70} ${y-gap-1}" stroke="${P.muted}" stroke-width="2.4" marker-end="url(#ah-${P.muted.replace('#','mk')})"/>`;
  });
  write('01-example-stack',W,H,svg);
})();

console.log('generated diagrams in', OUT);
