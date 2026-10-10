import os, sys
d = sys.argv[1] if len(sys.argv) > 1 else '.'
def rd(n): return open(os.path.join(d, n), encoding='utf-8').read()
def wr(n, s): open(os.path.join(d, n), 'w', encoding='utf-8').write(s)
def rep1(s, old, new):
    assert s.count(old) == 1, (old[:70], s.count(old))
    return s.replace(old, new, 1)

CSS = r"""
.share-btn{display:inline-flex;align-items:center;gap:6px;margin:10px 0 0 8px;padding:10px 16px;border:1px solid #cfd6dd;border-radius:999px;background:#fff;color:#111;font-weight:700;font-size:14px;cursor:pointer;}
#share-modal{position:fixed;top:0;right:0;bottom:0;left:0;background:rgba(0,0,0,.5);display:none;align-items:flex-end;justify-content:center;z-index:9999;}
@media(min-width:600px){#share-modal{align-items:center;padding:16px;}}
#share-modal .sh-card{background:#fff;color:#111;border-radius:16px 16px 0 0;width:100%;max-width:440px;padding:20px;}
@media(min-width:600px){#share-modal .sh-card{border-radius:16px;}}
#share-modal h3{margin:0 0 4px;}
#share-modal .sh-text{font-size:13px;color:#555;background:#f5f5f5;border-radius:10px;padding:10px;margin:8px 0 12px;white-space:pre-wrap;word-break:break-word;}
#share-modal .sh-grid{display:grid;grid-template-columns:1fr 1fr;gap:8px;}
#share-modal .sh-grid a,#share-modal .sh-grid button{display:flex;align-items:center;justify-content:center;gap:6px;padding:12px;border-radius:10px;border:0;color:#fff;font-weight:700;font-size:14px;text-decoration:none;cursor:pointer;}
#share-modal .sh-wa{background:#25D366;}
#share-modal .sh-fb{background:#1877F2;}
#share-modal .sh-x{background:#111;}
#share-modal .sh-tg{background:#229ED9;}
#share-modal .sh-cp{background:#666;grid-column:1 / -1;}
#share-modal .sh-close{margin-top:10px;border:0;background:none;color:#666;cursor:pointer;text-decoration:underline;width:100%;}
"""

JS = r"""/* ---------- Partage réseaux sociaux ---------- */
function _shareData(){
  const m = location.pathname.match(/^\/produit\/(.+)$/);
  if(!m) return null;
  const id = decodeURIComponent(m[1]);
  const offers = allOffers.filter(o => o.product_id === id).sort((a, b) => a.price_xof - b.price_xof);
  if(!offers.length) return null;
  const c = offers[0], hi = offers[offers.length - 1];
  const url = location.origin + '/produit/' + encodeURIComponent(id);
  let text = '🔥 ' + c.product_name.trim() + ' : ' + fmtPrice(c.price_xof) + ' chez ' + c.merchant_name;
  if(offers.length > 1){
    text += ' (' + offers.length + ' marchands comparés';
    const e = hi.price_xof - c.price_xof;
    if(e > 0) text += `, jusqu'à ` + fmtPrice(e) + ` d'écart`;
    text += ')';
  }
  text += ' sur Kasaprix';
  return { title: c.product_name + ' — Kasaprix', text: text, url: url };
}
async function shareProduct(){
  const d = _shareData();
  if(!d) return;
  if(navigator.share && /Mobi|Android|iPhone|iPad/i.test(navigator.userAgent)){
    try{ await navigator.share({ title: d.title, text: d.text, url: d.url }); return; }
    catch(e){ if(e && e.name === 'AbortError') return; }
  }
  openShareModal(d);
}
function openShareModal(d){
  let modal = document.getElementById('share-modal');
  if(!modal){
    modal = document.createElement('div'); modal.id = 'share-modal'; document.body.appendChild(modal);
    modal.addEventListener('click', e => { if(e.target === modal) modal.style.display = 'none'; });
  }
  const full = d.text + ' 👉 ' + d.url;
  const u = encodeURIComponent(d.url), t = encodeURIComponent(d.text), f = encodeURIComponent(full);
  modal.innerHTML = `<div class='sh-card'><h3>Partager cette comparaison</h3><div class='sh-text'>${_esc(full)}</div>
    <div class='sh-grid'>
      <a class='sh-wa' target='_blank' rel='noopener' href='https://wa.me/?text=${f}'>WhatsApp</a>
      <a class='sh-fb' target='_blank' rel='noopener' href='https://www.facebook.com/sharer/sharer.php?u=${u}&quote=${t}'>Facebook</a>
      <a class='sh-x' target='_blank' rel='noopener' href='https://twitter.com/intent/tweet?text=${t}&url=${u}'>X</a>
      <a class='sh-tg' target='_blank' rel='noopener' href='https://t.me/share/url?url=${u}&text=${t}'>Telegram</a>
      <button type='button' class='sh-cp'>🔗 Copier le message</button>
    </div>
    <button type='button' class='sh-close'>Fermer</button></div>`;
  modal.style.display = 'flex';
  modal.querySelector('.sh-close').onclick = () => { modal.style.display = 'none'; };
  modal.querySelector('.sh-cp').onclick = async (ev) => {
    const b = ev.currentTarget;
    try{ await navigator.clipboard.writeText(full); b.textContent = 'Copié ✓'; }
    catch(e){ prompt('Copie ce message :', full); }
  };
}
"""

s = rd('index.html')
s = s.replace('</style>', CSS + '</style>', 1)
s = rep1(s, 'Être alerté si le prix baisse</button>', 'Être alerté si le prix baisse</button>\n      <button class="share-btn" type="button" onclick="shareProduct()">📤 Partager</button>')
s = rep1(s, '/* ---------- Routeur (hash) ---------- */', JS + '\n/* ---------- Routeur (hash) ---------- */')
wr('index.html', s)
print('ok4')
