"""Static checks on supabase/migrations/001_init.sql: tables, RLS, policies, privacy."""
import re

from backend import config, supabase_verify

SQL = (config.ROOT / "supabase" / "migrations" / "001_init.sql").read_text(encoding="utf-8")
CODE = re.sub(r"--[^\n]*", "", SQL)  # ignore comments
TABLES = supabase_verify.PUBLIC_TABLES + supabase_verify.PRIVATE_TABLES


def table_body(name):
    m = re.search(rf"create table if not exists public\.{name} \((.*?)\n\);", CODE, re.S)
    assert m, f"table {name} missing"
    return m.group(1)


def test_all_tables_created():
    for t in TABLES:
        table_body(t)


def test_rls_enabled_on_every_table():
    for t in TABLES:
        assert re.search(rf"alter table public\.{t}\s+enable row level security", CODE), t


def test_anon_select_only_on_public_tables():
    policies = re.findall(r"create policy \"[^\"]+\"\s+on public\.(\w+)\s+for (\w+) to ([\w, ]+)", CODE)
    assert {p[0] for p in policies} == set(supabase_verify.PUBLIC_TABLES)
    assert all(p[1] == "select" for p in policies)
    for t in supabase_verify.PRIVATE_TABLES:
        assert not re.search(rf"create policy[^;]*on public\.{t}\b", CODE)
        assert re.search(rf"revoke all on [^;]*public\.{t}\b[^;]*from anon", CODE)


def test_phones_only_in_users_and_circle():
    for t in TABLES:
        has_phone = re.search(r"^\s*phone\s+text", table_body(t), re.M) is not None
        assert has_phone == (t in ("users", "circle_contacts", "places")), t
    assert "sample_places_have_no_phone" in CODE  # places.phone must stay NULL for sample rows


def test_request_log_is_anonymous():
    body = table_body("request_log")
    cols = {m.group(1) for m in re.finditer(r"^\s*(\w+)\s+\w", body, re.M)}
    for forbidden in ("phone", "name", "display_name", "text", "body", "user_id", "lat", "lng"):
        assert forbidden not in cols
    for needed in ("area", "hour", "mode", "lang", "channel", "intent", "route_found"):
        assert needed in cols


def test_every_table_has_sample_source():
    for t in TABLES:
        assert re.search(r"source\s+text not null default 'live' check \(source in \('sample', 'live'\)\)", table_body(t)), t


def test_circle_max_five_trigger():
    assert "circle is full (max 5 contacts)" in CODE and "create trigger circle_max_5" in CODE


def test_002_grants_keep_private_tables_closed():
    sql = re.sub(r"--[^\n]*", "", (config.ROOT / "supabase" / "migrations" / "002_api_grants.sql").read_text(encoding="utf-8"))
    anon_grants = re.findall(r"grant select on ([^;]+?)\s+to anon", sql)
    granted = {t.strip().removeprefix("public.") for g in anon_grants for t in g.split(",")}
    assert granted == set(supabase_verify.PUBLIC_TABLES)
    assert not re.search(r"grant (insert|update|delete|all)[^;]*to anon", sql)
    assert "notify pgrst, 'reload schema'" in sql
