# Avvai guardrails, harness and Code Red

Implemented 2026-11-03 for the athlete assistant, chat and voice (voice calls assistant).

## Runtime boundary

`backend/avvai_harness.py` screens common instruction-override attempts. Existing
health policies run first so urgent guidance is preserved. Detection normalizes
Unicode and removes format characters; it is heuristic and does not promise
coverage of encoded attacks, all Tamil/Tanglish, or multi-turn attacks.

Chat has no tool execution capability. Saved requests continue to use the
existing authenticated workflow endpoints and database authorization. This
change does not replace or certify those controls.

Only server-defined topic and language are sent to the guidance workflow;
model prompts use canonical app guidance rather than athlete free text.
Ollama, Gemini and n8n replies are validated against that canonical guidance.
Different wording falls back, even when benign. This intentionally limits
paraphrasing until a stronger grounded response contract is available. Provider
metadata cannot introduce actions, links or other model-owned fields.
Existing provider timeouts remain in force. The harness adds no retries and no
side effects; database workflows remain responsible for submission idempotency.
No new transcript logging or health-history storage is introduced.

## Code Red

Run offline regression checks:

    .venv/Scripts/python -m pytest backend/tests/test_code_red.py -q

The synthetic suite checks instruction overrides, role spoofing, Tamil/Tanglish
samples, zero-width obfuscation, fabricated medical/action claims, malicious
provider output, urgent guidance preservation and legitimate guidance. HTTP and
model calls are mocked. No attacks are sent to external systems.

A critical leakage or unauthorized-action failure blocks release. These tests
cover the chat boundary; they are not a complete security audit, clinical safety
assessment, model benchmark or multilingual evaluation. The rejected T4 adapter
remains undeployed. Broader multi-turn and encoding tests, authorization matrix
checks and independently reviewed health examples remain future work.
