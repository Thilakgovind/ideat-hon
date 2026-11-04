"""Safe NSS activity catalogue boundary.

Only institution-verified rows may be presented as joinable. The fallback rows
are clearly sample data and cannot expose volunteer contacts or accept requests.
"""
SAMPLE = [
    {"id":"nss_sample_1","institution_name":"Sample NSS Unit — Chennai","nss_unit_id":"sample-chennai-1","activity_type":"women_sports_awareness","district_id":"district_01","verified":False,"status":"sample","source":"sample"},
    {"id":"nss_sample_2","institution_name":"Sample NSS Unit — Madurai","nss_unit_id":"sample-madurai-1","activity_type":"scheme_navigation","district_id":"district_02","verified":False,"status":"sample","source":"sample"},
]

def match(*, district_id=None, activity_type=None, query=None, limit=10):
    q = (query or '').casefold()
    rows = []
    for row in SAMPLE:
        if row['status'] != 'open' or not row['verified']:
            continue
        if district_id and row['district_id'] != district_id:
            continue
        if activity_type and row['activity_type'] != activity_type:
            continue
        if q and q not in ' '.join(str(row.get(k,'')) for k in ('institution_name','activity_type','district_id')).casefold():
            continue
        rows.append(row)
    return rows[:limit]
