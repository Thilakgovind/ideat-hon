# SafePath V1.1 — going live (Windows)

Everything works without these steps (demo mode). Do them to receive real SMS,
get call-backs and route the demo page through n8n. Never paste keys into chat;
set them with the hidden prompt:

```powershell
.venv\Scripts\python -m backend.set_env NAME
```

Check at any time (prints names and OK / MISSING / FAILED only):

```powershell
.venv\Scripts\python -m backend.check_keys
```

---

## 1. Public URL with ngrok

Textbee, Twilio and n8n must reach your laptop.

1. Install once: `winget install ngrok.ngrok` (or download from https://ngrok.com/download).
2. Sign in at https://dashboard.ngrok.com → **Your Authtoken** → copy, then in PowerShell:
   `ngrok config add-authtoken <paste>` (type it in your terminal, not in chat).
3. Start the backend in one terminal:
   `.venv\Scripts\python -m uvicorn backend.app:app --port 8000`
4. In a second terminal: `ngrok http 8000`.
   Copy the **Forwarding** `https://….ngrok-free.app` URL.
5. Save it: `.venv\Scripts\python -m backend.set_env PUBLIC_BACKEND_URL` → paste → Enter.
6. Restart the backend (Ctrl+C, run step 3 again). `http://localhost:8000/health` now shows
   `"call_back": "ready"` when Twilio keys are present.

The free ngrok URL changes every time ngrok restarts: repeat steps 5–6 and update the
textbee webhook and n8n boxes below.

## 2. textbee (main SMS)

1. Android phone: install the textbee app, sign in, allow **SMS send + receive** permissions,
   keep the app running (battery optimisation off for it).
2. `.env`: `SMS_PROVIDER=textbee`, `TEXTBEE_API_KEY`, `TEXTBEE_DEVICE_ID` (check_keys shows "device found").
3. Inbound webhook: https://textbee.dev → **Dashboard** → **Webhooks** → **Add webhook**
   - URL: `{PUBLIC_BACKEND_URL}/api/sms/textbee`
   - Event: **SMS received** (`MESSAGE_RECEIVED`)
   - Save, then copy the **signing secret** and store it:
     `.venv\Scripts\python -m backend.set_env TEXTBEE_WEBHOOK_SECRET`
4. Test: from another phone, text the textbee phone `nungambakkam bus`. You get the 21G reply.
   Commands: `START`, `REACHED`, `HELP`, `CALL`.
5. `http://localhost:8000/api/demo/outbox` shows every send with provider + status (phones masked).

Indian numbers: messages leave from your Android SIM, so normal SIM rates and limits apply.

## 3. Twilio call-back (CALL) — optional

- Needs Twilio keys + `PUBLIC_BACKEND_URL`. No console webhook is needed for call-backs:
  the backend gives Twilio the URLs when it places the call.
- **Trial accounts** can only call **verified numbers**: Twilio Console → Phone Numbers →
  Manage → **Verified Caller IDs** → add the phone that will text `CALL`.
  Trial calls start with a short Twilio announcement.
- Flow: text `CALL` → Twilio rings her → AVAL greets in Tamil (Sarvam) → she speaks after the
  beep → Sarvam STT → AVAL → spoken Tamil answer (~20 s max). Any failure → SMS instead.
- Optional Twilio inbound SMS: Phone number → Messaging → "A message comes in" →
  `{PUBLIC_BACKEND_URL}/api/sms/webhook` (POST). Signatures are checked.

## 4. n8n (ideathon-m.app.n8n.cloud)

The workflow **"SafePath — AVAL Orchestrator"** already exists. Do not change its logic.

1. Open it and paste your `PUBLIC_BACKEND_URL` into the two boxes:
   **"Config + clean input"** and **"Backend URL"**. Save, and switch the workflow **Active**.
2. `.env` (with set_env):
   - `N8N_ORCHESTRATOR_URL` = `https://ideathon-m.app.n8n.cloud/webhook/safepath-aval`
   - `N8N_WEBHOOK_URL` = `https://ideathon-m.app.n8n.cloud/webhook/safepath-events`
   (Use `/webhook/…`, not `/webhook-test/…`, once the workflow is active.)
3. Restart the backend. The demo page (`/demo`) now shows **via n8n** under the reply; if n8n is
   down it falls back to **via backend** automatically.
4. Trip events (start, reached, alert, sos) are POSTed to `N8N_WEBHOOK_URL` in the background.
   They carry trip ids and times only, never phone numbers or names.

## 5. Supabase (when you are ready)

```powershell
.venv\Scripts\python -m backend.set_env SUPABASE_DB_URL    # Session pooler URI from Connect
.venv\Scripts\python -m backend.db_migrate                 # applies 001 + 002, checks RLS and grants
.venv\Scripts\python -m backend.supabase_verify            # API view: anon read-only, private tables blocked
.venv\Scripts\python -m backend.seed_supabase              # ~1,150 sample rows, prints counts only
```

Restart the backend: `/health` → `storage.mode` becomes `supabase`.

## 6. Launch plan (after the ideathon)

Production SMS in India needs **DLT registration** (entity + sender ID + templates) and an
Indian virtual number: use **MSG91** or **Exotel** for SMS and voice. Swap the provider in
`backend/agents/sms.py`; the orchestrator does not change.
