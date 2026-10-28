# SafePath — Project Brief for Claude Code

SafePath is a women's travel companion for Chennai (SDG 5: Gender Equality).
It finds the safest way to travel (bus / metro / train / auto), safe places to wait,
and keeps a trusted circle informed. Works on keypad phones (SMS + Tamil voice) and smartphones (web app).

**Golden rule: V1 must work end-to-end for ONE demo route before adding anything else.**
Demo route: **Anna Nagar West → Nungambakkam** (real MTC bus 40H and others from ChennaiGTFS, free on ordinary buses, plus Metro alternative).

---

## 1. Scope

### V1 — build now (must work live in the demo)
1. **SMS route helper** (keypad phones): SMS in → best route + free/paid + fare + safe waiting spot → SMS out.
2. **Journey Watch**: `START` → reminder at ETA → alert to trusted contact if no `REACHED`.
3. **Web app (smartphone)**: search a trip → route card (bus/metro, free badge, fare, switch point) → safe places list with filters → "Start trip" with trusted circle.
4. **Tamil voice (Sarvam AI)**: speak a trip in Tamil/Tanglish → spoken Tamil answer. Same backend as SMS.
5. **Demo page for judges**: keypad-phone mockup that sends real SMS-style text to the backend + "what the agents did" panel.

### V2 — only after V1 is done
- Live bus arrivals (real MTC feed if available), suburban train, auto booking deep links (Namma Yatri / Rapido / Ola / Uber).
- Policy dashboard (demand map + gaps where no safe place exists).
- Women's ratings of places ("felt safe here").

### Not doing
- Rating places by "what kind of people" go there (profiling). Use neutral signals only (see §5).
- Always-on location sharing. Location is shared only during a trip or SOS.

---

## 2. Architecture

```
Keypad phone ──SMS──► SMS gateway ─┐
Keypad phone ──call─► Sarvam voice ─┤
Smartphone ──web app──────────────┤
                                  ▼
                       n8n  Orchestrator workflow
                                  │
        ┌─────────────┬───────────┼─────────────┬──────────────┐
        ▼             ▼           ▼             ▼              ▼
   Intake Agent   Route Agent  Safety Agent  Circle Agent   Reply Formatter
   (Gemini: parse (code: match (code: rank   (Journey Watch, (SMS ≤160 chars /
    text → JSON)   data files)  safe places)  alerts)         voice / web JSON)
```

- **LLM is used only to parse and to phrase replies.** Routes, fares and places come from data files via code, so the AI cannot invent a bus.
- Strip phone numbers before any LLM call. Send only the message text.
- If the LLM fails or returns bad JSON → fallback SMS: `Sorry, send place name. Eg: Nungambakkam bus`.

---

## 3. API keys checklist (store in `.env`, never commit)

| Key | Used for | Status |
|---|---|---|
| `GEMINI_API_KEY` | Intake Agent + reply phrasing | ☐ |
| `SARVAM_API_KEY` | Tamil speech-to-text + text-to-speech | ☐ |
| `SMS_GATEWAY_KEY` (Twilio trial, or an Indian gateway) | SMS in/out. Note: Indian bulk SMS needs DLT registration — use trial/verified numbers for the demo | ☐ |
| `GOOGLE_MAPS_API_KEY` or OpenStreetMap (free) | Map + places on demo roads | ☐ |
| `N8N_WEBHOOK_URL` | Backend entry point | ☐ |
| Firebase / Supabase keys | Trips, circle, logs | ☐ |

Provide `.env.example` with all names and empty values.

---

## 4. Datasets (`/data`)

Real where available, otherwise **mock and labelled `"source": "sample"`**.

**routes.json**
```json
{ "id": "MTC-18683", "number": "40H", "mode": "bus", "free_for_women": true, "fare_inr": 0,
  "free_note": "Free on ordinary (white-board) MTC buses under Vidiyal Payanam. Deluxe / AC buses are paid.",
  "stops": [{ "name": "Anna Nagar West Depot", "min": 40, "area": "Anna Nagar West" }, "...",
            { "name": "Nungambakkam Railway Station", "min": 57, "area": "Nungambakkam" }],
  "departures": ["07:10", "07:20", "..."], "one_way": true, "source": "ChennaiGTFS (MTC)" }
```
Modes: `bus`, `metro`, `train`, `auto`. Metro: fare by station pair. Auto: estimated fare only + booking link.

**transfers.json** — switch points
```json
{ "at": "Koyambedu", "from": "bus", "to": "metro", "walk_min": 4, "lit": true }
```

**places.json** — safe places along demo roads
```json
{ "id": "p1", "name": "Lakshmi SHG Kiosk", "type": "shg_kiosk",
  "near_stop": "Anna Nagar West", "lat": 13.09, "lng": 80.20,
  "open": "06:00", "close": "21:00", "women_run": true, "well_lit": true,
  "crowd_by_hour": { "07": "busy", "21": "moderate" }, "source": "sample" }
```
Types: `pharmacy`, `grocery`, `tea_shop`, `atm`, `hospital`, `police_booth`, `shg_kiosk`, `petrol_bunk`, `bus_shelter`.

**circle** (database, per user)
```json
{ "user_id": "u_hash", "contacts": [{ "label": "Amma", "phone": "+91...", "accepted": true }] }
```
Max 5 contacts. Both sides must accept.

**trips** (database)
```json
{ "trip_id": "t1", "user_id": "u_hash", "route": "MTC-18683", "start": "08:20",
  "eta": "08:39", "status": "active|reached|alerted" }
```

**request_log** — anonymous only: area, hour, mode, no phone, no name.

---

## 5. Safe-places ranking (Safety Agent)

Score each place near the stop using only neutral signals:
- open now (+3), open 24h (+1)
- women-run / SHG partner (+2)
- well lit (+2 after 6pm)
- crowd level now: busy/moderate (+2), empty (−2 after 7pm)
- women's ratings (V2)

Show: **how many** places, **which types**, **busy or quiet now**. Filters: type, open now, women-run, well lit.
Always label sample data in the UI ("Sample data for demo").

---

## 6. Message formats

**SMS (≤160 chars, Tanglish/English by default; Tamil script only if user wrote Tamil — Tamil SMS fits ~70 chars)**
```
BUS 40H at Anna Nagar West Depot
Next ~8:20. Free for women on white-board buses. Safe wait: Lakshmi SHG Kiosk 691m
Reply START when you board
```
Never say a specific bus is free. The only wording: "Free for women on ordinary (white-board) buses" (SMS short form: "Free for women on white-board buses").
Commands: `START`, `REACHED`, `HELP`. Numbered choices for ambiguity: `1 Nungambakkam 2 Nanganallur`.
HELP reply: `Women helpline 181. Police 100. Your contact is informed.` (only if actually sent)

**Journey Watch timing**: ETA → reminder to her; ETA + 10 min → SMS to circle with last known stop and time.

**Voice (Sarvam)**: same JSON → short Tamil sentence, spoken. Max ~20 seconds.

---

## 7. Design system

| Token | Value |
|---|---|
| Plum (primary) | `#4A1D6E` |
| Pink (free bus) | `#E0457B` |
| Marigold (highlight) | `#F6A623` |
| Teal (safe/success) | `#0E7C74` |
| Cream (background) | `#FFF7EC` |
| Ink (text) | `#24132F` |

Fonts (all OFL, keep `OFL.txt` in `/public/fonts`):
- Headings/logo: **Noto Serif Tamil** Bold/ExtraBold (Tamil), Noto Sans Bold (English)
- Body/buttons: **Noto Sans Tamil** + **Noto Sans**, 400/500; minimum 16px
- Tap targets ≥ 48px, icons always with text, Tamil/English toggle on every screen, works on slow 3G.

---

## 8. Privacy rules (show these in the app and pitch)
- No names or phone numbers in logs or dashboards; locations rounded to area.
- Circle: both sides opt in, max 5, removable anytime.
- Location shared only during an active trip or SOS; never in the background.
- LLM calls get message text only, never phone numbers.
- Never claim an alert was sent unless it was.

---

## 9. Folder structure
```
/data            routes.json transfers.json places.json (sample-labelled)
/agents          intake_prompt.md reply_prompt.md safety_rules.md
/n8n             orchestrator.json journey_watch.json
/web             app (route card, places + filters, circle, voice button, demo page)
/public/fonts    Noto fonts + OFL.txt
.env.example
```

## 10. Definition of done for V1
- [ ] SMS "nungambakkam bus" → correct real-bus reply (eg 40H / 147B) with safe place in < 5 s
- [ ] START / REACHED / alert-to-contact works with a real phone
- [ ] Web: route card + 3+ safe places with working filters
- [ ] Tamil voice question → spoken Tamil answer
- [ ] Demo page shows agent steps
- [ ] All sample data visibly labelled

---

## V1 decisions (override the sections above)
- Intake/parsing LLM = Gemini (`GEMINI_API_KEY`).
- Sarvam AI = Tamil voice (STT + TTS).
- Razorpay = TEST mode only (`rzp_test_` keys).
- Every external service has a MOCK fallback; a missing key = demo mode, never a crash.
- Never print or commit key values.
- Backend: FastAPI in `/backend`. Frontend: React + Vite + Tailwind + shadcn/ui in `/frontend`.

## V1.1 plan — live services (overrides the sections above)
- **SMS**: textbee (Android phone gateway) is the main SMS path (`SMS_PROVIDER=textbee`); Twilio / Fast2SMS are alternatives; mock outbox is the fallback. Status is only `sent` when the provider confirmed it.
- **Call-back**: SMS `CALL` → Twilio voice calls her back, records her question, Sarvam STT → AVAL → Sarvam TTS (≤ ~20 s). Needs `PUBLIC_BACKEND_URL` (ngrok) and verified caller IDs on trial.
- **Voice**: Sarvam STT + TTS (backend only).
- **n8n**: `/api/demo/chat` goes through `N8N_ORCHESTRATOR_URL` when set, else the backend orchestrator. Circle/trip events post to `N8N_WEBHOOK_URL` in the background.
- **Supabase**: `store.py` uses Supabase when reachable, otherwise in-memory + `/data` JSON. Schema in `supabase/migrations/001_init.sql` + `002_api_grants.sql`; `python -m backend.db_migrate` → `supabase_verify` → `seed_supabase` (sample rows, labelled `source: sample`).
- **Maps**: MapLibre + MapTiler (public `VITE_MAPTILER_KEY` only); illustrated fallback when no key or the style fails to load.
- **Secrets**: service key, Razorpay secret, Twilio token, textbee key, Gemini, Sarvam stay backend-only. Vite exposes only MapTiler key + Supabase URL/anon key. Razorpay refuses `rzp_live_` keys.
- **Launch plan (after demo)**: DLT registration + MSG91 or Exotel for production SMS/voice in India.
- **Real bus data**: `data/gtfs_bus.json` = real MTC routes + timetables for the demo pair, from ChennaiGTFS (ODbL/PDDL, credit UngalSoththu). Rebuild: `python -m backend.seed.import_gtfs <ChennaiGTFS>/data/mtc`. Rows are one-way with exact departures; labelled `source: "ChennaiGTFS (MTC)"`. Free only on ordinary (white-board) buses, so every row carries `free_note`. The old sample 21G is removed. Safe places stay sample.
- **Port**: backend runs on **8000**; ngrok must match (`ngrok http 8000`) and `PUBLIC_BACKEND_URL` = that tunnel. 8001 is only a Windows fallback (then `ngrok http 8001`).
- Setup steps: `docs/LIVE_SETUP.md`.

## V2 backlog (text only — do not build until V1 is done)
- **Companion characters**: she picks one companion per mode (route guide, shop guide, stop guide). The SOS screen is never decorated. Original or CC0 art only (Kenney.nl, Quaternius). No copyrighted characters.
- **3D map**: MapLibre `fill-extrusion` buildings + tilted camera (look like the Apple Maps 3D city view). The companion moves along the route as a 2.5D sprite (flat animated image), not a 3D model, so it runs on slow-3G phones.
- **"Open in maps" links**: Apple Maps unified map URLs (https://developer.apple.com/documentation/mapkit/unified-map-urls) and Google Maps URLs for directions to the stop / safe place. Link only; no location sent to us.
- **Safety rules for companions**: safety info is always shown as text. The companion never changes safety info. The circle never sees the companion. No profiling.
- **Stealth mode**: hides the companion and shows a neutral screen.
- **Open data**: OSM Overpass (lit streets, toilets, shops), Nominatim (coordinates → nearby landmark), OpenRouteService or OSRM (walking routes), Open-Meteo (rain alerts; no key).
- **More real transit**: ChennaiGTFS CMRL metro + suburban rail feeds (same repo) to replace sample metro / train.
- **API Setu**: DigiLocker verification of trusted contacts (needs API consumer registration + consent framework).
- **MCP is build-time only**: Figma / Paper for design handoff, docs MCP for MapTiler / MapLibre. Not used at runtime.
