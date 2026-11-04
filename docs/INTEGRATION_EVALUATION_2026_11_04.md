# Avvai integration evaluation — 4 November 2026

Render was explicitly deferred by the user during this evaluation. Preserve existing working-tree changes.

## Verified

- 245 backend tests passed. Production frontend build passed after the application-review UI change.
- Local backend restarted on 127.0.0.1:8000. Health and athlete catalog returned HTTP 200. Unauthenticated offer drafting returned HTTP 401.
- Live provider checks: Sarvam Tamil TTS, Twilio trial account, Razorpay test-key read request, Supabase public/service credentials and textbee device lookup succeeded. No payments or external messages were sent.
- Gemini returned HTTP 503 during the live check. Configured keys do not prove working inference.
- Supabase REST exposes vm_opportunities, vm_athlete_profiles, vm_support_requests and vm_notification_outbox. vm_partner_offers returned HTTP 404. NSS is currently a sample catalogue in backend/nss_support.py; the absence of a vm_nss_units table is not itself an application error.

## Changes

- The opportunity dialog now offers profile-based preparation for verified open listings, displays shared fields for review, allows a note and support category, requires consent, and submits via the existing authenticated claim endpoint with a stable event ID. Sample listings stay view-only.
- n8n guide draft repaired to preserve bounded user text rather than replacing it with one of four generic prompts. The currently published version remains unchanged.
- n8n notification draft repaired: manual/scheduled trigger → authenticated claim of durable pending deliveries → split → Gmail → provider receipt. Existing credential bindings were reused. Execution data retention disabled. Workflow remains inactive; no Gmail messages sent.
- Credential-free, inactive workflow exports saved in n8n/. Notification export passes the structural checker. Remote node configurations validate; live delivery execution remains unverified.

## Unresolved dependencies

- The configured public backend URL returned HTTP 404. Neither local backend nor ngrok was running initially; local backend now works, while ngrok remains offline. Cloud n8n cannot call a loopback backend.
- VM_N8N_NOTIFICATIONS_URL and VM_N8N_WEBHOOK_SECRET are missing while VM_NOTIFICATIONS_ENABLED is true. The current email workflow is scheduled and can poll once reachable; it does not have an event webhook. Do not invent a webhook URL for it.
- vm_partner_offers migration must be applied through an authorized database connection. SUPABASE_DB_URL is absent locally. No schema changes were attempted with the REST service key.
- Verified partner/NSS/organizer records and supported application integrations are still needed. Existing claim logic creates an internal coordinator request, not an application on an external website. Automatic website submission requires an organizer adapter, data mapping, a review/consent step, and submission receipt handling.
- Razorpay remains TEST mode. Trial account validation is not proof of SMS/callback delivery. DigiLocker remains an official-site link without partner OAuth approval.
- Hermes/local trained model inference was not proven by this evaluation. The image does not bundle a local inference runtime.

## Next workflow gate

Restore a reachable backend callback address, update n8n's backend URLs, verify worker credential authentication with a read-only status request, test pending/empty/duplicate delivery handling in isolation, and only then activate opted-in delivery. Apply the partner migration and add verified records before testing profile-based offer submission with a signed-in user and participating coordinator.

## Poster evidence

Keep the prototype and illustrative-persona labels. Add the team's actual survey sample size, dated findings, and quotations only after the team supplies them. The existing poster is an idea submission, not proof of validated impact.

Notion memory could not be read or updated because the connection requires reauthentication. This report is saved in the repository only.
