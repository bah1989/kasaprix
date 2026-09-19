-- ============================================================
-- KASAPRIX — SCHÉMA COMPLET SUPABASE (PostgreSQL)
-- Projet Supabase : comparateur-prix-ci
--
-- ⚠️ Remplacer PLACEHOLDER_ADMIN_SECRET par un vrai secret fort
-- avant d'exécuter ce script, dans les 3 fonctions admin_* en bas.
-- Ne jamais commiter le vrai secret dans ce dépôt.
-- ============================================================

create extension if not exists "pgcrypto";

-- ------------------------------------------------------------
-- TABLES
-- ------------------------------------------------------------
create table merchants (
    id uuid primary key default gen_random_uuid(),
    name text not null,
    logo_url text,
    contact_phone text,
    contact_whatsapp text,
    website_url text,
    partnership_type text not null default 'direct'
        check (partnership_type in ('affiliate', 'direct')),
    base_affiliate_tag text,
    feed_url text,
    feed_format text check (feed_format in ('json', 'xml', 'csv')),
    is_active boolean not null default true,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    constraint chk_affiliate_tag check (
        (partnership_type = 'affiliate' and base_affiliate_tag is not null)
        or (partnership_type = 'direct')
    )
);

create table categories (
    id uuid primary key default gen_random_uuid(),
    name text not null,
    slug text not null unique,
    parent_id uuid references categories(id) on delete set null,
    created_at timestamptz not null default now()
);

create table products (
    id uuid primary key default gen_random_uuid(),
    name text not null,
    brand text,
    ean_sku text unique,
    category_id uuid references categories(id) on delete set null,
    image_url text,
    description text,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create table offers (
    id uuid primary key default gen_random_uuid(),
    product_id uuid not null references products(id) on delete cascade,
    merchant_id uuid not null references merchants(id) on delete cascade,
    price_xof numeric(12,2) not null check (price_xof >= 0),
    in_stock boolean not null default true,
    raw_url text not null,
    final_url text,
    last_checked_at timestamptz not null default now(),
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    unique (product_id, merchant_id)
);

create index idx_offers_product on offers(product_id);
create index idx_offers_merchant on offers(merchant_id);
create index idx_offers_price on offers(price_xof);

create table price_history (
    id uuid primary key default gen_random_uuid(),
    offer_id uuid not null references offers(id) on delete cascade,
    old_price_xof numeric(12,2),
    new_price_xof numeric(12,2) not null,
    changed_at timestamptz not null default now()
);

create index idx_price_history_offer on price_history(offer_id);

create table user_alerts (
    id uuid primary key default gen_random_uuid(),
    user_id uuid,
    product_id uuid not null references products(id) on delete cascade,
    target_price_xof numeric(12,2) not null,
    channel text not null default 'email' check (channel in ('email', 'sms', 'whatsapp')),
    contact text not null,
    is_active boolean not null default true,
    created_at timestamptz not null default now(),
    triggered_at timestamptz
);

create index idx_user_alerts_product on user_alerts(product_id);

-- ------------------------------------------------------------
-- TRIGGERS
-- ------------------------------------------------------------
create or replace function fn_log_price_change()
returns trigger as $$
begin
    if new.price_xof is distinct from old.price_xof then
        insert into price_history (offer_id, old_price_xof, new_price_xof)
        values (old.id, old.price_xof, new.price_xof);
    end if;
    new.updated_at = now();
    return new;
end;
$$ language plpgsql;

create trigger trg_offers_price_history
after update on offers
for each row
execute function fn_log_price_change();

create or replace function fn_touch_updated_at()
returns trigger as $$
begin
    new.updated_at = now();
    return new;
end;
$$ language plpgsql;

create trigger trg_merchants_touch
before update on merchants
for each row
execute function fn_touch_updated_at();

create trigger trg_products_touch
before update on products
for each row
execute function fn_touch_updated_at();

-- ------------------------------------------------------------
-- RLS
-- ------------------------------------------------------------
alter table merchants enable row level security;
alter table categories enable row level security;
alter table products enable row level security;
alter table offers enable row level security;
alter table price_history enable row level security;
alter table user_alerts enable row level security;

create policy "categories_public_read" on categories for select using (true);
create policy "products_public_read" on products for select using (true);
create policy "price_history_public_read" on price_history for select using (true);
-- merchants, offers, user_alerts : aucune policy select => anon bloqué par défaut.

-- ------------------------------------------------------------
-- VUE PUBLIQUE (utilisée par index.html)
-- security_invoker = false : la vue s'exécute avec ses propres
-- privilèges, pas ceux de l'appelant anonyme — sinon RLS bloque tout.
-- ------------------------------------------------------------
create view public_price_matrix
with (security_invoker = false)
as
select
    o.id as offer_id,
    p.id as product_id,
    p.name as product_name,
    p.brand,
    p.image_url,
    p.category_id,
    m.id as merchant_id,
    m.name as merchant_name,
    m.logo_url as merchant_logo_url,
    m.partnership_type,
    case when m.partnership_type = 'direct' then m.contact_whatsapp else null end as merchant_whatsapp,
    o.price_xof,
    o.in_stock,
    o.final_url,
    o.last_checked_at
from offers o
join products p on p.id = o.product_id
join merchants m on m.id = o.merchant_id
where m.is_active = true
order by o.price_xof asc;

grant select on public_price_matrix to anon;
grant select on categories to anon;
grant select on products to anon;
grant select on price_history to anon;

-- ------------------------------------------------------------
-- FONCTIONS PUBLIQUES (appelées par index.html avec la clé anon)
-- ------------------------------------------------------------
create or replace function upsert_offer_by_sku(
    p_sku text, p_name text, p_brand text, p_merchant_id uuid,
    p_price_xof numeric, p_in_stock boolean, p_raw_url text, p_final_url text
) returns uuid as $$
declare
    v_product_id uuid;
begin
    insert into products (ean_sku, name, brand)
    values (p_sku, p_name, p_brand)
    on conflict (ean_sku) do update set name = excluded.name, brand = excluded.brand
    returning id into v_product_id;

    insert into offers (product_id, merchant_id, price_xof, in_stock, raw_url, final_url, last_checked_at)
    values (v_product_id, p_merchant_id, p_price_xof, p_in_stock, p_raw_url, p_final_url, now())
    on conflict (product_id, merchant_id) do update
        set price_xof = excluded.price_xof, in_stock = excluded.in_stock,
            raw_url = excluded.raw_url, final_url = excluded.final_url, last_checked_at = now();

    return v_product_id;
end;
$$ language plpgsql security definer set search_path = public;

grant execute on function upsert_offer_by_sku(text, text, text, uuid, numeric, boolean, text, text) to service_role;

create or replace function create_price_alert(
    p_product_id uuid, p_target_price numeric, p_contact text, p_channel text default 'email'
) returns uuid as $$
declare
    v_id uuid;
begin
    if p_channel not in ('email','sms','whatsapp') then
        p_channel := 'email';
    end if;
    insert into user_alerts (product_id, target_price_xof, channel, contact)
    values (p_product_id, p_target_price, p_channel, p_contact)
    returning id into v_id;
    return v_id;
end;
$$ language plpgsql security definer set search_path = public;

grant execute on function create_price_alert(uuid, numeric, text, text) to anon;

-- ------------------------------------------------------------
-- FONCTIONS ADMIN (appelées par admin.html — mot de passe requis)
-- ⚠️ Remplacer PLACEHOLDER_ADMIN_SECRET par un vrai secret avant exécution.
-- ------------------------------------------------------------
create or replace function admin_list_merchants(p_admin_secret text)
returns setof merchants as $$
begin
    if p_admin_secret is distinct from 'PLACEHOLDER_ADMIN_SECRET' then
        raise exception 'unauthorized';
    end if;
    return query select * from merchants order by created_at desc;
end;
$$ language plpgsql security definer set search_path = public;

create or replace function admin_upsert_merchant(
    p_admin_secret text, p_id uuid default null, p_name text default null,
    p_partnership_type text default 'direct', p_base_affiliate_tag text default null,
    p_feed_url text default null, p_feed_format text default null,
    p_contact_whatsapp text default null, p_contact_phone text default null,
    p_website_url text default null, p_is_active boolean default true
) returns merchants as $$
declare
    v_row merchants;
begin
    if p_admin_secret is distinct from 'PLACEHOLDER_ADMIN_SECRET' then
        raise exception 'unauthorized';
    end if;

    if p_id is null then
        insert into merchants (name, partnership_type, base_affiliate_tag, feed_url, feed_format, contact_whatsapp, contact_phone, website_url, is_active)
        values (p_name, p_partnership_type, p_base_affiliate_tag, p_feed_url, p_feed_format, p_contact_whatsapp, p_contact_phone, p_website_url, p_is_active)
        returning * into v_row;
    else
        update merchants set
            name = coalesce(p_name, name), partnership_type = coalesce(p_partnership_type, partnership_type),
            base_affiliate_tag = p_base_affiliate_tag, feed_url = p_feed_url, feed_format = p_feed_format,
            contact_whatsapp = p_contact_whatsapp, contact_phone = p_contact_phone,
            website_url = p_website_url, is_active = coalesce(p_is_active, is_active)
        where id = p_id
        returning * into v_row;
    end if;
    return v_row;
end;
$$ language plpgsql security definer set search_path = public;

create or replace function admin_upsert_offer_manual(
    p_admin_secret text, p_merchant_id uuid, p_product_name text, p_brand text default null,
    p_price_xof numeric default null, p_in_stock boolean default true,
    p_link text default null, p_image_url text default null
) returns offers as $$
declare
    v_product_id uuid;
    v_offer offers;
    v_clean_link text;
    v_match text[];
begin
    if p_admin_secret is distinct from 'PLACEHOLDER_ADMIN_SECRET' then
        raise exception 'unauthorized';
    end if;

    v_match := regexp_match(p_link, 'https?://[^\s]+');
    v_clean_link := coalesce(v_match[1], p_link);

    select id into v_product_id from products where lower(name) = lower(p_product_name) limit 1;

    if v_product_id is null then
        insert into products (name, brand, ean_sku, image_url)
        values (p_product_name, p_brand, 'manual-' || gen_random_uuid()::text, p_image_url)
        returning id into v_product_id;
    elsif p_image_url is not null then
        update products set image_url = p_image_url where id = v_product_id;
    end if;

    insert into offers (product_id, merchant_id, price_xof, in_stock, raw_url, final_url, last_checked_at)
    values (v_product_id, p_merchant_id, p_price_xof, p_in_stock, v_clean_link, v_clean_link, now())
    on conflict (product_id, merchant_id) do update
        set price_xof = excluded.price_xof, in_stock = excluded.in_stock,
            raw_url = excluded.raw_url, final_url = excluded.final_url, last_checked_at = now()
    returning * into v_offer;

    return v_offer;
end;
$$ language plpgsql security definer set search_path = public;

create or replace function admin_list_offers(p_admin_secret text)
returns table(offer_id uuid, product_name text, merchant_name text, price_xof numeric, final_url text, last_checked_at timestamptz) as $$
begin
    if p_admin_secret is distinct from 'PLACEHOLDER_ADMIN_SECRET' then
        raise exception 'unauthorized';
    end if;
    return query
    select o.id, p.name, m.name, o.price_xof, o.final_url, o.last_checked_at
    from offers o
    join products p on p.id = o.product_id
    join merchants m on m.id = o.merchant_id
    order by o.last_checked_at desc;
end;
$$ language plpgsql security definer set search_path = public;

grant execute on function admin_list_merchants(text) to anon;
grant execute on function admin_upsert_merchant(text, uuid, text, text, text, text, text, text, text, text, boolean) to anon;
grant execute on function admin_upsert_offer_manual(text, uuid, text, text, numeric, boolean, text, text) to anon;
grant execute on function admin_list_offers(text) to anon;
