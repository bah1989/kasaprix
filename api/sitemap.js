const SUPABASE_URL = "https://bxljzktkxphdbalbmgcn.supabase.co";
const SUPABASE_ANON_KEY = "sb_publishable_w3bjyu8CeKjESzbLI7eCkQ_xdGTo_qw";
const SITE_URL = "https://kasaprix-elyseebah-6633.vercel.app";

export default async function handler(req, res) {
  try {
    const productsRes = await fetch(
      `${SUPABASE_URL}/rest/v1/public_price_matrix?select=product_id,last_checked_at`,
      { headers: { apikey: SUPABASE_ANON_KEY, Authorization: `Bearer ${SUPABASE_ANON_KEY}` } }
    );
    const rows = await productsRes.json();

    const seen = new Set();
    const productUrls = [];
    for (const r of Array.isArray(rows) ? rows : []) {
      if (!seen.has(r.product_id)) {
        seen.add(r.product_id);
        productUrls.push(
          `<url><loc>${SITE_URL}/produit/${r.product_id}</loc><lastmod>${new Date(r.last_checked_at).toISOString()}</lastmod></url>`
        );
      }
    }

    const categoriesRes = await fetch(
      `${SUPABASE_URL}/rest/v1/categories?select=slug`,
      { headers: { apikey: SUPABASE_ANON_KEY, Authorization: `Bearer ${SUPABASE_ANON_KEY}` } }
    );
    const categories = await categoriesRes.json();
    const categoryUrls = (Array.isArray(categories) ? categories : []).map(
      (c) => `<url><loc>${SITE_URL}/categorie/${c.slug}</loc></url>`
    );

    const xml = `<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
<url><loc>${SITE_URL}/</loc></url>
${categoryUrls.join('\n')}
${productUrls.join('\n')}
</urlset>`;

    res.setHeader('Content-Type', 'application/xml');
    res.status(200).send(xml);
  } catch (e) {
    res.status(500).send('<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"></urlset>');
  }
}
