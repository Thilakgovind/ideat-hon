"""Idempotent sports-only seeding. No deletion; never seeds private user tables.

python -m backend.seed_sports --local-only
python -m backend.seed_sports --migrate  # optional DB URL; applies only 004
python -m backend.seed_sports
"""
import sys
import httpx
from backend import config
from backend.seed.sports_sample import PUBLIC_TABLES, write

def normalize(rows):
    keys = sorted({k for row in rows for k in row})
    return [{k: row.get(k) for k in keys} for row in rows]

def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    rows = write()
    if '--local-only' in argv:
        for table in PUBLIC_TABLES:
            print(f'{table}: {len(rows[table])}')
        return 0
    if '--migrate' in argv:
        from backend.db_migrate import _connect
        conn = _connect()
        try:
            with conn.cursor() as cur:
                cur.execute((config.ROOT/'supabase/migrations/004_veeramangai_sports.sql').read_text(encoding='utf-8'))
        except Exception:
            print('SPORTS_MIGRATION: FAILED')
            return 1
        finally:
            conn.close()
    if not config.has('supabase'):
        print('SUPABASE_URL / SUPABASE_SERVICE_KEY: MISSING')
        return 1
    base = config.env('SUPABASE_URL').rstrip('/')+'/rest/v1'
    key = config.env('SUPABASE_SERVICE_KEY')
    headers = {'apikey':key,'Authorization':f'Bearer {key}', 'Prefer':'resolution=merge-duplicates,return=minimal'}
    # Preflight every table before writing anything.
    with httpx.Client(timeout=20) as client:
        for table in PUBLIC_TABLES:
            try:
                r=client.get(f'{base}/{table}',params={'select':'id','limit':0},headers=headers)
                if r.status_code != 200:
                    print(f'{table}: FAILED (HTTP {r.status_code}; apply 004 migration first)')
                    return 1
            except httpx.HTTPError:
                print(f'{table}: FAILED')
                return 1
        for table in PUBLIC_TABLES:
            try:
                normalized = normalize(rows[table])
                for start in range(0,len(normalized),200):
                    r=client.post(f'{base}/{table}',params={'on_conflict':'id'},headers=headers,json=normalized[start:start+200])
                    if r.status_code not in (200,201,204):
                        print(f'{table}: FAILED (HTTP {r.status_code})')
                        return 1
                # Verify all seeded IDs, including source labels, rather than printing attempted counts.
                expected={row['id'] for row in rows[table]}
                found=set()
                for start in range(0,len(normalized),100):
                    ids=','.join(row['id'] for row in normalized[start:start+100])
                    check=client.get(f'{base}/{table}',headers=headers,params={'select':'id,source','id':'in.('+ids+')','limit':100})
                    if check.status_code != 200:
                        print(f'{table}: FAILED (verification)')
                        return 1
                    found.update(r['id'] for r in check.json() if r['source']=='sample')
                if found != expected:
                    print(f'{table}: FAILED (verification)')
                    return 1
                print(f'{table}: {len(expected)}')
            except (httpx.HTTPError,ValueError,KeyError,TypeError):
                print(f'{table}: FAILED')
                return 1
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
