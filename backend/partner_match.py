"""Approved sponsor/merchant offer retrieval; sample rows are never claimable."""
import httpx
from . import config


def read():
    if not config.has('supabase'):
        return [], 'sample_fallback'
    key = config.env('SUPABASE_SERVICE_KEY')
    try:
        r = httpx.get(config.env('SUPABASE_URL').rstrip('/') + '/rest/v1/vm_partner_offers',
                      headers={'apikey': key, 'Authorization': f'Bearer {key}'},
                      params={'select': '*', 'verified': 'eq.true', 'status': 'eq.open', 'limit': 100}, timeout=5)
        r.raise_for_status()
        return r.json() if isinstance(r.json(), list) else [], 'supabase'
    except (httpx.HTTPError, ValueError):
        return [], 'sample_fallback'


def match(*, offer_type=None, sport_id=None, district_id=None, query=None, limit=5):
    rows, source = read()
    q = str(query or '').casefold()
    out = []
    for row in rows:
        if row.get('verified') is not True or row.get('status') != 'open':
            continue
        if offer_type and row.get('offer_type') != offer_type:
            continue
        if sport_id and row.get('sport_id') != sport_id:
            continue
        if district_id and row.get('district_id') != district_id:
            continue
        searchable = ' '.join(str(row.get(k, '')) for k in ('partner_name', 'offer_type', 'eligibility')).casefold()
        score = sum(1 for token in q.split() if token and token in searchable)
        if q and not score:
            continue
        out.append({**row, 'match_score': score, 'source_store': source})
    out.sort(key=lambda row: (-row['match_score'], row['id']))
    return out[:max(1, min(int(limit), 20))]
