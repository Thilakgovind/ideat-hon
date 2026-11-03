-- Additive sports module. Never drops or clears SafePath tables.
begin;
create table if not exists public.vm_districts (
  id text primary key, name text not null unique, name_ta text not null,
  source text not null default 'sample' check (source in ('sample','verified'))
);
create table if not exists public.vm_sports (
  id text primary key, name text not null unique, name_ta text not null,
  source text not null default 'sample' check (source in ('sample','verified'))
);
create table if not exists public.vm_organizations (
  id text primary key, name text not null, district_id text not null references public.vm_districts(id),
  verified boolean not null default false, source text not null default 'sample',
  check (source <> 'sample' or verified = false)
);
create table if not exists public.vm_opportunities (
  id text primary key, name text not null, sport_id text not null references public.vm_sports(id),
  district_id text not null references public.vm_districts(id),
  organization_id text not null references public.vm_organizations(id),
  kind text not null check (kind in ('trial','camp','tournament')),
  eligibility text not null, needs text not null, fee_inr numeric(10,2) not null default 0 check (fee_inr >= 0),
  starts_on date, deadline date, application_url text,
  status text not null default 'sample' check (status in ('sample','open','closed')),
  source text not null default 'sample',
  check (source <> 'sample' or (status = 'sample' and application_url is null))
);
create table if not exists public.vm_resources (
  id text primary key, district_id text not null references public.vm_districts(id),
  name text not null, category text not null check (category in ('equipment','entry_fee','travel','private_support')),
  description text not null, eligibility text not null, source text not null default 'sample'
);
-- Genuine auth users only. No invented accounts, phones or menstrual histories.
create table if not exists public.vm_athlete_profiles (
  user_id uuid primary key references auth.users(id) on delete cascade,
  display_name text not null, district_id text references public.vm_districts(id),
  sport_id text references public.vm_sports(id), language text not null default 'ta' check (language in ('ta','en'))
);
create table if not exists public.vm_support_requests (
  id uuid primary key default gen_random_uuid(), user_id uuid not null references auth.users(id) on delete cascade,
  category text not null check (category in ('equipment','entry_fee','travel','lighter_session','rest','private_conversation')),
  opportunity_id text references public.vm_opportunities(id),
  status text not null default 'submitted' check (status in ('submitted','reviewing','approved','declined','cancelled')),
  created_at timestamptz not null default now()
);
create table if not exists public.vm_request_events (
  id uuid primary key default gen_random_uuid(), request_id uuid not null references public.vm_support_requests(id) on delete cascade,
  status text not null check (status in ('submitted','reviewing','approved','declined','cancelled')),
  created_at timestamptz not null default now()
);
create index if not exists vm_opportunities_filter on public.vm_opportunities(district_id, sport_id);
create index if not exists vm_organizations_district on public.vm_organizations(district_id);
create index if not exists vm_opportunities_org on public.vm_opportunities(organization_id);
create index if not exists vm_opportunities_sport on public.vm_opportunities(sport_id);
create index if not exists vm_resources_district on public.vm_resources(district_id);
create index if not exists vm_requests_owner on public.vm_support_requests(user_id);
create index if not exists vm_requests_opportunity on public.vm_support_requests(opportunity_id);
create index if not exists vm_events_request on public.vm_request_events(request_id);

do $$
declare t text;
begin
  foreach t in array array['vm_districts','vm_sports','vm_organizations','vm_opportunities','vm_resources',
                          'vm_athlete_profiles','vm_support_requests','vm_request_events'] loop
    execute format('alter table public.%I enable row level security',t);
    execute format('revoke all on public.%I from anon, authenticated',t);
    execute format('grant select, insert, update, delete on public.%I to service_role',t);
  end loop;
  foreach t in array array['vm_districts','vm_sports','vm_organizations','vm_opportunities','vm_resources'] loop
    execute format('grant select on public.%I to anon, authenticated',t);
    execute format('drop policy if exists public_read on public.%I',t);
    execute format('create policy public_read on public.%I for select to anon, authenticated using (true)',t);
  end loop;
end $$;
grant select on public.vm_athlete_profiles, public.vm_support_requests, public.vm_request_events to authenticated;
drop policy if exists own_profile on public.vm_athlete_profiles;
create policy own_profile on public.vm_athlete_profiles for select to authenticated using ((select auth.uid()) = user_id);
drop policy if exists own_requests on public.vm_support_requests;
create policy own_requests on public.vm_support_requests for select to authenticated using ((select auth.uid()) = user_id);
drop policy if exists own_events on public.vm_request_events;
create policy own_events on public.vm_request_events for select to authenticated using (
  exists (select 1 from public.vm_support_requests r where r.id = request_id and r.user_id = (select auth.uid()))
);
-- All writes go through a backend that verifies identity and allowed transitions.
notify pgrst, 'reload schema';
commit;
