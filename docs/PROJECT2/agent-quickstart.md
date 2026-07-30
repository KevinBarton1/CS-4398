# Agent Quickstart — TrafficScope PROJECT2

Read [README.md](README.md) first for the locked contracts, then this file for orientation. This
quickstart describes the **target** repository. Where the current repository differs, the difference is
listed in [migration-from-current-implementation.md](migration-from-current-implementation.md).

## What You Are Building

TrafficScope is a browser application for rideshare-style trip planning in Austin, Texas. The user
enters an origin and a destination, picks Simulated or Real-Time mode, and receives route alternatives
with traffic-aware ETAs, per-segment road statistics, a traffic-colored Google map, and an illustrative
fare estimate.

Two mode names, three scenario variables, four endpoints, one map. That is the whole product surface.

| Layer | Location | Technology |
|-------|----------|-----------|
| View | `TrafficSImulation/src/` | React 19, TypeScript, Vite, `@vis.gl/react-google-maps` |
| Controller | `TrafficSImulation/main.py`, `TrafficSImulation/app/api/` | FastAPI on Uvicorn |
| Model | `TrafficSImulation/app/map/`, `simulation/`, `pricing/`, `weather/`, `heatmap/`, `config/` | Python domain packages |

Every fare, congestion level, and weather state is a simulated planning estimate. Route geometry,
distance, and traffic come from Google.

---

## Repository Layout

```
CS-4398/
├── AGENTS.md                          # Repo conventions: style, tests, commits. Read this too
├── docs/
│   ├── PROJECT2/                      # ← the rewrite specification, you are here
│   │   ├── README.md                  # Locked contracts. Authoritative
│   │   ├── agent-quickstart.md
│   │   ├── migration-from-current-implementation.md
│   │   └── srs-context/
│   │       ├── README.md              # Context index and MVC mapping
│   │       ├── requirements/          # FR and NFR catalogs, traceability
│   │       ├── architecture/          # Overview, class diagram, state diagrams
│   │       ├── model/                 # Domain contexts
│   │       ├── controller/            # API and orchestration contexts
│   │       └── view/                  # UI contexts
│   ├── agent-quickstart.md            # Legacy. Historical reference only
│   ├── srs-context/                   # Legacy. Historical reference only
│   └── jordan-context-files/          # Legacy. Historical reference only
└── TrafficSImulation/                 # All app code; run every command from here
    ├── main.py
    ├── .env.example
    ├── src/
    ├── app/
    └── tests/
```

The folder name is `TrafficSImulation` with a capital S and a lowercase i-m. It is not "Simulation".

---

## Run And Test

Run every command from `TrafficSImulation/`.

| Goal | Command |
|------|---------|
| Install frontend dependencies | `npm install` |
| Development, two terminals | `python main.py` and `npm run dev`, then open `http://127.0.0.1:5173` |
| Production build and serve | `npm run build`, then `python main.py`, then open `http://127.0.0.1:8000` |
| Backend and API tests | `python -m pytest` |
| Frontend tests | `npm test` |
| Type-check and bundle | `npm run build` |
| OpenAPI documentation | `http://127.0.0.1:8000/docs` |
| Health check | `GET /api/health` |

Vite proxies `/api/*` to FastAPI on port 8000 during development. In production FastAPI serves the
built single-page application from `dist/`.

Before submitting a change that touches either stack, run `python -m pytest`, `npm test`, and
`npm run build`.

---

## Architecture At A Glance

```
View (src/)                        Controller (app/api/)              Model (app/)
──────────────────                 ─────────────────────              ──────────────
RoutePlannerForm ─┐
RouteOptionList ──┤                                                   map/places.py
AnalysisPanel ────┼─ useRoutePlan ─ POST /api/plan ─► planning.py ────┤ map/routing.py
ScenarioControls ─┤                                  mode_policy.py   │ map/bounds.py
AppHeader ────────┘                                  errors.py        │ simulation/traffic.py
                                                                      │ simulation/segments.py
MapConfigProvider ─ useMapConfig ─ GET /api/map/config                │ simulation/scoring.py
  └─ RouteMap                                                         │ pricing/model.py
       ├─ RoutePolylineLayer                                          │ weather/service.py
       └─ MapBoundsController                                         └ config/__init__.py
```

**Plan request flow**

1. `useRoutePlan` posts `{ origin, destination, mode, hour, weather, congestion }` to `/api/plan`.
2. `app/api/routes.py` validates the body against `PlanRequest`.
3. `PlanningService` resolves the `ModePolicy`, resolves both places through Google Places, computes
   alternatives through Google Routes, applies weather, builds segments, estimates fares, scores
   routes, and computes bounds.
4. The response returns normalized routes with polylines, traffic intervals, segments, fares, and
   bounds.
5. The View renders route cards, the analysis panel, and traffic-colored polylines on one Google map.

**Map configuration flow**

`MapConfigProvider` fetches `GET /api/map/config`, receives the referrer-restricted browser
credential, and loads the Maps JavaScript API. This is independent of planning, so a map failure and a
plan failure degrade separately.

---

## Task To File Map

| I need to change… | Start here |
|-------------------|------------|
| Page layout and composition | `src/App.tsx` |
| Trip form, geolocation assist | `src/components/RoutePlannerForm.tsx` |
| Route cards and selection | `src/components/RouteOptionList.tsx` |
| The map surface | `src/components/RouteMap.tsx` |
| Polyline drawing and traffic colors | `src/components/RoutePolylineLayer.tsx`, `src/utils/trafficSegmentColor.ts` |
| Camera and `fitBounds` behavior | `src/components/MapBoundsController.tsx` |
| Browser map credential and `APIProvider` | `src/components/MapConfigProvider.tsx`, `src/hooks/useMapConfig.ts` |
| Scenario sliders and reset | `src/components/ScenarioControls.tsx`, `src/constants/scenario.ts` |
| Fare display and factor breakdown | `src/components/PriceSummary.tsx` |
| Segment statistics table | `src/components/SegmentTable.tsx` |
| Loading, empty, and error presentation | `src/components/StatusBanner.tsx`, `src/components/Toast.tsx` |
| Mode switch | `src/components/AppHeader.tsx` |
| Request lifecycle, debounce, selection | `src/hooks/useRoutePlan.ts` |
| Fetch, abort, error-envelope parsing | `src/api/client.ts` |
| Frontend API types | `src/types.ts` |
| Global styles | `src/styles.css` |
| Application assembly and static hosting | `main.py` |
| Endpoint declarations | `app/api/routes.py` |
| Request and response schemas | `app/api/models.py` |
| Plan orchestration | `app/api/planning.py` |
| Mode-dependent behavior | `app/api/mode_policy.py` |
| Error codes and handlers | `app/api/errors.py` |
| Place resolution | `app/map/places.py` |
| Route computation | `app/map/routing.py` |
| Polyline decoding | `app/map/polyline.py` |
| Bounds math | `app/map/bounds.py` |
| Google reachability probe | `app/map/health.py` |
| BPR timing and time-of-day factor | `app/simulation/traffic.py` |
| Segment derivation | `app/simulation/segments.py` |
| Route ranking | `app/simulation/scoring.py` |
| Fare estimation | `app/pricing/model.py` |
| Weather multipliers | `app/weather/service.py` |
| Coefficients, URLs, timeouts, credentials | `app/config/__init__.py` |
| Congestion heatmap, phase P3 | `app/heatmap/builder.py`, `app/heatmap/grid.py` |

---

## API Summary

| Method | Path | Phase | Purpose |
|--------|------|-------|---------|
| `POST` | `/api/plan` | P1 | Plan route alternatives |
| `GET` | `/api/health` | P1 | Service status and Google reachability |
| `GET` | `/api/map/config` | P1 | Browser map configuration |
| `POST` | `/api/heatmap` | P3 | Congestion heatmap cells, provisional |

`POST /api/plan` request body:

```json
{
  "origin": "Downtown Austin",
  "destination": "Austin Airport",
  "mode": "simulated",
  "hour": 17,
  "weather": 1,
  "congestion": 56
}
```

Validation: origin and destination 1 to 120 characters; `hour` 0 to 23; `weather` 0 to 3;
`congestion` 0 to 100. Out-of-range values return `422` with code `validation_error`.

Full schemas are in [srs-context/controller/api-contracts.md](srs-context/controller/api-contracts.md).

### Error codes

| Code | Status | Meaning |
|------|--------|---------|
| `validation_error` | 422 | The body failed schema validation |
| `invalid_location` | 400 | A location could not be resolved |
| `same_origin_destination` | 400 | Origin and destination are the same place |
| `no_route_found` | 400 | No driving alternatives exist |
| `maps_not_configured` | 503 | The required Google credential is absent |
| `upstream_unavailable` | 502 | Google returned an error status |
| `upstream_timeout` | 504 | Google exceeded the request timeout |

### Contract synchronization

| Python | TypeScript |
|--------|-----------|
| `app/api/models.py` — `PlanRequest`, `PlanResponse`, `RouteOption`, `RoadSegment`, `PriceFactors`, `MapConfigResponse` | `src/types.ts` — `PlanResult`, `RouteOption`, `RoadSegment`, `PriceFactors`, `MapConfig`, `ApiError` |

Change both files and the contract test in the same commit.

---

## Modes

| Mode | Wire value | Label | Alternatives | Scenario | Departure | Polyline color |
|------|-----------|-------|--------------|----------|-----------|----------------|
| Simulated | `simulated` | `Simulated` | Up to 3 | Applied | Next occurrence of `scenario.hour` | Google speed colors, tinted by congestion and weather |
| Real-Time | `realtime` | `Real-Time` | Exactly 1 | Ignored | Now | Google speed colors, untinted |

The response tells you which happened: read `mode` and `scenario_applied`, never the request intent.

---

## Configuration And Environment

Copy `TrafficSImulation/.env.example` to `.env` and set:

| Variable | Reaches the browser | Google restriction |
|----------|--------------------|--------------------|
| `GOOGLE_MAPS_API_KEY` | Never | Places API (New) and Routes API |
| `GOOGLE_MAPS_BROWSER_API_KEY` | Yes, via `GET /api/map/config` | Maps JavaScript API only, HTTP referrer restricted |
| `GOOGLE_MAPS_MAP_ID` | Yes, as `map_id`. Optional | Not a credential |

Required Google APIs: Places API (New) `places:searchText`, Routes API
`directions/v2:computeRoutes`, and the Maps JavaScript API.

All coefficients live in `app/config/__init__.py`. Do not scatter magic numbers.

---

## Testing

| File | Covers |
|------|--------|
| `tests/test_api.py` | Endpoint status codes, response shapes, every error code |
| `tests/test_contracts.py` | The exact response field set |
| `tests/test_planning.py` | Orchestration and the adjusted-ETA fallback chain |
| `tests/test_mode_policy.py` | Mode policy behavior table |
| `tests/test_simulation.py` | BPR, time-of-day factor, segment derivation |
| `tests/test_pricing.py` | Fare formula, factor reproduction, minimum fare |
| `tests/test_weather.py` | Severity to multipliers |
| `tests/test_scoring.py` | Normalization and recommendation |
| `tests/test_google_places.py`, `tests/test_google_routes.py` | Gateway payloads and error translation, mocked transports |
| `tests/test_polyline.py`, `tests/test_bounds.py` | Geometry helpers |
| `src/App.test.tsx` | Plan, select, and mode-switch behavior |
| `src/hooks/useRoutePlan.test.ts` | Debounce, abort, selection reconciliation |
| `src/components/*.test.tsx` | Map layers, banners, price summary, segment table |
| `src/utils/trafficSegmentColor.test.ts` | Color mapping and tinting |

The default suite makes no live Google calls. Any live-credential test is opt-in and excluded from the
default run.

---

## Non-Negotiables

1. One map rendering path. The Google Maps JavaScript API, for both modes, always.
2. The server credential never reaches the browser. The browser gets a separate referrer-restricted key.
3. No silent fallback data. A missing credential or an unreachable upstream is an explicit error state.
4. Three scenario variables: `hour`, `weather`, `congestion`. No others.
5. Only `app/api/mode_policy.py` inspects the mode string.
6. Only `app/config/__init__.py` holds coefficients and reads the environment.
7. The Model never imports the Controller, FastAPI, or any HTTP type.
8. Heatmaps are phase P3. Do not describe them as existing behavior.

---

## Common Pitfalls

1. Run commands from `TrafficSImulation/`, not the repository root.
2. Build the frontend before running `python main.py` in production mode.
3. A working Google credential is mandatory for planning. There is no offline path.
4. Do not duplicate coefficients; change `app/config/__init__.py` only.
5. Scenario changes are debounced; origin and destination changes require an explicit submit.
6. Adding a response field means touching `app/api/models.py`, `src/types.ts`, the contract test, and
   [srs-context/controller/api-contracts.md](srs-context/controller/api-contracts.md).

---

## Debug Checklist

1. `GET /api/health` — is `google_maps.ok` true?
2. Check the startup log for the Google probe result.
3. Browser devtools, Network tab — inspect the `/api/plan` response `code` and `detail`.
4. Map blank but the rest of the page working? Inspect `GET /api/map/config` and the browser key's
   referrer restrictions.
5. `python -m pytest tests/test_api.py -v` for the fastest API regression signal.

---

## Deeper Documentation

| Document | When to read |
|----------|--------------|
| [README.md](README.md) | Before anything else. Locked contracts |
| [srs-context/README.md](srs-context/README.md) | Context index and MVC mapping |
| [srs-context/requirements/functional-requirements.md](srs-context/requirements/functional-requirements.md) | Implementing or verifying a behavior |
| [srs-context/requirements/traceability.md](srs-context/requirements/traceability.md) | Finding the owner, phase, and test for a requirement |
| [srs-context/architecture/architecture-overview.md](srs-context/architecture/architecture-overview.md) | Boundaries, dependency rules, credentials |
| [srs-context/architecture/class-diagram.md](srs-context/architecture/class-diagram.md) | Class names and responsibilities |
| [srs-context/architecture/state-diagrams.md](srs-context/architecture/state-diagrams.md) | Lifecycles and state transitions |
| [migration-from-current-implementation.md](migration-from-current-implementation.md) | Understanding why something was removed |
| Repo-root `AGENTS.md` | Style, test, and commit conventions |
