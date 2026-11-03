"""Private Veeramangai persistence. Never substitutes demo data for a failed write."""
import httpx
from fastapi import HTTPException
from . import config


def call(path, *, method="GET", params=None, body=None, prefer=None):
    if not config.has("supabase"):
        raise HTTPException(503, "Support storage is not configured.")
    key = config.env("SUPABASE_SERVICE_KEY")
    headers = {"apikey": key, "Authorization": f"Bearer {key}"}
    if prefer:
        headers["Prefer"] = prefer
    try:
        r = httpx.request(method, config.env("SUPABASE_URL").rstrip("/") + "/rest/v1/" + path,
                          headers=headers, params=params, json=body, timeout=15, follow_redirects=False)
    except httpx.HTTPError:
        raise HTTPException(503, "Storage could not confirm the operation. Retry with the same event ID.") from None
    if r.status_code >= 300:
        # Never return upstream diagnostics, SQL, tokens or personal fields.
        try:
            code = r.json().get("message", "")
        except ValueError:
            code = ""
        errors = {"event_conflict": (409, "This event ID was already used for different data."),
                  "request_not_found": (404, "Request not found."),
                  "request_forbidden": (403, "This request belongs to another person."),
                  "invalid_transition": (409, "The request changed. Refresh before responding."),
                  "profile_required": (409, "Save your athlete profile first."),
                  "sample_opportunity": (422, "Sample opportunities cannot accept applications."),
                  "claim_conflict": (409, "Delivery claim is no longer valid.")}
        status, message = errors.get(code, (503, "Support storage is unavailable or its migration is pending."))
        raise HTTPException(status, message)
    return r.json() if r.content else None


def rpc(name, **body):
    return call("rpc/" + name, method="POST", body=body)


def page(table, *, filters, offset=0, limit=25, columns="*"):
    rows = call(table, params={"select": columns, **filters, "order": "created_at.desc,id.desc",
                               "offset": offset, "limit": limit + 1})
    return {"items": rows[:limit], "next_offset": offset + limit if len(rows) > limit else None}
