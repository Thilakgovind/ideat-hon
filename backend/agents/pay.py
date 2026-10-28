"""Pay agent: Razorpay TEST mode order -> verify -> ticket with QR data.

- Live keys (rzp_live_) are refused; the agent falls back to mock.
- Amount always comes from the server's own route plan, never from the client.
- Paying needs explicit confirmation.
"""
import hashlib
import hmac
import uuid
from datetime import timedelta

import httpx

from .. import config, data
from ..guardrails import needs_confirmation

ORDERS_URL = "https://api.razorpay.com/v1/orders"
ORDERS: dict = {}
TICKETS: dict = {}


def create_order(option: dict, frm: str, to: str, confirmed: bool = False, time: str = None) -> dict:
    amount = int(option.get("fare_inr", 0))
    paid_legs = [l for l in option.get("legs", []) if l["mode"] in ("metro", "train") or (l["mode"] == "bus" and not l.get("is_free"))]
    summary = {"from": frm, "to": to, "option_id": option.get("id"), "time": time,
               "lines": [{"label": l["label"], "mode": l["mode"], "fare_inr": l.get("fare_inr", 0),
                          "from": l.get("from"), "to": l.get("to")} for l in option.get("legs", []) if l["mode"] != "walk"],
               "amount_inr": amount}
    if option.get("kind") == "auto":
        return {"error": "auto_not_bookable", "message": "Auto fare is an estimate. Book in the auto app.",
                "booking_links": option.get("booking_links")}
    if amount <= 0 or not paid_legs:
        return {"free": True, "summary": summary, "ticket": _ticket(None, summary, option, "free")}
    if needs_confirmation("pay", confirmed):
        return {"needs_confirmation": True, "action": "pay", "summary": summary,
                "preview": f"Pay Rs {amount} for {' + '.join(x['label'] for x in summary['lines'])}?"}

    mode = config.razorpay_mode()
    receipt = "sp_" + uuid.uuid4().hex[:10]
    order = None
    if mode == "test":
        try:
            r = httpx.post(ORDERS_URL, json={"amount": amount * 100, "currency": "INR", "receipt": receipt},
                           auth=(config.env("RAZORPAY_KEY_ID"), config.env("RAZORPAY_KEY_SECRET")), timeout=10)
            if r.status_code in (200, 201):
                order = {"order_id": r.json()["id"], "mode": "test"}
                config.RUNTIME["razorpay_error"] = None
            else:
                config.RUNTIME["razorpay_error"] = f"HTTP {r.status_code}"
        except httpx.HTTPError:
            config.RUNTIME["razorpay_error"] = "network error"
            order = None
    if order is None:
        order = {"order_id": "order_mock_" + uuid.uuid4().hex[:10], "mode": "mock",
                 "fallback_reason": {"test": "razorpay_error", "refused_live": "live_key_refused"}.get(mode, "no_key")}
    ORDERS[order["order_id"]] = {**order, "summary": summary, "option": option, "status": "created"}
    out = {"order_id": order["order_id"], "amount_paise": amount * 100, "currency": "INR", "mode": order["mode"],
           "summary": summary}
    if order["mode"] == "test":
        out["checkout_key_id"] = config.env("RAZORPAY_KEY_ID")  # publishable test key id, needed by Checkout
    else:
        out["mock_hint"] = "Demo mode: call /api/pay/verify with payment_id 'pay_mock' and signature 'mock'."
        out["fallback_reason"] = order.get("fallback_reason")
    return out


def verify(order_id: str, payment_id: str, signature: str) -> dict:
    order = ORDERS.get(order_id)
    if not order:
        return {"error": "order_not_found"}
    if order["status"] == "paid":
        return {"ticket": TICKETS[order["ticket_id"]]}
    if order["mode"] == "test":
        expected = hmac.new(config.env("RAZORPAY_KEY_SECRET").encode(), f"{order_id}|{payment_id}".encode(),
                            hashlib.sha256).hexdigest()
        valid = hmac.compare_digest(expected, signature or "")
    else:
        valid = signature == "mock" and (payment_id or "").startswith("pay_mock")
    if not valid:
        return {"error": "signature_invalid"}
    order["status"] = "paid"
    ticket = _ticket(payment_id, order["summary"], order["option"], order["mode"])
    order["ticket_id"] = ticket["ticket_id"]
    return {"ticket": ticket}


def _ticket(payment_id, summary, option, mode):
    now = data.now_ist()
    tid = "TKT-" + uuid.uuid4().hex[:8].upper()
    metro = next((l for l in option.get("legs", []) if l["mode"] == "metro"), None)
    train = next((l for l in option.get("legs", []) if l["mode"] == "train"), None)
    lines = "+".join(x["label"] for x in summary["lines"])
    valid_until = (now + timedelta(hours=2)).strftime("%H:%M")
    ticket = {
        "ticket_id": tid, "payment_id": payment_id, "payment_mode": mode,
        "from": summary["from"], "to": summary["to"], "lines": summary["lines"], "amount_inr": summary["amount_inr"],
        "option_id": summary.get("option_id"), "trip_time": summary.get("time"),
        "issued_at": now.isoformat(), "valid_until": valid_until,
        "platform": (metro or train or {}).get("platform"),
        "women_coach": metro["women_coach"] if metro else (train["ladies_coaches"][0]["note"] if train else None),
        "best_exit": metro.get("best_exit") if metro else None,
        "qr_data": f"SAFEPATH|{tid}|{lines}|{summary['from']}>{summary['to']}|INR{summary['amount_inr']}|{valid_until}|{mode.upper()}",
        "is_test": True,  # V1 never takes real money
        "label": "No ticket on ordinary buses: free for women on ordinary (white-board) buses" if mode == "free" else "Test ticket - not valid for travel",
        "source": "sample",
    }
    TICKETS[tid] = ticket
    return ticket
