import os, sys
d = sys.argv[1] if len(sys.argv) > 1 else '.'
def rd(n): return open(os.path.join(d, n), encoding='utf-8').read()
def wr(n, s): open(os.path.join(d, n), 'w', encoding='utf-8').write(s)
def rep1(s, old, new):
    assert s.count(old) == 1, (old[:70], s.count(old))
    return s.replace(old, new, 1)

CSS = r"""
.rank-cta{display:inline-block;margin-top:14px;padding:12px 18px;border-radius:999px;background:#FF6B1A;color:#fff;font-weight:700;text-decoration:none;font-size:15px;}
.rk-tools{display:flex;flex-wrap:wrap;gap:8px;margin:6px 0 10px;align-items:center;}
.rk-tools input[type=search],.rk-tools select{font-size:15px;padding:10px 12px;border:1px solid #ddd;border-radius:10px;background:#fff;color:#111;min-width:0;}
.rk-tools input[type=search]{flex:1 1 220px;}
.rk-tools label{font-size:14px;display:flex;gap:6px;align-items:center;}
.rk-status{font-size:13px;color:#666;margin:4px 0 10px;}
.rk-list{display:flex;flex-direction:column;gap:6px;}
.rk-row{display:grid;grid-template-columns:34px 1fr auto;grid-template-areas:'n name price' 'n meta var';gap:2px 10px;align-items:center;padding:10px 12px;border:1px solid #e6e6e6;border-radius:12px;background:#fff;color:#111;text-decoration:none;}
.rk-row:hover{border-color:#FF6B1A;}
.rk-n{grid-area:n;font-weight:800;color:#999;text-align:center;}
.rk-row:nth-child(-n+3) .rk-n{color:#FF6B1A;}
.rk-name{grid-area:name;font-weight:700;font-size:15px;overflow:hidden;text-overflow:ellipsis;}
.rk-meta{grid-area:meta;font-size:12px;color:#777;}
.rk-price{grid-area:price;font-weight:800;font-size:16px;text-align:right;white-space:nowrap;}
.rk-var{grid-area:var;text-align:right;font-size:12px;font-weight:700;white-space:nowrap;}
.rk-down{color:#0a7a3d;}
.rk-up{color:#D5443B;}
.rk-flat{color:#999;font-weight:500;}
"""

VIEW = """  <!-- ============ VUE CLASSEMENT ============ -->
  <div id="view-rank" style="display:none">
    <section class="hero" style="padding-bottom:8px">
      <h1>Classement des prix</h1>
      <p class="reassure">Tous les articles de tous les magasins, du moins cher au plus cher. ▼ le prix a baissé · ▲ le prix a augmenté.</p>
    </section>
    <div class="rk-tools">
      <input id="rank-q" type="search" placeholder="Filtrer : produit, marque, magasin…">
      <select id="rank-merchant"><option value="">Tous les magasins</option></select>
      <select id="rank-dir"><option value="asc">Du moins cher au plus cher</option><option value="desc">Du plus cher au moins cher</option></select>
      <label><input type="checkbox" id="rank-drops"> Seulement les baisses</label>
    </div>
    <p id="rank-status" class="rk-status"></p>
    <div id="rank-list" class="rk-list"></div>
  </div>

"""

JS = r"""/* ---------- Classement des prix (temps réel) ---------- */
let _rankTimer = null;
const _rankState = { q: '', merchant: '', drops: false, dir: 'asc', updated: Date.now() };
function _lastChanges(){
  const m = {};
  (priceHistory || []).forEach(h => { const c = m[h.offer_id]; if(!c || new Date(h.changed_at) > new Date(c.changed_at)) m[h.offer_id] = h; });
  return m;
}
async function refreshRankData(){
  try{
    const hd = { apikey: SUPABASE_ANON_KEY, Authorization: 'Bearer ' + SUPABASE_ANON_KEY };
    const [a, b] = await Promise.all([
      fetch(SUPABASE_URL + '/rest/v1/public_price_matrix?select=*', { headers: hd }),
      fetch(SUPABASE_URL + '/rest/v1/price_history?select=*', { headers: hd })
    ]);
    if(a.ok) allOffers = await a.json();
    if(b.ok) priceHistory = await b.json();
    _rankState.updated = Date.now();
  }catch(e){}
}
function renderRanking(){
  const box = document.getElementById('rank-list');
  if(!box) return;
  const last = _lastChanges();
  let rows = allOffers.slice();
  const q = _rankState.q.trim().toLowerCase();
  if(q) rows = rows.filter(o => (o.product_name + ' ' + (o.brand || '') + ' ' + o.merchant_name).toLowerCase().includes(q));
  if(_rankState.merchant) rows = rows.filter(o => o.merchant_name === _rankState.merchant);
  if(_rankState.drops) rows = rows.filter(o => { const c = last[o.offer_id]; return c && Number(c.new_price_xof) < Number(c.old_price_xof); });
  rows.sort((a, b) => _rankState.dir === 'asc' ? a.price_xof - b.price_xof : b.price_xof - a.price_xof);
  const nDown = allOffers.filter(o => { const c = last[o.offer_id]; return c && Number(c.new_price_xof) < Number(c.old_price_xof); }).length;
  const nUp = allOffers.filter(o => { const c = last[o.offer_id]; return c && Number(c.new_price_xof) > Number(c.old_price_xof); }).length;
  document.getElementById('rank-status').textContent = rows.length + ' offre' + (rows.length > 1 ? 's' : '') + ' · ▼ ' + nDown + ' en baisse · ▲ ' + nUp + ' en hausse · mis à jour à ' + new Date(_rankState.updated).toLocaleTimeString('fr-FR') + ' (actualisation automatique)';
  if(!rows.length){ box.innerHTML = `<div class='empty-state'><strong>Aucune offre</strong>Essaie un autre filtre.</div>`; return; }
  box.innerHTML = rows.map((o, i) => {
    const c = last[o.offer_id];
    let v = `<span class='rk-flat' title='Prix stable'>– stable</span>`;
    if(c){
      const diff = Number(c.new_price_xof) - Number(c.old_price_xof);
      const pct = Math.round(Math.abs(diff) / Math.max(1, Number(c.old_price_xof)) * 100);
      const dt = new Date(c.changed_at).toLocaleDateString('fr-FR');
      if(diff < 0) v = `<span class='rk-down' title='Baisse du ${dt}'>▼ ${fmtPrice(-diff)} (-${pct}%)</span>`;
      else if(diff > 0) v = `<span class='rk-up' title='Hausse du ${dt}'>▲ +${fmtPrice(diff)} (+${pct}%)</span>`;
    }
    return `<a class='rk-row' href='/produit/${_esc(o.product_id)}'><span class='rk-n'>${i + 1}</span><span class='rk-name'>${_esc(o.product_name)}</span><span class='rk-price'>${fmtPrice(o.price_xof)}</span><span class='rk-meta'>${_esc(o.merchant_name)}</span><span class='rk-var'>${v}</span></a>`;
  }).join('');
}
function stopRanking(){ if(_rankTimer){ clearInterval(_rankTimer); _rankTimer = null; } }
function startRanking(){
  const sel = document.getElementById('rank-merchant');
  if(sel && sel.options.length <= 1){
    [...new Set(allOffers.map(o => o.merchant_name))].sort((a, b) => a.localeCompare(b)).forEach(n => { const op = document.createElement('option'); op.value = n; op.textContent = n; sel.appendChild(op); });
  }
  renderRanking();
  stopRanking();
  refreshRankData().then(renderRanking);
  _rankTimer = setInterval(() => { if(!document.hidden) refreshRankData().then(renderRanking); }, 60000);
}
document.getElementById('rank-q').addEventListener('input', e => { _rankState.q = e.target.value; renderRanking(); });
document.getElementById('rank-merchant').addEventListener('change', e => { _rankState.merchant = e.target.value; renderRanking(); });
document.getElementById('rank-dir').addEventListener('change', e => { _rankState.dir = e.target.value; renderRanking(); });
document.getElementById('rank-drops').addEventListener('change', e => { _rankState.drops = e.target.checked; renderRanking(); });
const _router0 = router;
router = function(){
  const rv = document.getElementById('view-rank');
  if(location.pathname === '/classement'){
    trackVisit();
    ['view-home', 'view-product', 'view-pro', 'view-compare'].forEach(id => { const e = document.getElementById(id); if(e) e.classList.remove('active'); });
    rv.style.display = 'block';
    document.title = 'Classement des prix — Kasaprix';
    startRanking();
    window.scrollTo(0, 0);
    return;
  }
  rv.style.display = 'none';
  stopRanking();
  _router0();
};
"""

s = rd('index.html')
s = s.replace('</style>', CSS + '</style>', 1)
s = rep1(s, '  <!-- ============ VUE ACCUEIL ============ -->', VIEW + '  <!-- ============ VUE ACCUEIL ============ -->')
s = rep1(s, '<a href="/bons-plans">Bons plans du jour</a>', '<a href="/classement">Classement des prix</a>\n      <a href="/bons-plans">Bons plans du jour</a>')
s = rep1(s, '<div class="chip-row" id="zone-chips" style="margin-top:10px;"></div>', '<div class="chip-row" id="zone-chips" style="margin-top:10px;"></div>\n      <a href="/classement" class="rank-cta">📊 Classement de tous les prix, du moins cher au plus cher</a>')
s = rep1(s, '/* ---------- Routeur (hash) ---------- */', JS + '\n/* ---------- Routeur (hash) ---------- */')
wr('index.html', s)
print('ok3')
