import os, sys
d = sys.argv[1] if len(sys.argv) > 1 else '.'
def rd(n): return open(os.path.join(d, n), encoding='utf-8').read()
def wr(n, s): open(os.path.join(d, n), 'w', encoding='utf-8').write(s)
def rep1(s, old, new):
    assert s.count(old) == 1, (old[:70], s.count(old))
    return s.replace(old, new, 1)

CSS = r"""
.m-extra{display:flex;flex-wrap:wrap;gap:2px 10px;align-items:center;margin-top:4px;font-size:12px;color:#555;}
.m-extra .m-rating{color:#C98A00;}
.m-extra .m-rating strong{color:#222;}
.m-extra .m-rating.m-none{color:#8a8a8a;}
.m-extra .m-deliv{color:#2b6b45;}
.m-review-btn{border:0;background:none;color:#0a7a3d;font-weight:700;font-size:12px;cursor:pointer;padding:0;text-decoration:underline;}
#rev-modal{position:fixed;top:0;right:0;bottom:0;left:0;background:rgba(0,0,0,.5);display:none;align-items:center;justify-content:center;z-index:9999;padding:16px;}
#rev-modal .rev-card{background:#fff;color:#111;border-radius:16px;max-width:440px;width:100%;max-height:90vh;overflow:auto;padding:20px;}
#rev-modal h3{margin:0 0 10px;}
#rev-modal .rev-item{border-top:1px solid #eee;padding:8px 0;font-size:14px;}
#rev-modal .rev-item p{margin:4px 0 0;}
#rev-modal .rev-form{border-top:2px solid #eee;margin-top:12px;padding-top:12px;display:flex;flex-direction:column;gap:8px;}
#rev-modal select,#rev-modal textarea,#rev-modal input{font-size:16px;padding:10px;border:1px solid #ddd;border-radius:10px;width:100%;box-sizing:border-box;}
#rev-modal .rev-send{background:#25D366;color:#fff;border:0;border-radius:10px;padding:12px;font-weight:700;font-size:15px;cursor:pointer;}
#rev-modal .rev-close{margin-top:10px;border:0;background:none;color:#666;cursor:pointer;text-decoration:underline;}
#rev-modal .rev-msg{margin:0;font-size:13px;font-weight:600;}
.ph-box{margin:18px 0;padding:16px;border:1px solid #e5e5e5;border-radius:14px;background:#fff;color:#111;}
.ph-box h3{margin:0 0 4px;font-size:16px;}
.ph-box svg{width:100%;height:150px;display:block;margin:8px 0;background:#F6FBF8;border-radius:8px;}
.ph-box p{margin:2px 0;font-size:13px;}
"""

JS = r"""/* ---------- Avis, livraison, historique des prix ---------- */
let _miP = null;
function _hdr(){ return { apikey: SUPABASE_ANON_KEY, Authorization: 'Bearer ' + SUPABASE_ANON_KEY, 'Content-Type': 'application/json' }; }
function _esc(t){ return String(t == null ? '' : t).replace(/[&<>\x22\x27]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','\x22':'&quot;','\x27':'&#39;'}[c])); }
function _stars(n){ const f = Math.max(0, Math.min(5, Math.round(n))); return '★'.repeat(f) + '☆'.repeat(5 - f); }
async function _rpc(name, body){
  const r = await fetch(SUPABASE_URL + '/rest/v1/rpc/' + name, { method:'POST', headers:_hdr(), body: JSON.stringify(body || {}) });
  if(!r.ok) throw new Error(name + ' ' + r.status);
  return r.json();
}
function loadMerchantInfo(){
  if(!_miP) _miP = (async () => {
    const map = {};
    try{ (await _rpc('public_merchant_info')).forEach(x => { map[x.name] = x; }); }catch(e){}
    return map;
  })();
  return _miP;
}
function merchantExtraHtml(o){ return `<div class='m-extra' data-m='${_esc(o.merchant_name)}'></div>`; }
async function enhanceOffers(offers){
  const info = await loadMerchantInfo();
  document.querySelectorAll('#offers-list .m-extra').forEach(el => {
    const m = info[el.getAttribute('data-m')];
    if(!m) return;
    const rating = Number(m.review_count) > 0
      ? `<span class='m-rating'>${_stars(m.avg_rating)} <strong>${Number(m.avg_rating).toFixed(1)}</strong> (${m.review_count} avis)</span>`
      : `<span class='m-rating m-none'>Pas encore d'avis</span>`;
    const deliv = m.delivery_info ? `<span class='m-deliv'>🚚 ${_esc(m.delivery_info)}</span>` : '';
    el.innerHTML = rating + deliv + `<button type='button' class='m-review-btn'>Voir / donner un avis</button>`;
    el.querySelector('.m-review-btn').onclick = () => openReviewModal(m);
  });
  loadPriceHistory(offers);
}
async function openReviewModal(m){
  let modal = document.getElementById('rev-modal');
  if(!modal){
    modal = document.createElement('div'); modal.id = 'rev-modal'; document.body.appendChild(modal);
    modal.addEventListener('click', e => { if(e.target === modal) modal.style.display = 'none'; });
  }
  modal.innerHTML = `<div class='rev-card'><h3>Avis sur ${_esc(m.name)}</h3><div class='rev-list'>Chargement…</div>
    <div class='rev-form'><strong>Ton avis</strong>
      <select class='rev-rating'><option value='5'>★★★★★ Excellent</option><option value='4'>★★★★☆ Bien</option><option value='3'>★★★☆☆ Moyen</option><option value='2'>★★☆☆☆ Décevant</option><option value='1'>★☆☆☆☆ Mauvais</option></select>
      <textarea class='rev-comment' maxlength='500' rows='3' placeholder='Livraison, qualité, accueil… (facultatif)'></textarea>
      <input class='rev-author' maxlength='60' placeholder='Ton prénom (facultatif)'>
      <button type='button' class='rev-send'>Envoyer mon avis</button><p class='rev-msg'></p></div>
    <button type='button' class='rev-close'>Fermer</button></div>`;
  modal.style.display = 'flex';
  modal.querySelector('.rev-close').onclick = () => { modal.style.display = 'none'; };
  const msg = modal.querySelector('.rev-msg');
  modal.querySelector('.rev-send').onclick = async (ev) => {
    const btn = ev.currentTarget; btn.disabled = true; msg.textContent = '';
    try{
      await _rpc('submit_merchant_review', { p_merchant_id: m.merchant_id, p_rating: Number(modal.querySelector('.rev-rating').value), p_comment: modal.querySelector('.rev-comment').value, p_author: modal.querySelector('.rev-author').value });
      msg.style.color = '#0a7a3d'; msg.textContent = 'Merci ! Ton avis sera publié après vérification.';
      modal.querySelector('.rev-comment').value = '';
    }catch(e){ msg.style.color = '#D5443B'; msg.textContent = `Oups, l'envoi a échoué. Réessaie dans un instant.`; }
    btn.disabled = false;
  };
  try{
    const rows = await _rpc('public_merchant_reviews', { p_merchant_id: m.merchant_id, p_limit: 5 });
    modal.querySelector('.rev-list').innerHTML = rows.length
      ? rows.map(r => `<div class='rev-item'><span style='color:#C98A00'>${_stars(r.rating)}</span> <small>${_esc(r.author_name || 'Client')} · ${new Date(r.created_at).toLocaleDateString('fr-FR')}</small>${r.comment ? '<p>' + _esc(r.comment) + '</p>' : ''}</div>`).join('')
      : `<p>Aucun avis publié pour l'instant. Sois le premier !</p>`;
  }catch(e){ modal.querySelector('.rev-list').innerHTML = ''; }
}
async function loadPriceHistory(offers){
  const old = document.getElementById('price-history'); if(old) old.remove();
  try{
    const ids = offers.map(o => o.offer_id);
    const r = await fetch(SUPABASE_URL + '/rest/v1/price_history?select=offer_id,old_price_xof,new_price_xof,changed_at&order=changed_at.asc&offer_id=in.(' + ids.join(',') + ')', { headers: _hdr() });
    if(!r.ok) return;
    const rows = await r.json();
    if(!rows.length) return;
    const best = offers.reduce((a, b) => a.price_xof <= b.price_xof ? a : b);
    const oid = rows.some(x => x.offer_id === best.offer_id) ? best.offer_id : rows[0].offer_id;
    const mine = rows.filter(x => x.offer_id === oid);
    const cur = offers.find(o => o.offer_id === oid);
    const pts = [{ t: new Date(mine[0].changed_at).getTime() - 86400000, p: Number(mine[0].old_price_xof) }];
    mine.forEach(x => pts.push({ t: new Date(x.changed_at).getTime(), p: Number(x.new_price_xof) }));
    pts.push({ t: Date.now(), p: cur.price_xof });
    const W = 600, H = 150, pad = 8;
    const t0 = pts[0].t, t1 = pts[pts.length - 1].t;
    const prices = pts.map(x => x.p), lo = Math.min(...prices), hi = Math.max(...prices);
    const X = t => pad + (W - 2 * pad) * (t - t0) / Math.max(1, t1 - t0);
    const Y = p => hi === lo ? H / 2 : H - pad - (H - 2 * pad) * (p - lo) / (hi - lo);
    let path = 'M' + X(pts[0].t).toFixed(1) + ' ' + Y(pts[0].p).toFixed(1);
    for(let i = 1; i < pts.length; i++){ path += ' H' + X(pts[i].t).toFixed(1) + ' V' + Y(pts[i].p).toFixed(1); }
    const delta = pts[pts.length - 1].p - pts[0].p;
    const trend = delta < 0 ? `📉 En baisse de ${fmtPrice(-delta)} depuis le début du suivi` : delta > 0 ? `📈 En hausse de ${fmtPrice(delta)} depuis le début du suivi` : 'Prix stable';
    const box = document.createElement('div'); box.id = 'price-history'; box.className = 'ph-box';
    box.innerHTML = `<h3>Historique du prix · ${_esc(cur.merchant_name)}</h3><p>${trend}</p>
      <svg viewBox='0 0 ${W} ${H}' preserveAspectRatio='none' role='img' aria-label='Évolution du prix'><path d='${path}' fill='none' stroke='#0a7a3d' stroke-width='3' vector-effect='non-scaling-stroke'/></svg>
      <p>Plus bas : <strong>${fmtPrice(lo)}</strong> · Plus haut : <strong>${fmtPrice(hi)}</strong></p>`;
    document.getElementById('offers-list').insertAdjacentElement('afterend', box);
  }catch(e){}
}
"""

s = rd('index.html')
s = s.replace('</style>', CSS + '</style>', 1)
s = rep1(s, '${zoneBadgeFor(o)}\n        </div>\n      </div>\n      <div class="offer-action">', '${zoneBadgeFor(o)}\n          ${merchantExtraHtml(o)}\n        </div>\n      </div>\n      <div class="offer-action">')
s = rep1(s, "  }).join('');\n\n  document.getElementById('alert-confirm').style.display = 'none';", "  }).join('');\n  enhanceOffers(offers);\n\n  document.getElementById('alert-confirm').style.display = 'none';")
s = rep1(s, '/* ---------- Routeur (hash) ---------- */', JS + '\n/* ---------- Routeur (hash) ---------- */')
wr('index.html', s)

# ---------------- admin.html ----------------
ACARDS = """  <div class="card">
    <h3 style="margin:0 0 6px;font-family:'Manrope',sans-serif;">Avis sur les marchands <span id="reviews-count" style="color:var(--text-muted);font-weight:500;"></span></h3>
    <p class="sub" style="margin:0 0 16px;">Les avis ne s'affichent sur le site qu'après ta validation.</p>
    <div class="table-scroll"><table>
      <thead><tr><th>Marchand</th><th>Note</th><th>Commentaire</th><th>Statut</th><th>Action</th></tr></thead>
      <tbody id="reviews-tbody"></tbody>
    </table></div>
  </div>

  <div class="card">
    <h3 style="margin:0 0 6px;font-family:'Manrope',sans-serif;">Livraison par marchand</h3>
    <p class="sub" style="margin:0 0 16px;">Texte court affiché sur chaque offre (ex : Livraison 1 500 FCFA · 24-48 h). Laisse vide pour ne rien afficher.</p>
    <div class="table-scroll"><table>
      <thead><tr><th>Marchand</th><th>Infos livraison</th><th></th></tr></thead>
      <tbody id="deliv-tbody"></tbody>
    </table></div>
  </div>

"""
AJS = r"""function _aesc(t){ return String(t == null ? '' : t).replace(/[&<>\x22\x27]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','\x22':'&quot;','\x27':'&#39;'}[c])); }
async function loadReviews(){
  try{
    const rows = await rpc('admin_list_reviews', { p_admin_secret: ADMIN_SECRET });
    document.getElementById('reviews-count').textContent = '(' + rows.filter(x => x.status === 'pending').length + ' en attente)';
    const tb = document.getElementById('reviews-tbody');
    if(!rows.length){ tb.innerHTML = `<tr><td colspan='5' style='color:var(--text-muted)'>Aucun avis pour l'instant.</td></tr>`; return; }
    tb.innerHTML = rows.map(x => `<tr><td><strong>${_aesc(x.merchant_name)}</strong></td><td>${'★'.repeat(x.rating)}</td><td>${_aesc(x.comment)}<br><small>${_aesc(x.author_name || '')}</small></td><td>${x.status === 'pending' ? 'À valider' : x.status === 'approved' ? 'Publié' : 'Refusé'}</td><td>${x.status !== 'approved' ? `<button data-rv='${x.id}' data-st='approved'>Publier</button> ` : ''}${x.status !== 'rejected' ? `<button data-rv='${x.id}' data-st='rejected'>Refuser</button>` : ''}</td></tr>`).join('');
  }catch(e){}
}
document.getElementById('reviews-tbody').addEventListener('click', async e => {
  const b = e.target.closest('button[data-rv]'); if(!b) return;
  b.disabled = true;
  try{ await rpc('admin_moderate_review', { p_admin_secret: ADMIN_SECRET, p_id: b.dataset.rv, p_status: b.dataset.st }); }catch(err){}
  loadReviews();
});
async function loadDelivery(){
  try{
    const rows = await rpc('admin_list_delivery_info', { p_admin_secret: ADMIN_SECRET });
    document.getElementById('deliv-tbody').innerHTML = rows.map(x => `<tr><td><strong>${_aesc(x.name)}</strong></td><td><input data-di='${x.merchant_id}' value='${_aesc(x.delivery_info || '')}' maxlength='160' placeholder='Ex : Livraison 1 500 FCFA · 24-48 h' style='width:100%;min-width:220px'></td><td><button data-dm='${x.merchant_id}'>Enregistrer</button></td></tr>`).join('');
  }catch(e){}
}
document.getElementById('deliv-tbody').addEventListener('click', async e => {
  const b = e.target.closest('button[data-dm]'); if(!b) return;
  const inp = b.closest('tr').querySelector('input[data-di]');
  b.disabled = true;
  try{ await rpc('admin_set_delivery_info', { p_admin_secret: ADMIN_SECRET, p_merchant_id: b.dataset.dm, p_info: inp.value }); b.textContent = 'Enregistré ✓'; }catch(err){ b.textContent = 'Erreur'; }
  setTimeout(() => { b.textContent = 'Enregistrer'; b.disabled = false; }, 1500);
});

"""
a = rd('admin.html')
a = rep1(a, '  <div class="card">\n    <h3 style="margin:0 0 6px;font-family:\'Manrope\',sans-serif;">Inscrits aux alertes', ACARDS + '  <div class="card">\n    <h3 style="margin:0 0 6px;font-family:\'Manrope\',sans-serif;">Inscrits aux alertes')
a = rep1(a, 'async function loadSubscribers(){', AJS + 'async function loadSubscribers(){')
a = rep1(a, '    loadSubscribers();\n    loadClickStats();', '    loadSubscribers();\n    loadReviews();\n    loadDelivery();\n    loadClickStats();')
wr('admin.html', a)
print('ok2')
