# Agent Quickstart — TrafficScope

Read this first before exploring the repo. It maps the codebase to common tasks so you can jump straight to the right files.

## What This Project Is

**TrafficScope 1.1** is a web app for rideshare-style route planning in Austin, TX. Users enter origin/destination, compare three objective-based route alternatives, adjust scenario sliders (time, weather, congestion, demand), view heatmaps and segment stats, and see an illustrative price estimate.

All demand, traffic, weather, and fare values are **simulated planning estimates** — not official Uber/Lyft fares or live traffic data (except Google route geometry when configured).

**Stack:** React 19 + TypeScript (Vite) frontend, FastAPI (Python) backend. Everything runnable lives under `TrafficSImulation/`.

---

## Repo Layout

```
CS-4398/
├── AGENTS.md                 # Repo conventions (style, tests, commits) — read this too
├── docs/
│   ├── agent-quickstart.md   # ← you are here
│   ├── srs-context/          # SRS requirement breakdown by MVC layer (deep dives)
│   └── jordan-context-files/ # Feature-specific integration notes (map widget, Google embed)
└── TrafficSImulation/        # ← all app code and commands run from here
    ├── main.py               # FastAPI entry, HTTP routes, static SPA hosting
    ├── start_demo.bat        # Windows one-click demo (build + serve)
    ├── .env.example          # Copy to .env for GOOGLE_MAPS_API_KEY
    ├── src/                  # React frontend
    ├── app/                  # Python domain modules
    └── tests/                # pytest backend/API tests
```

---

## Run & Test (from `TrafficSImulation/`)

| Goal | Command |
|------|---------|
| Install frontend deps | `npm install` |
| Dev (hot reload) | Terminal 1: `python main.py` · Terminal 2: `npm run dev` → http://127.0.0.1:5173 |
| Production build + serve | `npm run build` then `python main.py` → http://127.0.0.1:8000 |
| Windows demo shortcut | `start_demo.bat` |
| Backend tests | `python -m pytest` |
| Frontend tests | `npm test` |
| Type-check + bundle | `npm run build` |
| OpenAPI docs | http://127.0.0.1:8000/docs |
| Health check | `GET /api/health` |

Vite proxies `/api/*` to FastAPI on port 8000 during dev (`vite.config.ts`).

---

## Architecture at a Glance

```
React (src/)                    FastAPI (main.py)              Python domain (app/)
─────────────────               ─────────────────              ────────────────────
RoutePlanner ──┐
RouteOptions ──┼── useRoutePlan ── POST /api/plan ──► plan_route() in api/routes.py
TrafficMap ────┤                                              ├── map/service.py (Places + Routes)
Analysis ──────┘                                              ├── simulation/traffic.py (BPR)
Header / Toast                                                ├── pricing/model.py
                                                              ├── weather/service.py
                                                              ├── heatmap/builder.py
                                                              └── config/__init__.py (coefficients)
```

**Core request flow:**

1. `useRoutePlan` POSTs `{ origin, destination, mode, hour, weather, congestion, demand }` to `/api/plan`.
2. `plan_route()` geocodes via Google Places, fetches up to 3 routes via Google Routes, runs BPR traffic simulation, applies weather/time multipliers, estimates price, builds heatmap, scores routes, returns JSON.
3. Frontend renders route cards, map embed + SVG polylines, and analysis panel.

---

## Task → File Map

Use this table to find code without searching the whole repo.

| I need to change… | Start here |
|-------------------|------------|
| Page layout / composition | `src/App.tsx` |
| Route form, geolocation button | `src/components/RoutePlanner.tsx` |
| Three route cards, selection | `src/components/RouteOptions.tsx` |
| Map iframe, zoom, "View all" | `src/components/TrafficMap.tsx` |
| SVG route polylines on map | `src/components/RouteOverlay.tsx` |
| Scenario sliders, segment table, pricing breakdown | `src/components/Analysis.tsx` |
| Realtime vs simulated toggle | `src/components/Header.tsx` |
| Toast notifications | `src/components/Toast.tsx` |
| Fetch/state/debounce for planning | `src/hooks/useRoutePlan.ts` |
| Default scenario values | `src/constants/scenario.ts` |
| Lat/lng → SVG projection | `src/utils/mapProjection.ts` |
| Frontend API types | `src/types.ts` |
| Global styles | `src/styles.css` |
| HTTP endpoints, static hosting | `main.py` |
| Plan orchestration, scoring, response assembly | `app/api/routes.py` |
| Request/response Pydantic models | `app/api/models.py` |
| Simulation coefficients, Google URLs, API key | `app/config/__init__.py` |
| Geocoding + route building entry point | `app/map/service.py` |
| Google Places search | `app/map/google_places.py` |
| Google Routes compute | `app/map/google_routes.py` |
| Map embed URL generation | `app/map/google_embed.py` |
| Startup Google API probe | `app/map/google_startup_check.py` |
| Encoded polyline decode | `app/map/polyline.py` |
| Local Austin fallback geocoder | `app/map/local.py` |
| BPR link timing, segments, time-of-day | `app/simulation/traffic.py` |
| Price estimate + factor breakdown | `app/pricing/model.py` |
| Weather severity multipliers | `app/weather/service.py` |
| Heatmap grid + overlay cells | `app/heatmap/builder.py`, `app/heatmap/grid.py` |

---

## API Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| `GET` | `/api/health` | Service status + Google Maps probe result |
| `POST` | `/api/plan` | Plan routes (main app endpoint) |
| `POST` | `/api/map/embed` | Build Google Maps embed URL for a center/zoom |

### `POST /api/plan` body

```json
{
  "origin": "Downtown Austin",
  "destination": "Austin Airport",
  "mode": "simulated",
  "hour": 17,
  "weather": 1,
  "congestion": 56,
  "demand": 68
}
```

- `mode`: `"simulated"` (user controls scenario sliders) or `"realtime"` (traffic-aware Google routing; sliders reset to baseline).
- Validation: origin/destination 1–120 chars; hour 0–23; weather 0–3; congestion/demand 0–100. Out-of-range → HTTP 422.
- Business errors (bad locations, missing API key) → HTTP 400 with `detail` string.

### Shared types (keep in sync)

| Python | TypeScript |
|--------|------------|
| `app/api/models.py` — `PlanRequest`, `RouteOption`, `RoadSegment` | `src/types.ts` — `PlanResult`, `RouteOption`, `Segment`, `Scenario` |

When changing response shape, update **both** files and relevant tests.

---

## Modes Explained

| Mode | Behavior |
|------|----------|
| `simulated` | Google provides route geometry/distances; congestion, demand, weather, and prices come from user sliders. |
| `realtime` | Google traffic-aware durations when available; scenario sliders are overridden to baseline values server-side. |

Route planning **requires** a valid `GOOGLE_MAPS_API_KEY` (Places + Routes APIs). Without it, `/api/plan` returns HTTP 400.

---

## Configuration & Environment

- **Coefficients** (BPR, pricing, scoring weights, weather multipliers): `app/config/__init__.py` — single source of truth; do not scatter magic numbers elsewhere.
- **Google API key:** copy `TrafficSImulation/.env.example` → `.env`, set `GOOGLE_MAPS_API_KEY=...`. Loaded automatically on startup.
- **Required Google APIs:** Places API (New) `places:searchText`, Routes API `directions/v2:computeRoutes`.

---

## Tests

| File | Covers |
|------|--------|
| `tests/test_api.py` | Health, plan endpoint shape, 422 validation, map embed |
| `tests/test_backend.py` | BPR math, pricing reproduction, ETA monotonicity, Google client parsing, polyline/map embed helpers |
| `tests/test_google_startup.py` | Live Google probe (needs real API key) |
| `tests/google_mocks.py` | Shared mocks for Google Places/Routes in unit tests |
| `src/App.test.tsx` | Frontend behavior (Testing Library) |
| `src/utils/mapProjection.test.ts` | Projection math |

Run `python -m pytest` and `npm test` after backend or frontend changes respectively. Run `npm run build` when touching TypeScript.

---

## Coding Conventions (short)

- Python: 4 spaces, `snake_case` modules/functions, type hints via Pydantic/dataclasses.
- TypeScript: 2 spaces, `PascalCase` components/types, `camelCase` variables, strict typing.
- React components live in `src/components/`; shared state/fetch logic in `src/hooks/`.
- Backend domain logic stays in `app/<component>/`, not in `main.py` (HTTP layer only).
- Commit messages: short imperative ("Add weather validation", "Fix map zoom").

Full details: repo-root `AGENTS.md`.

---

## Deeper Documentation

| Doc | When to read |
|-----|--------------|
| `TrafficSImulation/README.md` | User-facing run instructions, Google setup |
| `docs/srs-context/README.md` | SRS requirement index, MVC mapping, FR IDs |
| `docs/srs-context/model/*.md` | Simulation, pricing, weather, heatmap, config details |
| `docs/srs-context/view/*.md` | UI panels, controls, results display |
| `docs/srs-context/controller/*.md` | API contracts, validation, orchestration |
| `docs/jordan-context-files/map-widget-and-routes-integration.md` | Map iframe + SVG overlay architecture |
| `docs/jordan-context-files/googleMapsEmbeddedWidget.md` | Google embed widget specifics |

Use **this quickstart** for orientation and file lookup; use **srs-context** when implementing or verifying a specific requirement.

---

## Common Pitfalls

1. **Run commands from `TrafficSImulation/`**, not the repo root.
2. **Build before `python main.py` in production mode** — FastAPI serves `dist/`; missing build prints a warning and UI won't load.
3. **Google key is mandatory** for route planning; local geocoder (`app/map/local.py`) exists as fallback reference but `build_route_options` uses Google.
4. **Don't duplicate coefficients** — change `app/config/__init__.py` only.
5. **Frontend debounces scenario changes** (180 ms in `useRoutePlan`) but not origin/destination — those require form submit.
6. **Folder name is `TrafficSImulation`** (capital S, lowercase im) — not "Simulation".

---

## Quick Debug Checklist

1. `GET /api/health` — is `google_maps.ok` true?
2. Check terminal output on `python main.py` startup for Google probe messages.
3. Browser devtools → Network tab → `/api/plan` response body on failure.
4. Run `python -m pytest tests/test_api.py -v` for fast API regression signal.
