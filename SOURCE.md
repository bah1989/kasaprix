# Kasaprix — source de production

Le code déployé est dans **`src/`** (Vercel : Root Directory = `src`, pas de commande de build).

- `src/index.html` : site public (SPA, routeur par chemins : /produit/:id, /categorie/:slug, /classement, ...)
- `src/admin.html`, `src/merchant.html` : back-office et espace marchand
- `src/middleware.js` : aperçus de liens (Open Graph) pour WhatsApp, Facebook, etc.
- `src/api/og.js` : génère l'image 1200x630 des aperçus (sharp) — servie en /og/<id>.jpg
- `src/api/sitemap.js` : sitemap dynamique
- `src/vercel.json` : réécritures d'URL
- Base de données : Supabase projet `comparateur-prix-ci` (id bxljzktkxphdbalbmgcn)

`tools/patches/` : historique des correctifs appliqués (référence, ne pas exécuter).
Ancien contenu (schema.sql, workflow.json, admin.html à la racine) : brouillons d'origine, conservés.
