-- SafePath V1.1 — explicit Data API grants (run after 001_init.sql; safe to re-run)
-- Newer Supabase projects do not expose new tables to the API automatically, so the
-- API cannot see them (error PGRST205) until the API roles have explicit grants.
-- RLS from 001 still applies: anon can only SELECT the 5 public tables.

grant usage on schema public to anon, authenticated, service_role;

-- Public reference data: read-only for the browser.
grant select on public.stops, public.routes, public.transfers, public.places, public.reviews
  to anon, authenticated;

-- Backend (service key) only: full access to every SafePath table and sequence.
grant select, insert, update, delete on
  public.stops, public.routes, public.transfers, public.places, public.reviews,
  public.users, public.circle_contacts, public.trips, public.trip_events, public.request_log
  to service_role;
grant usage, select on all sequences in schema public to service_role;

-- Private tables stay closed to browser roles (no grants, no policies).
revoke all on public.users, public.circle_contacts, public.trips, public.trip_events,
  public.request_log from anon, authenticated;

-- Make the API pick up the tables now.
notify pgrst, 'reload schema';
