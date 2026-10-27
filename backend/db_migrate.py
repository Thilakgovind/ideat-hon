"""Run / check the Supabase migrations over a direct Postgres connection.

    python -m backend.db_migrate --check   # diagnose only (tables, RLS, grants, API schema)
    python -m backend.db_migrate           # apply supabase/migrations/*.sql in order, reload the API, re-check

Uses SUPABASE_DB_URL (session pooler URI) from .env. Backend / your machine only.
Never prints the URL, password, host or row data: only table names, booleans and counts.
"""
import sys
from pathlib import Path

from backend import config

MIGRATIONS = sorted((config.ROOT / "supabase" / "migrations").glob("*.sql"))
TABLES = ["stops", "routes", "transfers", "places", "reviews", "users", "circle_contacts", "trips", "trip_events", "request_log"]
PUBLIC = {"stops", "routes", "transfers", "places", "reviews"}


def _connect():
    import psycopg
    url = config.env("SUPABASE_DB_URL")
    if not url.startswith(("postgresql://", "postgres://")):
        raise SystemExit("SUPABASE_DB_URL: MISSING or not a postgresql:// URI")
    try:
        return psycopg.connect(url, autocommit=True, connect_timeout=15)
    except psycopg.OperationalError as e:
        text = str(e).lower()
        why = ("password rejected" if "password" in text else "host / network unreachable" if "resolve" in text or "timeout" in text
               else "connection refused")
        raise SystemExit(f"SUPABASE_DB_URL: FAILED ({why})") from None


def check(conn) -> list:
    rows = []
    with conn.cursor() as cur:
        cur.execute("select table_name from information_schema.tables where table_schema = 'public' and table_name = any(%s)", (TABLES,))
        present = {r[0] for r in cur.fetchall()}
        cur.execute("select relname, relrowsecurity from pg_class where relnamespace = 'public'::regnamespace and relname = any(%s)", (TABLES,))
        rls = dict(cur.fetchall())
        for t in TABLES:
            if t not in present:
                rows.append((t, "MISSING", "table not created"))
                continue
            cur.execute("select has_table_privilege('service_role', %s, 'insert'), has_table_privilege('anon', %s, 'select'),"
                        " has_table_privilege('anon', %s, 'insert')", (f"public.{t}",) * 3)
            svc, anon_read, anon_write = cur.fetchone()
            ok = rls.get(t) and svc and not anon_write and (anon_read == (t in PUBLIC))
            rows.append((t, "OK" if ok else "FAILED",
                         f"rls={rls.get(t)} service_write={svc} anon_read={anon_read} anon_write={anon_write}"))
        cur.execute("select count(*) from pg_policies where schemaname = 'public' and roles::text like '%anon%'")
        rows.append(("anon policies", "OK", f"{cur.fetchone()[0]} (expected 5)"))
        cur.execute("select setting from pg_settings where name = 'pgrst.db_schemas'")
        r = cur.fetchone()
        cur.execute("select coalesce((select array_to_string(setconfig, ',') from pg_db_role_setting s join pg_roles ro "
                    "on ro.oid = s.setrole where ro.rolname = 'authenticator'), '')")
        conf = cur.fetchone()[0]
        exposed = "public" in (r[0] if r else "") or "public" in conf or not conf
        rows.append(("API exposes public schema", "OK" if exposed else "FAILED", "" if exposed else "add public in Data API settings"))
    return rows


def apply(conn):
    for f in MIGRATIONS:
        with conn.cursor() as cur:
            cur.execute(f.read_text(encoding="utf-8"))
        print(f"  applied {f.name}")
    with conn.cursor() as cur:
        cur.execute("notify pgrst, 'reload schema'")
    print("  API schema cache reload requested")


def main(argv=None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    import psycopg
    conn = _connect()
    try:
        if "--check" not in argv:
            print("== applying migrations ==")
            try:
                apply(conn)
            except psycopg.Error as e:
                diag = getattr(e, "diag", None)
                print(f"  FAILED: SQLSTATE {e.sqlstate} {getattr(diag, 'message_primary', '') or ''}")
                return 1
        print("== database check ==")
        rows = check(conn)
    finally:
        conn.close()
    width = max(len(r[0]) for r in rows)
    for name, status, note in rows:
        print(f"  {name.ljust(width)}  {status:<7} {note}")
    return 0 if all(r[1] == "OK" for r in rows) else 1


if __name__ == "__main__":
    sys.exit(main())
