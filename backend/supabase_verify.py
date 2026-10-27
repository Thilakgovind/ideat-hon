"""Verify the Supabase schema and RLS after running supabase/migrations/001_init.sql.

    python -m backend.supabase_verify

Prints table names and OK / FAILED only. Never prints keys, URLs or row data.
The one write test (anon insert into places) uses a throwaway id and is removed
with the service key if RLS ever lets it through.
"""
import sys

import httpx

from backend import config

PUBLIC_TABLES = ["stops", "routes", "transfers", "places", "reviews"]
PRIVATE_TABLES = ["users", "circle_contacts", "trips", "trip_events", "request_log"]
TIMEOUT = 30
PROBE_ID = "__rls_probe__"


def _rest(key_name):
    url = config.env("SUPABASE_URL").rstrip("/") + "/rest/v1"
    key = config.env(key_name)
    return url, {"apikey": key, "Authorization": f"Bearer {key}"}


def run() -> list:
    rows = []
    if not (config.env("SUPABASE_URL") and config.env("SUPABASE_SERVICE_KEY") and config.env("SUPABASE_ANON_KEY")):
        return [("supabase", "MISSING", "needs SUPABASE_URL, SUPABASE_ANON_KEY, SUPABASE_SERVICE_KEY")]
    svc_url, svc = _rest("SUPABASE_SERVICE_KEY")
    anon_url, anon = _rest("SUPABASE_ANON_KEY")

    for t in PUBLIC_TABLES + PRIVATE_TABLES:
        r = httpx.get(f"{svc_url}/{t}", params={"select": "*", "limit": 0}, headers=svc, timeout=TIMEOUT)
        rows.append((f"{t}: exists (service key)", "OK" if r.status_code == 200 else "FAILED",
                     "" if r.status_code == 200 else f"HTTP {r.status_code} - run the migration"))

    for t in PUBLIC_TABLES:
        r = httpx.get(f"{anon_url}/{t}", params={"select": "*", "limit": 1}, headers=anon, timeout=TIMEOUT)
        rows.append((f"{t}: anon can read", "OK" if r.status_code == 200 else "FAILED",
                     "" if r.status_code == 200 else f"HTTP {r.status_code}"))

    for t in PRIVATE_TABLES:
        r = httpx.get(f"{anon_url}/{t}", params={"select": "*", "limit": 1}, headers=anon, timeout=TIMEOUT)
        if r.status_code == 404:
            rows.append((f"{t}: anon blocked", "FAILED", "table missing - run the migration"))
            continue
        blocked = r.status_code in (401, 403) or (r.status_code == 200 and r.json() == [])
        rows.append((f"{t}: anon blocked", "OK" if blocked else "FAILED",
                     f"HTTP {r.status_code}" if blocked else "anon could read rows!"))

    probe = {"id": PROBE_ID, "name": "probe", "type": "atm", "area": "probe", "lat": 0, "lng": 0, "source": "sample"}
    r = httpx.post(f"{anon_url}/places", json=probe, headers={**anon, "Prefer": "return=minimal"}, timeout=TIMEOUT)
    write_blocked = r.status_code in (401, 403)
    rows.append(("places: anon write blocked", "OK" if write_blocked else "FAILED", f"HTTP {r.status_code}"))
    if not write_blocked:
        httpx.delete(f"{svc_url}/places", params={"id": f"eq.{PROBE_ID}"}, headers=svc, timeout=TIMEOUT)
    return rows


def main() -> int:
    try:
        rows = run()
    except httpx.HTTPError as e:
        print(f"supabase: FAILED ({type(e).__name__})")
        return 1
    width = max(len(r[0]) for r in rows)
    for name, status, note in rows:
        print(f"  {name.ljust(width)}  {status:<7} {note}")
    failed = sum(r[1] != "OK" for r in rows)
    print(f"\n{len(rows) - failed} OK, {failed} not OK")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
