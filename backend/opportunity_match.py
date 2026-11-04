"""Deterministic opportunity matching over the public Supabase catalogue.

The matcher owns retrieval and ranking; language models may phrase the result but
never invent an opportunity, eligibility rule, deadline, or application action.
"""
from .seed.sports_sample import PUBLIC_TABLES
from .sports_store import read


def _norm(value):
    return " ".join(str(value or "").casefold().replace("–", "-").split())


def match(*, sport=None, district=None, kind=None, query=None, limit=5):
    rows = {table: read(table)[0] for table in PUBLIC_TABLES}
    sports = {row["id"]: row for row in rows["vm_sports"]}
    districts = {row["id"]: row for row in rows["vm_districts"]}
    q = _norm(query)
    # Extract known dimensions from free text before ranking; unknown words never
    # become invented filters or catalogue values.
    if q and not sport:
        sport = next((row["name"] for row in sports.values()
                      if _norm(row["name"]) in q or _norm(row.get("name_ta")) in q), None)
    if q and not district:
        district = next((row["name"] for row in districts.values()
                         if _norm(row["name"]) in q or _norm(row.get("name_ta")) in q), None)
    if q and not kind:
        kind = next((value for value in ("trial", "camp", "tournament") if value in q), None)
    filters = [_norm(value) for value in (sport, district, kind) if value]
    results = []
    for item in rows["vm_opportunities"]:
        sport_row = sports.get(item.get("sport_id"), {})
        district_row = districts.get(item.get("district_id"), {})
        searchable = _norm(" ".join(str(item.get(key, "")) for key in ("name", "kind", "eligibility")))
        searchable += " " + _norm(" ".join(str(sport_row.get(key, "")) for key in ("name", "name_ta")))
        searchable += " " + _norm(" ".join(str(district_row.get(key, "")) for key in ("name", "name_ta")))
        if sport and _norm(sport) not in searchable:
            continue
        if district and _norm(district) not in searchable:
            continue
        if kind and _norm(kind) not in searchable:
            continue
        score = sum(2 for token in q.split() if token and token in searchable)
        if q and score == 0:
            continue
        results.append({**item, "sport": sport_row.get("name", ""), "sport_ta": sport_row.get("name_ta", ""),
                        "district": district_row.get("name", ""), "district_ta": district_row.get("name_ta", ""),
                        "match_score": score})
    results.sort(key=lambda row: (-row["match_score"], row.get("deadline") or "9999-12-31", row["id"]))
    return results[: max(1, min(int(limit), 20))]
