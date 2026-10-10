const sharp = require('sharp');
const SB = 'https://bxljzktkxphdbalbmgcn.supabase.co';
const KEY = 'sb_publishable_w3bjyu8CeKjESzbLI7eCkQ_xdGTo_qw';
const W = 1200, H = 630;
const G = {
  K: ['X...X', 'X..X.', 'X.X..', 'XX...', 'X.X..', 'X..X.', 'X...X'],
  a: ['.....', '.....', '.XXX.', '....X', '.XXXX', 'X...X', '.XXXX'],
  s: ['.....', '.....', '.XXXX', 'X....', '.XXX.', '....X', 'XXXX.'],
  p: ['.....', '.....', 'XXXX.', 'X...X', 'XXXX.', 'X....', 'X....'],
  r: ['.....', '.....', 'X.XX.', 'XX..X', 'X....', 'X....', 'X....'],
  i: ['..X..', '.....', '.XX..', '..X..', '..X..', '..X..', '.XXX.'],
  x: ['.....', '.....', 'X...X', '.X.X.', '..X..', '.X.X.', 'X...X']
};
function defaultSvg() {
  const px = 20, gap = 20, word = 'Kasaprix';
  const total = word.length * 5 * px + (word.length - 1) * gap;
  const x0 = Math.round((W - total) / 2), y0 = Math.round((H - 7 * px) / 2) - 20;
  let rects = '';
  [...word].forEach((ch, i) => {
    const color = i >= 4 ? '#1F1F1F' : '#FFFFFF';
    const ox = x0 + i * (5 * px + gap);
    G[ch].forEach((row, r) => [...row].forEach((c, k) => {
      if (c === 'X') rects += `<rect x='${ox + k * px}' y='${y0 + r * px}' width='${px}' height='${px}' fill='${color}'/>`;
    }));
  });
  rects += `<rect x='${x0}' y='${y0 + 7 * px + 40}' width='${total}' height='10' rx='5' fill='#FFFFFF' opacity='0.5'/>`;
  return `<svg xmlns='http://www.w3.org/2000/svg' width='${W}' height='${H}'><rect width='${W}' height='${H}' fill='#FF6B1A'/>${rects}</svg>`;
}
async function fetchT(url, opts, ms) {
  const c = new AbortController();
  const t = setTimeout(() => c.abort(), ms);
  try { return await fetch(url, { ...opts, signal: c.signal }); } finally { clearTimeout(t); }
}
async function productImage(id) {
  const r = await fetchT(`${SB}/rest/v1/public_price_matrix?product_id=eq.${id}&select=image_url&limit=1`, { headers: { apikey: KEY, Authorization: 'Bearer ' + KEY } }, 6000);
  const rows = await r.json();
  const u = rows && rows[0] && rows[0].image_url;
  if (!u || !/^https?:\/\//.test(u)) return null;
  const ir = await fetchT(u, { headers: { 'User-Agent': 'Mozilla/5.0 (compatible; KasaprixOG/1.0)', Accept: 'image/*', Referer: new URL(u).origin + '/' }, redirect: 'follow' }, 8000);
  if (!ir.ok) return null;
  const buf = Buffer.from(await ir.arrayBuffer());
  return buf.length > 12e6 ? null : buf;
}
module.exports = async (req, res) => {
  let out = null;
  try {
    const id = String((req.query && req.query.id) || '');
    if (/^[0-9a-f-]{36}$/i.test(id)) {
      const buf = await productImage(id);
      if (buf) out = await sharp(buf, { failOn: 'none' }).rotate().resize(W, H, { fit: 'contain', background: '#ffffff' }).flatten({ background: '#ffffff' }).jpeg({ quality: 80 }).toBuffer();
    }
  } catch (e) { out = null; }
  if (!out) out = await sharp(Buffer.from(defaultSvg())).jpeg({ quality: 85 }).toBuffer();
  res.setHeader('Content-Type', 'image/jpeg');
  res.setHeader('Cache-Control', 'public, max-age=86400, s-maxage=86400, stale-while-revalidate=604800');
  res.setHeader('Content-Length', String(out.length));
  res.status(200).send(out);
};
