-- NeuroArchive — Supabase schema
-- Run this in the Supabase SQL editor.
--
-- Everything lives in its own schema (`neuroarchive`) instead of `public`, so it
-- can sit alongside other apps in the same Supabase project without colliding.
--
-- ⚠️ One-time setup in Supabase Studio:
--   Settings → API → "Exposed schemas" — add `neuroarchive` (comma-separated)
--   so PostgREST / the JS client / Realtime can see the table.

create extension if not exists "pgcrypto";

-- ─── schema ────────────────────────────────────────────────────────────────
create schema if not exists neuroarchive;

-- Grant usage so the auto-generated Supabase roles can reach into the schema.
grant usage on schema neuroarchive to anon, authenticated, service_role;
alter default privileges in schema neuroarchive
    grant all on tables    to service_role;
alter default privileges in schema neuroarchive
    grant all on sequences to service_role;
alter default privileges in schema neuroarchive
    grant all on functions to service_role;

-- ─── downloads ─────────────────────────────────────────────────────────────
create table if not exists neuroarchive.downloads (
    id           uuid primary key default gen_random_uuid(),
    user_id      uuid not null references auth.users(id) on delete cascade,
    source_url   text not null,
    title        text,
    thumbnail    text,
    duration     integer,                -- seconds
    media_type   text not null check (media_type in ('audio','video')),
    quality      text not null check (quality in ('best','1080p','720p','audio')),
    status       text not null default 'queued'
                 check (status in ('queued','downloading','processing','uploading','completed','failed','deleted')),
    progress     numeric(5,2) not null default 0,
    error        text,
    r2_key       text,                   -- object key in R2 bucket
    public_url   text,                   -- optional permanent URL if R2 is public-mapped
    bytes        bigint,
    transcript   text,                   -- reserved for future Whisper integration
    created_at   timestamptz not null default now(),
    updated_at   timestamptz not null default now()
);

create index if not exists downloads_user_id_idx on neuroarchive.downloads(user_id);
create index if not exists downloads_status_idx  on neuroarchive.downloads(status);
create index if not exists downloads_created_idx on neuroarchive.downloads(created_at desc);

-- keep updated_at fresh
create or replace function neuroarchive.tg_set_updated_at()
returns trigger language plpgsql as $$
begin
  new.updated_at := now();
  return new;
end $$;

drop trigger if exists set_updated_at on neuroarchive.downloads;
create trigger set_updated_at
  before update on neuroarchive.downloads
  for each row execute function neuroarchive.tg_set_updated_at();

-- Per-table grants (default privileges only cover *future* objects).
grant select, insert, update, delete on neuroarchive.downloads to authenticated;
grant all on neuroarchive.downloads to service_role;

-- ─── Row-Level Security ────────────────────────────────────────────────────
alter table neuroarchive.downloads enable row level security;

drop policy if exists "owners read"   on neuroarchive.downloads;
drop policy if exists "owners insert" on neuroarchive.downloads;
drop policy if exists "owners update" on neuroarchive.downloads;
drop policy if exists "owners delete" on neuroarchive.downloads;

create policy "owners read"   on neuroarchive.downloads for select using  (auth.uid() = user_id);
create policy "owners insert" on neuroarchive.downloads for insert with check (auth.uid() = user_id);
create policy "owners update" on neuroarchive.downloads for update using  (auth.uid() = user_id);
create policy "owners delete" on neuroarchive.downloads for delete using  (auth.uid() = user_id);

-- Realtime
alter publication supabase_realtime add table neuroarchive.downloads;
