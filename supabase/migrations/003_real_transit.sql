-- SafePath V1.1 — real transit data (ChennaiGTFS) next to the sample rows. Safe to re-run.
-- Real rows use source = 'live' and say where they came from in data_source.
--   routes.departures  exact departures from the first stop, ["07:10", "07:20", ...] (real timetable)
--   routes.one_way     true: this row is one direction only (GTFS); false: sample row, app runs it both ways
--   routes.free_note   the scheme rule shown in the app ("free on ordinary (white-board) buses")
--   stop_sequence items may carry "area": the app area a stop stands for on that route

alter table public.routes add column if not exists departures  jsonb;
alter table public.routes add column if not exists one_way     boolean not null default false;
alter table public.routes add column if not exists free_note   text;
alter table public.routes add column if not exists data_source text;
alter table public.routes add column if not exists source_url  text;

alter table public.stops  add column if not exists data_source text;

-- Grants from 002 cover new columns (table-level). Make the API see them now.
notify pgrst, 'reload schema';
