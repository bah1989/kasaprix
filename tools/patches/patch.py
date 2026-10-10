import re, sys, os
src = sys.argv[1] if len(sys.argv) > 1 else '.'
out = sys.argv[2] if len(sys.argv) > 2 else src

def rd(n):
    return open(os.path.join(src, n), encoding='utf-8').read()
def wr(n, s):
    os.makedirs(out, exist_ok=True)
    open(os.path.join(out, n), 'w', encoding='utf-8').write(s)
def sub1(pattern, repl, s, flags=re.S):
    new, n = re.subn(pattern, lambda m: repl, s, flags=flags)
    assert n == 1, (pattern[:50], n)
    return new

# ---------------- index.html ----------------
s = rd('index.html')

CSS = """
.alert-box.alert-prominent{border:2px solid #25D366;background:#F1FBF5;box-shadow:0 6px 20px rgba(37,211,102,.15);}
.alert-prominent .phone-row{display:flex;align-items:stretch;gap:0;margin:10px 0;}
.alert-prominent .phone-prefix{display:flex;align-items:center;padding:0 12px;background:#E3F5EA;border:1px solid #cfe9d8;border-right:0;border-radius:10px 0 0 10px;font-weight:700;font-size:15px;}
.alert-prominent .phone-row input{margin:0;border-radius:0 10px 10px 0;flex:1;min-width:0;font-size:16px;}
.alert-prominent .deals-opt{display:flex;gap:8px;align-items:flex-start;font-size:13px;margin:8px 0 12px;cursor:pointer;}
.alert-prominent .deals-opt input{width:auto;margin-top:2px;}
.alert-prominent .alert-submit{background:#25D366;color:#fff;font-size:16px;padding:14px;width:100%;}
.alert-prominent .privacy-note{font-size:12px;color:#6b7280;margin:10px 0 0;}
.alert-jump{display:inline-flex;align-items:center;gap:6px;margin:10px 0 0;padding:10px 16px;border:0;border-radius:999px;background:#25D366;color:#fff;font-weight:700;font-size:14px;cursor:pointer;}
"""
assert s.count('</style>') >= 1
s = s.replace('</style>', CSS + '</style>', 1)

BOX = """<div class="alert-box alert-prominent" id="alert-box">
        <h3>🔔 Ce prix est trop haut ?</h3>
        <p>Laisse ton numéro WhatsApp : on te prévient dès que ce produit baisse de prix.</p>
        <div class="phone-row"><span class="phone-prefix">🇨🇮 +225</span><input id="alert-contact" type="tel" inputmode="tel" autocomplete="tel-national" placeholder="07 00 00 00 00"></div>
        <label class="deals-opt"><input type="checkbox" id="alert-deals" checked> <span>Recevoir aussi les bons plans de la semaine</span></label>
        <button class="alert-submit" id="alert-submit">🔔 Me prévenir sur WhatsApp</button>
        <p class="msg error" id="alert-error" style="display:none"></p>
        <p class="alert-confirm" id="alert-confirm">✓ C'est noté ! On te prévient sur WhatsApp dès que le prix baisse.</p>
        <p class="privacy-note">Ton numéro sert uniquement aux alertes de prix Kasaprix. Jamais revendu ni partagé.</p>
      </div>"""
s = sub1(r'<div class="alert-box">\s*<h3>Ce prix est trop haut \?</h3>.*?✓ Alerte créée, on te préviendra\.</p>\s*</div>', BOX, s)

JUMP = '<p class="product-meta" id="p-meta">Chargement…</p>\n      <button class="alert-jump" type="button" onclick="document.getElementById(\'alert-box\').scrollIntoView({behavior:\'smooth\',block:\'center\'})">🔔 Être alerté si le prix baisse</button>'
assert s.count('<p class="product-meta" id="p-meta">Chargement…</p>') == 1
s = s.replace('<p class="product-meta" id="p-meta">Chargement…</p>', JUMP, 1)

JS = """document.getElementById('alert-confirm').style.display = 'none';
  document.getElementById('alert-error').style.display = 'none';
  document.getElementById('alert-contact').value = '';
  document.getElementById('alert-submit').onclick = async () => {
    const btn = document.getElementById('alert-submit');
    const errEl = document.getElementById('alert-error');
    const okEl = document.getElementById('alert-confirm');
    errEl.style.display = 'none'; okEl.style.display = 'none';
    const raw = document.getElementById('alert-contact').value.replace(/[\\s.\\-()]/g, '').replace(/^(\\+225|00225|225)/, '');
    if(!/^(01|05|07|21|25|27)\\d{8}$/.test(raw)){
      errEl.textContent = 'Numéro invalide. Entre 10 chiffres, par ex. 07 00 00 00 00.';
      errEl.style.display = 'block';
      return;
    }
    btn.disabled = true;
    const label = btn.textContent; btn.textContent = 'Envoi…';
    try{
      const res = await fetch(`${SUPABASE_URL}/rest/v1/rpc/create_price_alert`, {
        method:'POST',
        headers:{
          apikey: SUPABASE_ANON_KEY,
          Authorization:`Bearer ${SUPABASE_ANON_KEY}`,
          'Content-Type':'application/json'
        },
        body: JSON.stringify({ p_product_id: productId, p_target_price: Math.floor(cheapest*0.9), p_contact: raw, p_channel: 'whatsapp', p_wants_deals: document.getElementById('alert-deals').checked })
      });
      if(!res.ok) throw new Error('http ' + res.status);
      okEl.style.display = 'block';
      document.getElementById('alert-contact').value = '';
    }catch(e){
      errEl.textContent = 'Oups, l\\'inscription a échoué. Réessaie dans un instant.';
      errEl.style.display = 'block';
    }finally{
      btn.disabled = false; btn.textContent = label;
    }
  };"""
s = sub1(r"document\.getElementById\('alert-confirm'\)\.style\.display = 'none';\s*document\.getElementById\('alert-contact'\)\.value = '';\s*document\.getElementById\('alert-submit'\)\.onclick = async \(\) => \{.*?\}catch\(e\)\{\}\s*\};", JS, s)
wr('index.html', s)

# ---------------- admin.html ----------------
a = rd('admin.html')
CARD = """  <div class="card">
    <h3 style="margin:0 0 6px;font-family:'Manrope',sans-serif;">Inscrits aux alertes <span id="subs-count" style="color:var(--text-muted);font-weight:500;"></span></h3>
    <p class="sub" style="margin:0 0 16px;">Numéros WhatsApp collectés via le bouton d'alerte. Utilise-les uniquement pour les alertes de prix et les bons plans (si la case est cochée).</p>
    <div style="margin:0 0 12px;display:flex;gap:8px;flex-wrap:wrap;"><button type="button" id="subs-copy" style="padding:8px 14px;border-radius:8px;border:1px solid #ddd;background:#fff;cursor:pointer;">Copier les numéros « bons plans »</button></div>
    <div class="table-scroll">
    <table>
      <thead><tr><th>Contact</th><th>Alertes</th><th>Produits suivis</th><th>Bons plans</th><th>Dernière inscription</th></tr></thead>
      <tbody id="subs-tbody"></tbody>
    </table>
    </div>
  </div>

"""
ANCH = '  <div class="card">\n    <h3 style="margin:0 0 6px;font-family:\'Manrope\',sans-serif;">Alertes de prix déclenchées</h3>'
assert a.count(ANCH) == 1, a.count(ANCH)
a = a.replace(ANCH, CARD + ANCH, 1)

LOADER = """async function loadSubscribers(){
  try{
    const subs = await rpc('admin_list_subscribers', { p_admin_secret: ADMIN_SECRET });
    const tbody = document.getElementById('subs-tbody');
    document.getElementById('subs-count').textContent = '(' + subs.length + ')';
    const fmt = d => d ? new Date(d).toLocaleDateString('fr-FR') : '';
    const esc = t => String(t == null ? '' : t).replace(/[&<>"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
    window.__dealsNumbers = subs.filter(x => x.wants_deals).map(x => x.contact);
    if(subs.length === 0){
      tbody.innerHTML = `<tr><td colspan="5" style="color:var(--text-muted)">Aucun inscrit pour l'instant.</td></tr>`;
      return;
    }
    tbody.innerHTML = subs.map(x => `
      <tr>
        <td><strong>${esc(x.contact)}</strong></td>
        <td>${Number(x.nb_alerts)}</td>
        <td>${esc(Array.isArray(x.products) ? x.products.join(', ') : x.products)}</td>
        <td>${x.wants_deals ? '✓ oui' : '—'}</td>
        <td>${fmt(x.last_seen)}</td>
      </tr>
    `).join('');
  }catch(e){}
}
document.getElementById('subs-copy').addEventListener('click', async () => {
  const list = (window.__dealsNumbers || []).join('\\n');
  try{ await navigator.clipboard.writeText(list); alert((window.__dealsNumbers || []).length + ' numéro(s) copié(s)'); }catch(e){ prompt('Copie les numéros :', list); }
});

"""
A2 = 'async function loadTriggeredAlerts(){'
assert a.count(A2) == 1
a = a.replace(A2, LOADER + A2, 1)
A3 = '    loadTriggeredAlerts();\n    loadClickStats();'
assert a.count(A3) == 1
a = a.replace(A3, '    loadTriggeredAlerts();\n    loadSubscribers();\n    loadClickStats();', 1)
wr('admin.html', a)
print('ok')
