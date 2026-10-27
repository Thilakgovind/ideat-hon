# SafePath — Supabase

## Run the migration (once)

1. Open https://supabase.com/dashboard and pick the SafePath project (the one in `SUPABASE_URL`).
2. Left sidebar → **SQL Editor** → **New query**.
3. Open `supabase/migrations/001_init.sql`, copy everything, paste it into the editor.
4. Click **Run** (or Ctrl+Enter). Expect "Success. No rows returned".
   It is safe to run again; it only creates what is missing and resets the policies.
5. Do the same with `supabase/migrations/002_api_grants.sql` (explicit Data API grants).
   Newer projects do not expose new tables to the API on their own; without this file the
   API answers `PGRST205 Could not find the table ... in the schema cache`.
6. Check: left sidebar → **Table Editor** shows 10 tables, each with an "RLS enabled" badge:
   `stops, routes, transfers, places, reviews, users, circle_contacts, trips, trip_events, request_log`.
7. From the repo root, verify keys + RLS (prints names and OK/FAILED only):

   ```bash
   .venv/Scripts/python -m backend.supabase_verify
   ```

## Security model

| Table | anon key (browser) | service key (backend only) |
|---|---|---|
| places, reviews, routes, stops, transfers | SELECT only | read / write |
| users, circle_contacts, trips, trip_events, request_log | no access | read / write |

- RLS is on for every table. Writes never come from the browser.
- `SUPABASE_SERVICE_KEY` bypasses RLS: backend `.env` only, never a `VITE_` variable.
- Phone numbers live only in `users.phone` and `circle_contacts.phone` (sample rows: fake numbers).
- `request_log` is anonymous: area, hour, mode, lang, channel, intent, route_found.
- Sample rows have `source = 'sample'`.
