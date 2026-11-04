# Veeramangai sports data and n8n

This module adds eight `vm_` tables. It does not clear or replace SafePath data.
Public demo records: 12 districts, 6 sports, 72 fictional organizations,
648 fictional opportunities and 288 support resources (1,026 records total).
District and sport names are reference labels; listings are not official notices.
No real dates, business endorsements, funding promises, phone numbers or health histories are seeded.

## Supabase

Use the project matching `SUPABASE_URL` in the root `.env`.
In Supabase's SQL Editor, create a new query, paste the entire file
`supabase/migrations/004_veeramangai_sports.sql`, and click Run.
This file has its own transaction and is safe to rerun.

From Windows PowerShell:

```powershell
Set-Location 'C:\Users\THILAK GOVIND\OneDrive\Desktop\murdermurugaveni'
python -m backend.seed_sports
```

Alternatively, if `SUPABASE_DB_URL` is saved locally, apply only the new migration and seed:

```powershell
python -m backend.seed_sports --migrate
```

The seeder upserts stable IDs in dependency order and verifies seeded IDs before
printing counts. It never deletes rows or seeds private tables. It normalizes all
bulk objects to matching keys. Network failures can leave earlier tables seeded;
rerun the command to finish safely.

Offline generation:

```powershell
python -m backend.seed_sports --local-only
```

The generated JSON is `data/veeramangai/sports_sample.json`.
`GET /api/veeramangai/catalog` reads Supabase when available and otherwise uses
the same deterministic sample generator. The opportunities screen consumes this API.
Restart the backend after adding the endpoint.

## Access rules

RLS is enabled for all eight tables. Anonymous/authenticated clients can SELECT
the five reference tables. Signed-in athletes can SELECT only their own profile,
requests and related events. Browser writes are denied. Private tables start empty.
The backend service key can write; backend request handlers must verify identity
and allowed status changes before using it. Profiles, submissions and coordinator
approvals are schema groundwork: existing request forms still save browser drafts.
No unrestricted browser approval path is provided.

## n8n access and workflow

### Trial account preparation

Cloud API access is unavailable on the current trial. Workflow editing, importing
and manual execution can still be done in the signed-in browser.
The catalog workflow has been configured and executed successfully in n8n Cloud:
12 districts, 6 sports, 648 opportunities, 288 resources, database `supabase`.

Keep the backend and tunnel running:

```powershell
python -m uvicorn backend.app:app --host 127.0.0.1 --port 8000 --no-access-log
ngrok http 8000
```

After a tunnel restart, run `python -m backend.prepare_n8n`. This checks the
public catalog, updates PUBLIC_BACKEND_URL locally and refreshes the two import
files without embedding credentials. It does not update n8n Cloud automatically;
update its HTTP nodes to the new URL or import the refreshed files.
The catalog workflow is a manual diagnostic, not a scheduled notification worker.

The Supabase connector must be connected to an account containing this project
before it can manage the database. An empty connector project list does not mean
the existing `.env` service credentials are invalid.

For n8n management, save `N8N_BASE_URL` (your HTTPS dashboard origin) and
`N8N_API_KEY` in the root `.env`. Generate an API key in Settings > n8n API >
Create API key. Keys remain backend/local only. Check without displaying values:

```powershell
python -m backend.check_n8n
```

Import `n8n/veeramangai_avvai.json` as a **new inactive workflow**.
Set the n8n environment variable `AVVAI_BACKEND_URL` to the current public
backend HTTPS origin. The workflow uses that variable; it contains no tunnel
URL and should not be edited per deployment.
The guide webhook accepts either the app contract (`text`, `lang`) or an
allowlisted topic (`topic`, `lang`), truncates text to 1500 characters, and has
no ability to access private profiles, send messages, approve requests or pay.
Test the webhook and the backend response before publishing/activating.

Input schema: `{ "topic": "opportunities|funding|travel|support", "lang": "ta|en" }`.
The workflow forwards only the bounded guide text and language to the backend.
Successful/error execution saving is disabled in the import template. There is
no payment, application, approval or SMS node. The app sends requests to
`/api/veeramangai/assistant`, which forwards topic/language to the webhook and
falls back to backend guidance if n8n fails; the demo chat path can forward the
user's bounded text through `/api/demo/chat` when configured.

The notification import `n8n/veeramangai_notifications.json` is a separate,
inactive worker. Bind both HTTP Request nodes to an n8n Header Auth credential
named `X-VM-Automation` whose value matches the backend's VM_AUTOMATION_SECRET.
Bind Send generic update to the account's Gmail OAuth credential. No credentials
are embedded in the file. Only enable VM_NOTIFICATIONS_ENABLED after binding and
testing consent with controlled accounts. The worker claims pending rows, sends
generic updates, and records the Gmail ID or `uncertain` on error. It never
automatically retries uncertain deliveries. The inactive import includes a
one-minute schedule plus the manual trigger; activate it only after credentials,
the worker secret, and consent-controlled test accounts are verified.

For a database read check, import `n8n/veeramangai_supabase_catalog.json` as a
separate workflow. It uses `AVVAI_BACKEND_URL`; execute it manually after that
variable is configured. It returns public catalog counts and `supabase` or
`sample_fallback`; a successful HTTP request alone does not prove live storage.
This workflow uses the backend as the Supabase boundary and contains no API keys.
It does not migrate, seed, create projects, send messages or approve requests.

## Complete workflow migration

After the sports migration has succeeded, run the whole contents of
`supabase/migrations/20261102193817_veeramangai_workflow.sql` in a second
Supabase SQL Editor query. It adds the transactional request event table and
notification outbox used by the backend. Run it once; it is idempotent.

The backend must then have these server-only settings in `.env`:

```env
VM_COORDINATOR_USER_ID=<UUID of the verified coordinator Supabase user>
VM_AUTOMATION_SECRET=<random secret, at least 32 characters>
VM_N8N_NOTIFICATIONS_URL=https://<n8n-host>/webhook/veeramangai-notifications
VM_N8N_WEBHOOK_SECRET=<different random secret, at least 32 characters>
N8N_ORCHESTRATOR_URL=https://<n8n-host>/webhook/veeramangai-avvai
```

The values are placeholders; do not commit them or paste them into chat.
The coordinator UUID is obtained from the authenticated Supabase user record,
not invented. The n8n notification workflow must call
`POST /api/veeramangai/automation/claim` with `X-VM-Automation` and then call
`POST /api/veeramangai/automation/receipt` only after the provider confirms
delivery. A failed provider call must use `status: uncertain`, never `sent`.
Keep the old SafePath workflow separate.

Official references:
- https://docs.n8n.io/api/authentication/
- https://supabase.com/docs/guides/database/postgres/row-level-security
