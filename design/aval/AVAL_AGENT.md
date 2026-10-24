# AVAL (அவள்) — the SafePath agent

AVAL means "she" in Tamil. She is SafePath's AI travel companion: a Chennai woman with a braid and jasmine, gold jimikki earrings, plum kurta, pink dupatta and a teal phone. Original character drawn for SafePath.

This folder has everything needed to show her and make her work.

## 1. Assets

| Folder | What | Use in app |
|---|---|---|
| `svg/` | front, three-quarter, back, wave, 6 faces, app icon | sharp art at any size |
| `png/` | same as PNG (transparent) | slides, quick use |
| `poses/` | cheer, guide, booking (ticket), wave, turn left/right, back, front | guidance moments |
| `abilities/` | shops, connect, free bus, pay, live trip, SOS + `aval_combined.png` poster | feature cards, onboarding |
| `travel/` | bus, train, metro, auto scenes (static) | headers |
| `travel_animated/` | same scenes as **animated SVG** (wheels spin, road + city move, AVAL waves) + GIFs | page headers in the app (use the SVGs) |
| `pixel/` | pixel-art versions | loaders, badges |
| `aval_character_sheet.html` | open in a browser: live AVAL with all states | reference |
| `code/` | `draw_v2.js`, `poses.js`, `features.js` — functions that return AVAL as SVG strings | render her live in React |

### Rendering her live (recommended for the agent screen)
`code/draw_v2.js` exposes `front(mood, state)`, `head(mood)`, `faceOnly(mood)`, `back()`, `threeQuarter()`.
`poses.js` adds `cheer()`, `guide()`, `booking()`, `sideLeft()`, `sideRight()`, `busScene()`, `trainScene()`, `metroScene()`, `autoScene()`.
`features.js` adds `featShops()`, `featConnect()`, `featBus()`, `featPay()`, `featTrip()`, `featSOS()`, `combined()`.
Each returns an SVG string. In React: wrap them in a small `<Aval mood state />` component (`dangerouslySetInnerHTML` from these trusted local strings is fine), or port the shapes to JSX later.

Animation CSS (copy from `aval_character_sheet.html`):
`.bob` idle float · `.eyes` blink · `.braid` sway · `.wave .arm-r` waving · `.talking .mouth-talk` · `.listening .ring` · `.alert .halo` pulse. Respect `prefers-reduced-motion`.

## 2. States (what the user sees)

| State | Mood | When |
|---|---|---|
| `idle` | smile | AVAL screen open, waiting |
| `wave` | happy | Home greeting, onboarding |
| `listening` | smile + teal rings | mic held, Sarvam speech-to-text running |
| `thinking` | thinking + dots | agents working (route, places, safety) |
| `talking` | talking mouth | reply being spoken (Sarvam text-to-speech) |
| `alert` | serious + pink halo | missed check-in, SOS — no playful motion |
| pose `guide` | — | "switch here", "turn left", next step |
| pose `cheer` | — | reached safely, payment success |
| pose `booking` | — | ticket ready |

## 3. How AVAL works (agent behaviour)

```
User (voice/text/SMS)
   → Intake: Gemini parses text → JSON {intent, from, to, time, with_child, lang}
   → Orchestrator picks agents:
        Route agent   — trips from data (bus/metro/train/auto), fares, free-bus flag
        Safety agent  — scores routes: people around, shops open now, lighting, women-run places
        Places agent  — places near a point / along a route, open now, reviews
        Circle agent  — trusted contacts, Journey Watch (START / check-in / alert), SOS
        Pay agent     — Razorpay (TEST mode) → ticket
   → Reply: short card + one action, in the user's language; spoken via Sarvam if voice
   → "What AVAL did" log shown on screen
```

### Intents (V1)
`plan_trip` · `safe_route_home` · `places_open_now` · `place_details` · `free_bus_now` · `book_ticket` · `share_trip` · `start_trip` / `reached` · `sos` · `help`.

### Rules (guardrails)
1. **The LLM never invents** a bus, fare, place or review. It only parses and phrases; data comes from files/APIs through code.
2. Strip phone numbers and names before any LLM call.
3. Validate LLM JSON; if invalid → fallback reply "Sorry, tell me the place name. Eg: Nungambakkam bus".
4. **Confirm before** paying or messaging anyone ("Send this to Amma? Yes / No").
5. **SOS skips everything**: alert circle, show 181 / 100, share location until stopped.
6. Location shared only during an active trip or SOS. Crowd data is anonymous areas only.
7. Never say an alert was sent unless it actually was.
8. Reply in Tamil if the user spoke Tamil; short sentences; one card + one button.

### Example
User (voice, Tamil): "நுங்கம்பாக்கம், 8 மணி, பொண்ணோட"
→ intent `plan_trip`, to Nungambakkam, 08:00, with_child true, lang ta
→ Route: free bus 21G, next 8:05 · Safety: busy stops, SHG kiosk to wait · Circle: Amma ready
→ Reply card: "21G இலவசம் · 8:05 · லக்ஷ்மி கடையில் காத்திருங்கள்" + [Start trip]
→ AVAL state: thinking → talking → idle.
