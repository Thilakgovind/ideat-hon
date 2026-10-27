-- SafePath V1.1 — initial schema + Row Level Security
-- Run once in Supabase: Dashboard → SQL Editor → New query → paste this file → Run.
-- Safe to re-run (IF NOT EXISTS / DROP POLICY IF EXISTS).
--
-- Security model
--   * RLS is ON for every table.
--   * The anon (public) key may only SELECT: places, reviews, routes, stops, transfers.
--   * Everything else (users, circle, trips, logs) and ALL writes go through the
--     backend with the service key (which bypasses RLS). Never ship that key to a browser.
--   * Phone numbers exist only in users.phone and circle_contacts.phone.
--   * request_log is anonymous: area, hour, mode, lang, channel, intent. No phone, no name, no text.
--   * Sample rows carry source = 'sample'.

-- ============================================================ public reference data

create table if not exists public.stops (
  id          text primary key,                 -- stop / station code, eg 'ANW'
  name        text not null,
  name_ta     text,
  area        text not null,
  kind        text not null check (kind in ('bus_stop', 'metro_station', 'train_station')),
  lat         double precision not null,
  lng         double precision not null,
  source      text not null default 'live' check (source in ('sample', 'live')),
  created_at  timestamptz not null default now()
);

create table if not exists public.routes (
  id                   text primary key,          -- eg '21G', 'M-PURPLE'
  number               text not null,
  mode                 text not null check (mode in ('bus', 'metro', 'train', 'auto')),
  name                 text not null,
  operator             text,
  free_for_women       boolean not null default false,
  fare_inr             integer not null default 0 check (fare_inr >= 0),
  fare_others_inr      integer check (fare_others_inr >= 0),
  -- ordered stops: [{"stop_id": "ANW", "min": 0, "platform": "1", "best_exit": "..."}]
  stop_sequence        jsonb not null default '[]'::jsonb,
  first_departure      time,
  last_departure       time,
  frequency_min        integer check (frequency_min > 0),
  headway_peak_min     integer,
  headway_offpeak_min  integer,
  peak_hours           jsonb,                    -- ["07:00-10:30", ...]
  fare_rules           jsonb,                    -- metro station-pair fares / auto estimate rules
  women_coach          text,
  ladies_coaches       jsonb,
  total_coaches        integer,
  ladies_special       jsonb,
  stops_well_lit       boolean,
  walk_start_min       integer,
  walk_end_min         integer,
  color                text,
  notes                text,
  source               text not null default 'live' check (source in ('sample', 'live')),
  created_at           timestamptz not null default now()
);

create table if not exists public.transfers (
  id          text primary key,
  at_stop     text not null references public.stops (id) on delete cascade,
  from_mode   text not null check (from_mode in ('bus', 'metro', 'train', 'auto', 'walk')),
  to_mode     text not null check (to_mode in ('bus', 'metro', 'train', 'auto', 'walk')),
  walk_min    integer not null check (walk_min >= 0),
  lit         boolean not null default false,
  note        text,
  source      text not null default 'live' check (source in ('sample', 'live')),
  created_at  timestamptz not null default now()
);

create table if not exists public.places (
  id               text primary key,
  name             text not null,                -- generic / fictional names for sample data
  name_ta          text,
  type             text not null check (type in ('pharmacy', 'grocery', 'tea_shop', 'atm', 'hospital',
                                                 'police_booth', 'shg_kiosk', 'petrol_bunk', 'bus_shelter', 'bakery')),
  category         text,
  area             text not null,
  address          text,
  near_stop        text references public.stops (id) on delete set null,
  lat              double precision not null,
  lng              double precision not null,
  open_time        time,
  close_time       time,
  open_24h         boolean not null default false,
  women_run        boolean not null default false,
  well_lit         boolean not null default false,
  can_wait_inside  boolean not null default false,
  -- {"00": "empty", ..., "23": "quiet"}; values: empty | quiet | moderate | busy
  crowd_by_hour    jsonb not null default '{}'::jsonb,
  rating           numeric(2, 1) check (rating between 0 and 5),
  reviews_count    integer not null default 0,
  photo            text,
  phone            text,                          -- always NULL for sample data
  source           text not null default 'live' check (source in ('sample', 'live')),
  created_at       timestamptz not null default now(),
  constraint sample_places_have_no_phone check (source <> 'sample' or phone is null)
);

create table if not exists public.reviews (
  id          text primary key,
  place_id    text not null references public.places (id) on delete cascade,
  author      text not null,                     -- first name only, eg 'Deepa (sample)'
  rating      smallint not null check (rating between 1 and 5),
  lang        text not null default 'en' check (lang in ('en', 'ta')),
  body        text not null,
  days_ago    integer,
  source      text not null default 'live' check (source in ('sample', 'live')),
  created_at  timestamptz not null default now()
);

-- ============================================================ private data (backend only)

create table if not exists public.users (
  id            text primary key,                -- 'u_demo' or a hash of the phone, never the phone itself
  display_name  text,
  phone         text,                            -- PRIVATE
  home_area     text,
  start_area    text,
  lang          text default 'en' check (lang in ('en', 'ta')),
  source        text not null default 'live' check (source in ('sample', 'live')),
  created_at    timestamptz not null default now()
);

create table if not exists public.circle_contacts (
  id          text primary key,
  user_id     text not null references public.users (id) on delete cascade,
  label       text not null,
  label_ta    text,
  relation    text,
  phone       text,                              -- PRIVATE; sample rows use fake numbers
  accepted    boolean not null default false,    -- both sides must accept
  status      text,
  area        text,
  lat         double precision,                  -- shown only during a trip or SOS
  lng         double precision,
  source      text not null default 'live' check (source in ('sample', 'live')),
  created_at  timestamptz not null default now()
);
create index if not exists circle_contacts_user_idx on public.circle_contacts (user_id);

-- Max 5 people in a circle.
create or replace function public.enforce_circle_max() returns trigger
language plpgsql set search_path = public as $$
begin
  if (select count(*) from public.circle_contacts where user_id = new.user_id and id <> new.id) >= 5 then
    raise exception 'circle is full (max 5 contacts)';
  end if;
  return new;
end $$;
drop trigger if exists circle_max_5 on public.circle_contacts;
create trigger circle_max_5 before insert on public.circle_contacts
  for each row execute function public.enforce_circle_max();

create table if not exists public.trips (
  id               text primary key,
  user_id          text not null references public.users (id) on delete cascade,
  option_id        text,
  kind             text,
  summary          text,
  from_area        text,
  to_area          text,
  alight_stop      text,
  start_at         timestamptz not null,
  eta_at           timestamptz not null,
  status           text not null check (status in ('active', 'reached', 'alerted', 'stopped')),
  notified_circle  boolean not null default false,
  reminded         boolean not null default false,
  distance_m       integer,
  last_lat         double precision,             -- only while active; cleared on reach / stop
  last_lng         double precision,
  last_checkin_at  timestamptz,
  source           text not null default 'live' check (source in ('sample', 'live')),
  created_at       timestamptz not null default now()
);
create index if not exists trips_user_status_idx on public.trips (user_id, status);

create table if not exists public.trip_events (
  id          bigint generated always as identity primary key,
  trip_id     text not null references public.trips (id) on delete cascade,
  at          timestamptz not null default now(),
  event       text not null,                     -- start | checkin | reminder | alert | reached | sos
  detail      jsonb not null default '{}'::jsonb, -- delivery counts only, never phone numbers
  source      text not null default 'live' check (source in ('sample', 'live'))
);
create index if not exists trip_events_trip_idx on public.trip_events (trip_id);

-- Anonymous request log for the policy dashboard. No phone, no name, no message text.
create table if not exists public.request_log (
  id                bigint generated always as identity primary key,
  created_at        timestamptz not null default now(),
  area              text,                        -- rounded to area name, never coordinates
  hour              smallint check (hour between 0 and 23),
  mode              text,
  lang              text,
  channel           text check (channel in ('app', 'sms', 'voice', 'call')),
  intent            text,
  route_found       boolean,
  safe_place_found  boolean,
  source            text not null default 'live' check (source in ('sample', 'live'))
);

-- ============================================================ Row Level Security

alter table public.stops            enable row level security;
alter table public.routes           enable row level security;
alter table public.transfers        enable row level security;
alter table public.places           enable row level security;
alter table public.reviews          enable row level security;
alter table public.users            enable row level security;
alter table public.circle_contacts  enable row level security;
alter table public.trips            enable row level security;
alter table public.trip_events      enable row level security;
alter table public.request_log      enable row level security;

-- Public reference data: read-only for anon (and signed-in) clients.
drop policy if exists "public read stops"     on public.stops;
drop policy if exists "public read routes"    on public.routes;
drop policy if exists "public read transfers" on public.transfers;
drop policy if exists "public read places"    on public.places;
drop policy if exists "public read reviews"   on public.reviews;
create policy "public read stops"     on public.stops     for select to anon, authenticated using (true);
create policy "public read routes"    on public.routes    for select to anon, authenticated using (true);
create policy "public read transfers" on public.transfers for select to anon, authenticated using (true);
create policy "public read places"    on public.places    for select to anon, authenticated using (true);
create policy "public read reviews"   on public.reviews   for select to anon, authenticated using (true);

-- Belt and braces: no write grants for client roles on public tables,
-- and no access at all to private tables (no policies + no grants).
revoke insert, update, delete, truncate on public.stops, public.routes, public.transfers,
  public.places, public.reviews from anon, authenticated;
revoke all on public.users, public.circle_contacts, public.trips, public.trip_events,
  public.request_log from anon, authenticated;
revoke execute on function public.enforce_circle_max() from public, anon, authenticated;
