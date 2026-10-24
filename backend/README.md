# SafePath V1 — Backend (FastAPI)

AVAL's agents behind one API. Works fully in **demo mode** with no keys: every
external service has a mock, and all data in `/data` is labelled `"source": "sample"`.

## Run (Windows, from the repo root)

```bash
python -m venv .venv
.venv/Scripts/python -m pip install -r backend/requirements.txt
.venv/Scripts/python -m uvicorn backend.app:app --reload --port 8000
```

Open http://localhost:8000/health and http://localhost:8000/docs (interactive API).

## Tests

```bash
.venv/Scripts/python -m pytest backend/tests -q
```

Tests force every service into mock mode, so they never call a real API.

## Keys (optional)

Copy `.env.example` to `.env` and fill in what you have. A service is **real**
only when all its keys are set; otherwise it is a mock. `/health` shows which.

| Service | Keys | Mock behaviour |
|---|---|---|
| Gemini (intake) | `GEMINI_API_KEY` (+ optional `GEMINI_MODEL`, default `gemini-2.5-flash`) | rule-based Tamil/English/Tanglish parser |
| Sarvam (voice) | `SARVAM_API_KEY` | STT returns the `hint` / demo sentence; TTS returns no audio (use device speech) |
| Twilio (SMS) | `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `TWILIO_PHONE_NUMBER` | messages logged to `/api/demo/outbox`, marked "not sent" |
| Razorpay | `RAZORPAY_KEY_ID`, `RAZORPAY_KEY_SECRET` | `rzp_test_` keys only; live keys are refused; mock verify with `signature: "mock"` |
| n8n | `N8N_WEBHOOK_URL` | trip/SOS events not forwarded |
| Supabase, MapTiler | — | not used by the V1 backend (in-memory store; maps are in the frontend) |

## Layout

```
backend/
  app.py            API server
  orchestrator.py   intake -> agents -> reply card + "What AVAL did" steps
  guardrails.py     PII stripping, grounding, confirmations, location, anonymous logs
  agents/           intake, route, safety, places, circle, pay, voice, sms
  tests/            one file per agent + guardrails + API
```

## Endpoints

`GET /health` · `POST /api/aval/chat` · `POST /api/aval/voice` · `GET /api/routes` ·
`GET /api/safe-route` · `GET /api/places` · `GET /api/places/{id}` · `POST /api/trip/start|checkin|reached` ·
`GET /api/trip/{id}` · `POST /api/sos` · `GET|POST /api/circle` · `POST /api/pay/order|verify` ·
`POST /api/sms/webhook` · `GET /api/demo/outbox`

Point a Twilio number's "A message comes in" webhook at `https://<public-url>/api/sms/webhook`.

## Known V1 limits
- State (circle, trips, orders) is in memory and resets on restart.
- Twilio webhook signatures are not validated yet.
- `agents/route_and_sakhi_lookup.py` (the earlier prototype) is superseded by `backend/agents/route.py`.
