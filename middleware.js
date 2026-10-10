export const config = {
  matcher: ['/produit/:path*', '/categorie/:path*'],
};

const BOT_REGEX = /(whatsapp|facebookexternalhit|twitterbot|telegrambot|googlebot|bingbot|linkedinbot|slackbot|discordbot|applebot|skypeuripreview|vkshare|pinterest|redditbot)/i;

const SUPABASE_URL = "https://bxljzktkxphdbalbmgcn.supabase.co";
const SUPABASE_ANON_KEY = "sb_publishable_w3bjyu8CeKjESzbLI7eCkQ_xdGTo_qw";

function escapeHtml(str) {
  return String(str || '').replace(/[&<>"']/g, (c) => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
  }[c]));
}

function fmtPrice(n) {
  return Number(n).toLocaleString('fr-FR', { maximumFractionDigits: 0 }) + ' FCFA';
}

function __ogImage(image, url) {
  try {
    const u = new URL(url);
    const m = u.pathname.match(/^\/produit\/([^/]+)/);
    if (m) return u.origin + '/og/' + encodeURIComponent(decodeURIComponent(m[1])) + '.jpg';
    return u.origin + '/og/default.jpg';
  } catch (e) { return image; }
}
function renderMetaPage({ title, description, image, url }) {
  image = __ogImage(image, url);
  return `<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<title>${escapeHtml(title)}</title>
<meta name="description" content="${escapeHtml(description)}">
<meta property="og:type" content="product">
<meta property="og:site_name" content="Kasaprix">
<meta property="og:title" content="${escapeHtml(title)}">
<meta property="og:description" content="${escapeHtml(description)}">
<meta property="og:image" content="${escapeHtml(image)}">
<meta property="og:image:secure_url" content="${escapeHtml(image)}">
<meta property="og:image:type" content="image/jpeg">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:url" content="${escapeHtml(url)}">
<meta name="twitter:card" content="summary_large_image">
<link rel="canonical" href="${escapeHtml(url)}">
</head>
<body>
<h1>${escapeHtml(title)}</h1>
<p>${escapeHtml(description)}</p>
<img src="${escapeHtml(image)}" alt="${escapeHtml(title)}" style="max-width:400px">
</body>
</html>`;
}

export default async function middleware(request) {
  const ua = request.headers.get('user-agent') || '';
  if (!BOT_REGEX.test(ua)) {
    return;
  }

  const url = new URL(request.url);
  const parts = url.pathname.split('/').filter(Boolean);
  const defaultImage = 'https://kasaprix-elyseebah-6633.vercel.app/og-default.png';

  try {
    if (parts[0] === 'produit' && parts[1]) {
      const res = await fetch(
        `${SUPABASE_URL}/rest/v1/public_price_matrix?product_id=eq.${encodeURIComponent(parts[1])}&select=*&order=price_xof.asc&limit=1`,
        { headers: { apikey: SUPABASE_ANON_KEY, Authorization: `Bearer ${SUPABASE_ANON_KEY}` } }
      );
      const data = await res.json();
      if (Array.isArray(data) && data[0]) {
        const p = data[0];
        const html = renderMetaPage({
          title: `${p.product_name} — ${fmtPrice(p.price_xof)} | Kasaprix`,
          description: `Le prix le plus bas pour ${p.product_name} : ${fmtPrice(p.price_xof)} chez ${p.merchant_name}. Comparez sur Kasaprix.`,
          image: p.image_url || defaultImage,
          url: url.toString(),
        });
        return new Response(html, { headers: { 'content-type': 'text/html; charset=utf-8' } });
      }
    } else if (parts[0] === 'categorie' && parts[1]) {
      const name = decodeURIComponent(parts[1]);
      const html = renderMetaPage({
        title: `${name} — Kasaprix`,
        description: `Comparez les prix en ${name} sur Kasaprix.`,
        image: defaultImage,
        url: url.toString(),
      });
      return new Response(html, { headers: { 'content-type': 'text/html; charset=utf-8' } });
    }
  } catch (e) {
    // en cas d'erreur, on laisse passer vers le site normal plutôt que de casser le partage
  }
}
