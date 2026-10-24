# SafePath — Frontend Spec (V1 designs)

This folder is the design handoff for the SafePath app. **It is a reference, not code to ship.**
Build the real app in React + Tailwind + shadcn/ui and match these screens.

- `screens_png/` — picture of every screen (390 × 844, phone). Look at these first.
- `screens_html/` — the same screens as static HTML/CSS. Open `Login.html` in a browser and click through. Copy exact colours, spacing and copy from here.
- `assets/` — AVAL character art (PNG) and animated travel scenes (GIF). Full asset pack (SVG, all poses, pixel art) is in `AVAL_asset_pack.zip`.

All data on screens is **sample Chennai data** and must stay labelled "Sample data for demo" until real data is connected.

---

## Design system

| Token | Value | Use |
|---|---|---|
| Plum | `#5B1F96` | primary buttons, active tab |
| Pink | `#FF4F8B` | free bus, accents, user location |
| Marigold | `#FFB52E` | highlights, "people around" glow |
| Teal | `#0FA596` (dark text `#0B7F74`) | safe, success, open now |
| Mint | `#2EE6A8` | live dot, navigation green line |
| Cream | `#FFF7EC` | app background |
| Ink | `#24132F` | text |
| Muted | `#6A5878` | secondary text |
| Night map | `#120F19` / `#14111B` | dark map screens |
| SOS red | `#E3263F` | SOS only |

Fonts (Google Fonts, OFL): **Noto Sans** (UI), **Noto Sans Tamil** (Tamil text), **Noto Serif Tamil** ExtraBold (Tamil logo/headings only).
Rules: tap targets ≥ 48 px, body ≥ 13 px, cards radius 16–22 px, every screen has Tamil + English, icons always with a text label, SOS reachable from every trip screen.

AVAL (அவள்) is the AI agent. Use her face in the nav, her poses for guidance (wave = greeting, guide = next step, cheer = success, alert face = SOS). Never cute animations on SOS.

---

## Screens (17) and how they link

### Flow 1 — Book a trip
| # | File | Screen | Key parts | Goes to |
|---|---|---|---|---|
| 1 | Login | Welcome & login | AVAL hero, language தமிழ்/English, phone + OTP, privacy note | Home |
| 2 | Home | Home | greeting, "Where to?" + mic, quick trips, live free-bus strip, 4 animated mode tiles, **Safe way home** card, circle row, floating SOS, bottom nav (Home · Route · AVAL · Circle · Tickets) | all |
| 3 | Main | AVAL agent | chat, voice reply, route card, "What AVAL did" steps, quick asks, big mic | Booking / LiveTrip |
| 4 | Booking | Choose your ride | from/to + swap, "with child" toggle, Safest/Cheapest/Fastest tabs, route cards, AVAL tip, Start free trip | Payment / LiveTrip |
| 5 | Payment | Payment | trip summary (free bus ₹0 + metro ₹30), UPI apps, card, Razorpay note | Ticket |
| 6 | Ticket | Ticket | cheering AVAL, QR ticket, platform, women's coach, Share with Amma, Start trip | Connect / LiveTrip |

### Flow 2 — Travel safely
| # | File | Screen | Key parts |
|---|---|---|---|
| 7 | Bus | Free bus tracker | animated bus header, stop picker, Free-only filter, arrivals with minutes, safe waiting spot |
| 8 | Metro | Metro | animated header, next-train countdown, women's coach, station timeline, best exit, fare |
| 9 | Train | Local train | animated header, **ladies coach position diagram**, next trains + delays, last-train reminder |
| 10 | Nearby | **Safe way home (night)** — the core idea | dark map; amber glow = where people are (anonymous areas); green route = safest; pins = shops open now vs closed; circle members shown on map; route comparison: people around / shops open at night / your people; Walk main road, Ask Kavya to meet |
| 11 | Connect | Your circle | members with live status, call/message, pending invite, max 5, "how sharing works" |
| 12 | LiveTrip | Live walk | AR-style road view with **green navigation line + arrows**, next open shop, who's watching, AVAL guiding, I've reached, SOS |
| 13 | SOS | SOS | hold-2-seconds button, what will happen, 181 / 100, nearest help, I'm safe now |

### Flow 3 — Find a place
| # | File | Screen | Key parts |
|---|---|---|---|
| 14 | Explore | Explore map | light map, **picture pins** (place thumbnails, OPEN badge, +N clusters), "What are you looking for?" chips (Open at night, Women-run, Pharmacy, Tea & food, Bus & metro, Police & help) |
| 15 | Place | Place, reviews & safety | photo header, rating + reviews count, Open now · closes, **Safety at night** card, How to reach / Call / Share, "What women say" reviews |
| 16 | Reach | How to reach | Transit/Walk/Auto tabs, route cards with legs (Walk › bus 70 › Walk), price, **safety bar**, SAFEST / FASTEST tags, AVAL explanation |
| 17 | Steps | Route & steps | map with coloured legs, step timeline with times, **Start navigation** → screen 12 |

---

## Core product idea (keep this central)
At night, SafePath picks the route where **people are around**, **shops are still open**, and **your own trusted people are nearby**, then guides you along it with a green line while your circle watches.

## Privacy rules shown in UI
- Crowd = anonymous areas, never individuals.
- Circle members see you only during a trip or SOS; both sides accept; max 5.
- Confirm before paying or messaging; SOS needs no confirmation.

## Known V1 gaps (to improve later)
- Maps are drawn illustrations → replace with MapLibre / mapcn + real tiles.
- Place photos are illustrations → real photos from a places API.
- All transit, crowd and review data is sample.
