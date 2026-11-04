-- Approved sponsor/merchant offer records. No sample row is claimable.
begin;
create table if not exists public.vm_partner_offers (
  id text primary key,
  partner_name text not null,
  offer_type text not null check (offer_type in ('equipment','entry_fee','travel','training')),
  sport_id text references public.vm_sports(id),
  district_id text references public.vm_districts(id),
  eligibility text not null,
  value_inr numeric(10,2) check (value_inr is null or value_inr >= 0),
  application_url text,
  verified boolean not null default false,
  status text not null default 'sample' check (status in ('sample','open','closed')),
  source text not null default 'sample',
  check (source <> 'sample' or (verified = false and status = 'sample' and application_url is null))
);
alter table public.vm_partner_offers enable row level security;
revoke all on public.vm_partner_offers from anon, authenticated;
grant select on public.vm_partner_offers to anon, authenticated;
grant insert, update, delete on public.vm_partner_offers to service_role;
drop policy if exists public_read on public.vm_partner_offers;
create policy public_read on public.vm_partner_offers for select to anon, authenticated using (status = 'open' and verified = true);
commit;
