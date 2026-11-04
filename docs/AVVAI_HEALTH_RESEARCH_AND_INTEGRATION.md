# Avvai health-support research and integration boundary

Updated: 2026-11-04

This document separates evidence-backed public information from demo data. Avvai is a sports-support and opportunity assistant, not a diagnostic or emergency-care service.

## Evidence used

- India’s official ERSS says 112 is the pan-India emergency number for police, fire and health emergencies, including women-safety emergencies: https://112.gov.in/
- The Directorate General of Health Services says Tele-MANAS can be reached at 14416 or 1800-89-14416 and provides counselling, referral and follow-up pathways: https://dghs.mohfw.gov.in/national-mental-health-programme.php
- Tamil Nadu’s health department lists government mental-health facilities and district mental-health services: https://www.tnhealth.org/treatment.htm
- NFHS-5 reports that 53% of women aged 15–49 in Tamil Nadu were anaemic in 2019–21. This is a population survey statistic, not an individual diagnosis: https://www.mohfw.gov.in/sites/default/files/NFHS-5_Phase-II_0.pdf
- The IOC RED-S consensus describes low energy availability as potentially affecting reproductive, musculoskeletal, immune, cardiovascular and psychological function; screening is not diagnosis: https://doi.org/10.1136/bjsports-2023-106994
- Current reviews do not establish a simple causal rule that a normal menstrual-cycle phase predicts injury or the “best” workout. Avvai must not prescribe phase-based training: https://pmc.ncbi.nlm.nih.gov/articles/PMC9958828/

## Ten product areas and their grounded integration

1. Opportunities: match only rows in Supabase/sample catalogue; show source, eligibility and deadline; never invent a scheme.
2. Funding and fee help: create an editable request draft; submit only after identity and explicit consent; no payment promise.
3. Partner offers: return only verified, open partner rows. The migration file is `supabase/migrations/20261104010000_partner_offers.sql`; live deployment is still pending because no Supabase project is connected to this workspace.
4. Profile and form assistance: prefill only user-provided fields; show a review screen; never infer caste, income, health, eligibility or documents.
5. Tamil/Tanglish voice: Sarvam STT/TTS uses the same guarded backend response as chat; no health history is sent to the model.
6. SMS/callback: TextBee/Twilio paths remain transport adapters. A missing provider must fall back to demo mode and must not claim delivery.
7. Trusted-circle notifications: opt-in only, maximum five contacts, and only during an active journey/event. Health or menstrual details are never shared by default.
8. Mental-health support: Avvai gives supportive language and official referral numbers. It does not act as a therapist. Crisis terms bypass Gemini/local generation and show 112 plus Tele-MANAS.
9. Injury, fatigue and menstrual support: symptom-led check-ins can suggest rest, clinician assessment or a sports professional. No diagnosis, hormone-level inference, medication dose or return-to-play clearance.
10. Safety, evaluation and policy: guardrails and regression tests verify prompt-injection resistance, privacy, source labels, refusal of unsafe medical requests and no false “sent/approved” claims.

### NSS integration

NSS is suitable for a verified community-service directory, not as a medical or security guarantee. The official NSS objectives include community problem-solving, civic responsibility, emergency capacity and mobilising participation: https://nss.gov.in/about/mission-objectives. NSS is a student volunteer programme under the Ministry of Youth Affairs & Sports, so an NSS volunteer must never be presented as a clinician, police officer, counsellor or guaranteed escort: https://www.nss.gov.in/en/youth-affairs/national-service-scheme.

The live design is:

- an institution or NSS Programme Officer verifies each unit;
- a unit publishes an activity such as women’s-sports awareness, digital-literacy help, event navigation or public-scheme orientation;
- the athlete sees location, date, organiser, contact and verification date;
- joining is an explicit request, not an automatic assignment;
- no volunteer receives an athlete’s health, menstrual, identity or live-location data by default;
- safeguarding escalation goes to the institution’s designated contact or official emergency services, never to an unverified volunteer.

Recommended data fields: `institution_name`, `nss_unit_id`, `programme_officer_contact`, `activity_type`, `district_id`, `event_time`, `capacity`, `verified`, `verification_source`, `last_verified_at`, `status`. Do not store volunteer personal phone numbers in the public catalogue.

## Hormone and body-support boundary

Do not build a hormone tracker in V1. A calendar cannot measure hormone levels. If an athlete opts in, the safe minimum is a private, deletable symptom check-in: `symptoms`, `impact_on_training`, `urgent_flag`, `consent`, `created_at`. Do not collect exact cycle dates, lab values, photos, weight targets or reproductive details unless a later clinical/privacy review explicitly approves it. The coach sees only the neutral adjustment the athlete chooses to share.

The app may say: “You can request rest or a lighter session and speak with a clinician.” It must not say: “Your hormones are low,” “you have RED-S,” “train in this phase,” or “take this supplement.”

## Mental-health flow

1. Detect only high-level safety language locally; do not send crisis text to a generative model.
2. If immediate danger or self-harm risk is expressed, show 112 and advise moving near a trusted person / emergency department.
3. Offer Tele-MANAS 14416 or 1800-89-14416 for counselling and referral.
4. Do not automatically alert a coach or family member. Ask separately for consent; emergency services are the exception when the user directly initiates an SOS.
5. Do not store the message as a health history or expose it in analytics.

## What is real versus demo

Government helplines and public evidence above are real. Catalogue opportunities, partner offers, safe places and professional directories must carry a source URL, verification date and `sample`/`verified` status. A private mental-health app should not be scraped or represented as an Avvai partner without written permission. For live professionals, use a manually verified directory or referral institution and display “confirm availability and credentials.”

## Integration status

The backend already has guarded opportunity matching, offer drafts/claims, Sarvam voice, n8n orchestration, SMS adapters, Supabase fallback and regression tests. The next safe live step is applying the partner-offers migration in the actual Supabase project, then adding a stateless health check-in endpoint and UI copy review. Until that migration is applied, partner matching correctly returns no live rows rather than inventing sponsors.
