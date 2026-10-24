# SafePath V1 — Frontend

React 19 + Vite + Tailwind CSS v4 + shadcn/ui. 17 screens from `design/screens_png`, all data from the backend API.

```bash
npm install
npm run dev     # http://localhost:5173, proxies /api to http://localhost:8000
npm run build
```

- Design tokens: `src/index.css` (`@theme`). Fonts: Noto Sans / Noto Sans Tamil / Noto Serif Tamil (OFL), bundled via `@fontsource`.
- AVAL: `src/components/Aval.jsx` renders `src/aval/art.js` (copied from `design/aval/code`), states idle / wave / listening / thinking / talking / alert.
- Travel scenes: animated SVGs imported from `design/aval/travel_animated`.
- Tamil/English toggle: `src/lib/i18n.jsx`.
- Confirmation before paying or messaging: `src/components/Confirm.jsx`, `src/components/StartTrip.jsx`. SOS never asks.
- Maps are illustrations in V1 (MapLibre + real tiles later). Every screen shows "Sample data for demo".
