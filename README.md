# Kasaprix

Comparateur de prix multi-marchands en Côte d'Ivoire — modèle hybride (grands e-commerçants affiliés + marchands locaux de proximité).

## Stack

- **Base de données** : Supabase (PostgreSQL) — projet `comparateur-prix-ci`
- **Automatisation** : n8n — ingestion des flux catalogues marchands, logique conditionnelle d'affiliation
- **Front-end** : HTML/JS statique, sans framework — déployé sur Vercel
- **Hébergement** : Vercel

## Structure du dépôt

```
/index.html          Site public Kasaprix (accueil + matrice de prix + alertes)
/admin.html           Panneau d'administration des marchands et offres
/supabase/schema.sql  Schéma complet de la base (tables, vues, fonctions, RLS)
/n8n/workflow.json    Scénario d'ingestion automatisée des catalogues marchands
```

## Déploiement

Le site est déployé sur Vercel : `kasaprix-elyseebah-6633.vercel.app`

Pour redéployer après modification : pousser les fichiers `index.html` / `admin.html` mis à jour, puis redéployer sur Vercel (ou connecter ce dépôt à un projet Vercel pour un déploiement automatique à chaque push).

## Sécurité

- Le site public utilise uniquement la clé Supabase **anon** (publique par design), jamais la clé `service_role`.
- L'accès en écriture aux marchands/offres passe par des fonctions Postgres `SECURITY DEFINER` protégées par un mot de passe, vérifié côté serveur uniquement — **ce mot de passe n'est jamais commité dans ce dépôt**. Il est géré séparément.
- `n8n/workflow.json` utilise des variables d'environnement n8n (`$vars.SUPABASE_URL`, `$vars.SUPABASE_SERVICE_ROLE_KEY`) — aucune clé secrète n'est présente dans ce fichier.
