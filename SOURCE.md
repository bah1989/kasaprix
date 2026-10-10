# Kasaprix — source de production

Le code déployé est dans **la racine du dépôt** (Vercel : aucun dossier racine spécifique, pas de commande de build).

- `index.html` : site public (SPA, routeur par chemins : /produit/:id, /categorie/:slug, /classement, ...)
- `admin.html`, `merchant.html` : back-office et espace marchand
- `middleware.js` : aperçus de liens (Open Graph) pour WhatsApp, Facebook, etc.
- `api/og.js` : génère l'image 1200x630 des aperçus (sharp) — servie en /og/<id>.jpg
- `api/sitemap.js` : sitemap dynamique
- `vercel.json` : réécritures d'URL
- Base de données : Supabase projet `comparateur-prix-ci` (id bxljzktkxphdbalbmgcn)

`tools/patches/` : historique des correctifs appliqués (référence, ne pas exécuter).
Ancien contenu (archive-ancien/ : schema.sql, workflow.json, ancien admin.html) : brouillons d'origine, conservés.
