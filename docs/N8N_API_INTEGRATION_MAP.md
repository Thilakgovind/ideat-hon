# Avvai API and n8n integration map

## Boundary rule

n8n is the workflow coordinator. It must not contain Gemini, Sarvam, Supabase
service-role, TextBee/Twilio, or Razorpay secrets. n8n calls the FastAPI backend;
the backend owns authentication, consent, guardrails, provider retries, and
truthful delivery status.

## Connected flows

| Flow | n8n entry point | Backend boundary | Provider owned by backend |
|---|---|---|---|
| Avvai guidance | `veeramangai-avvai` webhook | `POST /api/veeramangai/chat` | Gemini or local model |
| Public catalog check | manual workflow | `GET /api/veeramangai/catalog` | Supabase read boundary |
| Opted-in updates | one-minute schedule | `/api/veeramangai/automation/claim` and `/receipt` | Gmail OAuth |
| SMS inbound | provider webhook to FastAPI | `POST /api/sms/textbee` or `/api/sms/webhook` | TextBee/Twilio |
| Tamil voice | frontend/backend request | `POST /api/veeramangai/voice` | Sarvam STT/TTS |
| Journey events | backend background event | `N8N_WEBHOOK_URL` | SMS provider, after backend consent checks |

## Deliberately not exposed as public n8n actions

- `POST /api/pay/order` and `/api/pay/verify`: payment state stays server-side;
  Razorpay is TEST-only.
- `POST /api/sos`: SOS must use the authenticated backend and trusted-circle
  rules, not an unauthenticated workflow webhook.
- Supabase writes, profile data, circle contacts, and trip records: accessed by
  backend identity and RLS, never by a public n8n node.
- Raw phone numbers, names, health text, and government identifiers: never sent
  to the LLM or n8n guide workflow.

## n8n environment

Configure this in the n8n runtime, not in a Code node:

```env
AVVAI_BACKEND_URL=https://<public-backend-origin>
```

Bind the notification HTTP nodes to the `X-VM-Automation` Header Auth
credential. Keep all imported workflows inactive until the webhook test,
catalog test, and controlled notification test pass.

## Verification order

1. `GET <AVVAI_BACKEND_URL>/health`
2. Execute the catalog workflow and confirm `storage` reports `supabase`.
3. POST `{ "topic": "opportunities", "lang": "en" }` to the Avvai webhook.
4. POST bounded `{ "text": "Find a trial", "lang": "en" }` and confirm the
   same backend contract works for the demo chat path.
5. Claim notifications with a controlled test account only.
6. Activate the workflow after all receipts are `sent` or explicitly
   `uncertain`; never infer delivery from an HTTP 200 alone.
