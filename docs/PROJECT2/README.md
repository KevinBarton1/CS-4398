# PROJECT2 — TrafficScope Rewrite Documentation Set

**Status:** Future-state design. Nothing in this directory describes shipped behavior.

PROJECT2 is a ground-up specification for rebuilding TrafficScope. The existing code under
`TrafficSImulation/` is treated as a *behavioral reference* only: it shows what the product does today,
not how the rewrite is structured. Where PROJECT2 deliberately diverges from the current code, the
difference is recorded in [migration-from-current-implementation.md](migration-from-current-implementation.md).

The legacy documentation set (`docs/srs-context/`, `docs/agent-quickstart.md`,
`docs/jordan-context-files/`) is preserved unchanged for historical comparison. Do not treat it as
authoritative for PROJECT2.

---

## What PROJECT2 Is

TrafficScope is a browser application for rideshare-style trip planning in Austin, Texas. A user enters
an origin and a destination, chooses a planning mode, and receives route alternatives with
traffic-aware ETAs, per-segment road statistics, a traffic-colored map, and an illustrative fare
estimate.

| Aspect | Decision |
|--------|----------|
| Product name | TrafficScope |
| Service area | Austin, Texas metro (Google Places results biased to a 35 km circle around 30.2672, -97.7431) |
| View | React 19 + TypeScript, built with Vite |
| Controller | FastAPI, Python 3.13 |
| Model | Python domain packages under `TrafficSImulation/app/` |
| Map rendering | Google Maps JavaScript API only, through `@vis.gl/react-google-maps` |
| Place resolution | Google Places API (New) `places:searchText`, server-side |
| Routing | Google Routes API `directions/v2:computeRoutes`, server-side |
| Weather, congestion, pricing | Simulated planning estimates, never presented as official data |

All fares, congestion levels, and weather states are illustrative planning estimates. They are not
official Uber or Lyft fares and not live weather observations.

---

## Locked Decisions

Everything below is authoritative for the whole PROJECT2 set. No other PROJECT2 file may introduce a
different name, field, mode, or label. If a decision needs to change, change it here first, then
propagate.

### Terminology

| Term | Meaning | Do not call it |
|------|---------|----------------|
| Simulated mode | Scenario-driven planning; wire value `simulated`; UI label `Simulated` | sandbox, offline |
| Real-Time mode | Live traffic-aware planning; wire value `realtime`; UI label `Real-Time` | Reference, realtime mode (capitalize as `Real-Time` in UI text) |
| Route alternative | One of up to three scored driving options for a trip | route variant |
| Segment | A contiguous stretch of one route with its own road statistics | link, edge |
| Traffic interval | A polyline index range with a Google speed category | speed reading |
| Scenario | The set of user-adjustable planning variables | simulation config |
| Plan | One request/response cycle of `POST /api/plan` | query, search |

### Planning modes

| Mode | Wire value | Alternatives returned | Scenario applied | Departure time |
|------|-----------|----------------------|------------------|----------------|
| Simulated | `simulated` | Up to 3 | Yes | Next occurrence of `scenario.hour` |
| Real-Time | `realtime` | Exactly 1 | No | Now |

### Scenario variables

The complete, closed set. There are exactly three.

| Variable | Type | Range | Default | Meaning |
|----------|------|-------|---------|---------|
| `hour` | int | 0–23 | 17 | Departure hour, local Austin time |
| `weather` | int | 0–3 | 1 | Severity index: 0 Clear, 1 Light rain, 2 Heavy rain, 3 Severe |
| `congestion` | int | 0–100 | 56 | Network congestion percentage used by the BPR segment model |

**`demand` is out of scope for PROJECT2.** It is not a scenario variable, not a pricing factor, not a
route-scoring term, and not a heatmap metric. It does not appear in any request or response field.
This is the only statement of that decision; every other file simply omits it.

### Endpoints

| Method | Path | Phase | Purpose |
|--------|------|-------|---------|
| `POST` | `/api/plan` | P1 | Plan route alternatives for a trip |
| `GET` | `/api/health` | P1 | Service status plus Google API reachability |
| `GET` | `/api/map/config` | P1 | Browser map configuration, including the referrer-restricted browser key |
| `POST` | `/api/heatmap` | P3 | Congestion heatmap cells for a scenario (provisional contract) |

No other endpoints exist in the target design.

### `POST /api/plan` request

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

| Field | Type | Required | Constraint |
|-------|------|----------|------------|
| `origin` | string | yes | 1–120 characters after trimming |
| `destination` | string | yes | 1–120 characters after trimming |
| `mode` | string | no | `simulated` or `realtime`; default `simulated` |
| `hour` | int | no | 0–23; default 17 |
| `weather` | int | no | 0–3; default 1 |
| `congestion` | int | no | 0–100; default 56 |

In Real-Time mode the server accepts and then ignores `hour`, `weather`, and `congestion`.

The scenario variables are flat in the request and nested under `scenario` in the response. This is
deliberate: the request carries what the user asked for, the response reports what the server actually
used, and the two differ in Real-Time mode. Keeping them at different shapes makes it impossible to
confuse one for the other in either stack.

### `POST /api/plan` response

```json
{
  "origin": "Downtown Austin",
  "destination": "Austin-Bergstrom International Airport",
  "mode": "simulated",
  "scenario_applied": true,
  "scenario": { "hour": 17, "weather": 1, "congestion": 56 },
  "weather": {
    "severity": 1,
    "label": "Light rain",
    "time_multiplier": 1.08,
    "price_multiplier": 1.03,
    "source": "Simulated fallback"
  },
  "routes": [],
  "recommended_route_id": "route-1",
  "map_bounds": { "north": 30.29, "south": 30.19, "east": -97.66, "west": -97.76 },
  "notice": "Simulated mode: Google Maps supplies route geometry and departure-hour traffic; scenario controls adjust planning estimates."
}
```

| Field | Type | Notes |
|-------|------|-------|
| `origin`, `destination` | string | Resolved Google Places display names, not the raw user text |
| `mode` | string | Echo of the effective mode |
| `scenario_applied` | bool | `true` in Simulated mode, `false` in Real-Time mode |
| `scenario` | `Scenario` | Effective values actually used. In Real-Time mode: `hour` is the local departure hour, `weather` is 0, `congestion` is 0 |
| `weather` | `WeatherState` | `severity`, `label`, `time_multiplier`, `price_multiplier`, `source` |
| `routes` | `RouteOption[]` | Up to 3 in Simulated mode, exactly 1 in Real-Time mode |
| `recommended_route_id` | string | Always equals the `id` of one element of `routes` |
| `map_bounds` | `RouteBounds` | Union of the bounds of every returned route |
| `notice` | string | Mode-specific data-provenance sentence, always present and non-empty |

### `RouteOption`

| Field | Type | Notes |
|-------|------|-------|
| `id` | string | `route-1`, `route-2`, `route-3` |
| `name` | string | `Fastest`, `Balanced`, `Low traffic` |
| `objective` | string | Human-readable routing goal |
| `color` | string | Hex stroke color assigned by index |
| `distance_miles` | float | One decimal place |
| `base_eta_minutes` | float | Google static duration, one decimal place |
| `adjusted_eta_minutes` | float | After weather and mode adjustments, one decimal place |
| `estimated_price` | float | Two decimal places, US dollars |
| `congestion_score` | int | 0–100, derived from `scenario.congestion` and route index |
| `normalized_score` | float | Weighted comparison score, four decimal places, lower is better |
| `data_source` | string | `Google Routes with departure-hour traffic` or `Google Routes with live traffic` |
| `polyline` | `LatLngPoint[]` | Decoded route geometry, ordered origin to destination |
| `traffic_intervals` | `TrafficInterval[]` | Possibly empty; index ranges refer to `polyline` |
| `segments` | `RoadSegment[]` | At least one element |
| `price_factors` | `PriceFactors` | Fare breakdown |
| `bounds` | `RouteBounds` | Bounding box of `polyline` |

### Where the time-of-day factor applies

The time-of-day factor is `1.22` for hours 7 to 9 and 16 to 18, `0.92` for hours before 6 and from 22,
and `1.0` otherwise. It is applied in exactly two places, and deliberately not in a third.

| Quantity | Simulated | Real-Time | Why |
|----------|-----------|-----------|-----|
| `adjusted_eta_minutes` | Google traffic-aware duration times `weather.time_multiplier` | Google traffic-aware duration, unmodified | Google's traffic-aware duration for the current departure time already reflects real congestion. Multiplying it by a synthetic rush-hour factor would count the same effect twice |
| `price_factors.time_multiplier` | `1.0` | `time_of_day_factor` at the local departure hour | On the fare this factor represents time-of-day demand pricing, not travel time, so it is not a double count |

In Simulated mode the user's chosen departure hour is passed to Google as `departureTime`, so the same
reasoning applies: the hour shapes the ETA through Google, not through a multiplier.

### Shared value objects

| Type | Fields |
|------|--------|
| `LatLngPoint` | `lat` float, `lng` float |
| `RouteBounds` | `north` float, `south` float, `east` float, `west` float |
| `TrafficInterval` | `start_index` int, `end_index` int, `speed` enum |
| `TrafficSpeed` | `NORMAL`, `SLOW`, `TRAFFIC_JAM`, `SPEED_UNSPECIFIED` |
| `Scenario` | `hour` int, `weather` int, `congestion` int |
| `WeatherState` | `severity` int, `label` string, `time_multiplier` float, `price_multiplier` float, `source` string |
| `PriceFactors` | `route_subtotal` float, `traffic_multiplier` float, `weather_multiplier` float, `time_multiplier` float, `unrounded_total` float |
| `RoadSegment` | `name` string, `length_miles` float, `lanes` int, `speed_limit_mph` int, `average_speed_mph` float, `volume_vehicles_hour` int, `congestion` float 0–1, `capacity_vehicles_hour` int, `free_flow_minutes` float, `adjusted_minutes` float, `traffic_ratio` float, `polyline` `LatLngPoint[]` |

Every `PriceFactors` field is always present. `time_multiplier` is `1.0` when no time-of-day factor
applies, never absent and never null.

### `GET /api/map/config` response

```json
{
  "maps_browser_api_key": "AIza...",
  "map_id": null,
  "default_center": { "lat": 30.2672, "lng": -97.7431 },
  "default_zoom": 12,
  "color_scheme": "DARK",
  "libraries": ["core", "maps"]
}
```

`maps_browser_api_key` is a *separate* Google credential from the server key. See
[srs-context/controller/external-service-boundaries.md](srs-context/controller/external-service-boundaries.md).

### `GET /api/health` response

```json
{
  "status": "ok",
  "service": "TrafficScope",
  "version": "2.0",
  "google_maps_configured": true,
  "google_maps": { "ok": true, "message": "Places and Routes reachable.", "checked_at": "2026-07-30T21:00:00Z" }
}
```

### Error envelope

Every non-2xx response from every endpoint uses the same body shape.

```json
{ "detail": "Could not resolve \"Mars Colony\" to an Austin-area location.", "code": "invalid_location" }
```

| `code` | HTTP status | Cause |
|--------|-------------|-------|
| `validation_error` | 422 | Request body failed schema validation; adds a `fields` array |
| `invalid_location` | 400 | Places returned no usable result for `origin` or `destination` |
| `same_origin_destination` | 400 | Origin and destination resolved to the same place |
| `no_route_found` | 400 | Routes returned zero alternatives |
| `maps_not_configured` | 503 | A required Google credential is absent: the server key on `POST /api/plan`, the browser key on `GET /api/map/config` |
| `upstream_unavailable` | 502 | Places or Routes returned an error status |
| `upstream_timeout` | 504 | Places or Routes exceeded the request timeout |

### Requirement numbering

Functional requirements are `FR-<group>.<n>`. Non-functional requirements are `NFR-<group>.<n>`.
Acceptance tests are `T-<nn>`, zero-padded.

| Group | Subject |
|-------|---------|
| FR-1 | Location entry and resolution |
| FR-2 | Route planning, ETA, and comparison |
| FR-3 | Map rendering and traffic visualization |
| FR-4 | Planning mode selection |
| FR-5 | Scenario controls |
| FR-6 | Price estimation |
| FR-7 | Error handling and degraded operation |
| FR-8 | Congestion heatmap |
| NFR-1 | Responsiveness and performance |
| NFR-2 | Reliability and external API failure handling |
| NFR-3 | Security and API-key trust boundaries |
| NFR-4 | Accessibility |
| NFR-5 | Maintainability and architecture |
| NFR-6 | Testability and contract consistency |
| NFR-7 | Transparency and usability |

### Requirement status labels

Every requirement carries exactly one status.

| Status | Meaning |
|--------|---------|
| `Target` | Must be delivered by the phase named in the requirement's `Phase` column |
| `Out of scope` | Explicitly excluded from PROJECT2; recorded so it is not silently reintroduced |

### Roadmap phases

| Phase | Label | Content |
|-------|-------|---------|
| P1 | Core planning | Location resolution, Google-backed routing, one JavaScript API map path for both modes, route comparison, scenario controls, pricing, error envelope |
| P2 | Depth and resilience | Richer segment detail, degraded-mode experience, accessibility hardening, response caching, expanded test matrix |
| P3 | Congestion heatmap | `POST /api/heatmap`, grid overlay layer, legend |
| — | Out of scope | Accounts and login, driver profiles, payment processing, saved trip history, official rideshare fares, live weather APIs, demand modeling, transit and multimodal routing, native mobile apps |

### Target module layout

```
TrafficSImulation/
  main.py                        # ASGI app assembly, router mounting, SPA hosting
  app/
    api/                         # Controller
      models.py                  # Pydantic request and response models
      routes.py                  # APIRouter for /api/plan, /api/health, /api/map/config
      planning.py                # PlanningService orchestration
      mode_policy.py             # Simulated and Real-Time policy objects
      errors.py                  # Domain error to HTTP mapping and handlers
      dependencies.py            # Dependency providers
    map/                         # Model: geospatial and Google adapters
      places.py                  # GooglePlacesGateway
      routing.py                 # GoogleRoutesGateway
      polyline.py                # decode_polyline
      bounds.py                  # bounds_for_points, union_bounds
      health.py                  # GoogleApiProbe
      types.py                   # ResolvedPlace, RawRoute, LatLngPoint, RouteBounds, TrafficInterval
    simulation/                  # Model: traffic physics and scoring
      traffic.py                 # bpr_adjusted_time, time_of_day_factor
      segments.py                # SegmentBuilder
      scoring.py                 # RouteScorer
    pricing/
      model.py                   # PricingModel
    weather/
      service.py                 # WeatherService
    heatmap/                     # P3
      grid.py
      builder.py
    config/
      __init__.py                # Settings and all coefficients
  src/                           # View
    main.tsx
    App.tsx
    types.ts
    styles.css
    api/client.ts
    hooks/useRoutePlan.ts
    hooks/useMapConfig.ts
    constants/scenario.ts
    utils/trafficSegmentColor.ts
    utils/format.ts
    components/AppHeader.tsx
    components/RoutePlannerForm.tsx
    components/RouteOptionList.tsx
    components/RouteMap.tsx
    components/MapConfigProvider.tsx
    components/RoutePolylineLayer.tsx
    components/MapBoundsController.tsx
    components/AnalysisPanel.tsx
    components/ScenarioControls.tsx
    components/PriceSummary.tsx
    components/SegmentTable.tsx
    components/StatusBanner.tsx
    components/Toast.tsx
  tests/                         # pytest
```

The package names `api`, `map`, `heatmap`, `simulation`, `pricing`, `weather`, and `config` are fixed by
repo-root `AGENTS.md`. PROJECT2 keeps them and never uses flat module paths such as `app/routes.py`,
`app/models.py`, or `app/map_service.py`.

---

## Reading Order

| Order | Document | Purpose |
|-------|----------|---------|
| 1 | This file | Locked decisions and contracts |
| 2 | [agent-quickstart.md](agent-quickstart.md) | Orientation, commands, task-to-file map |
| 3 | [srs-context/README.md](srs-context/README.md) | Context index and MVC mapping |
| 4 | [srs-context/requirements/functional-requirements.md](srs-context/requirements/functional-requirements.md) | FR catalog |
| 5 | [srs-context/requirements/non-functional-requirements.md](srs-context/requirements/non-functional-requirements.md) | NFR catalog |
| 6 | [srs-context/architecture/architecture-overview.md](srs-context/architecture/architecture-overview.md) | Boundaries, dependency rules, trust boundaries |
| 7 | [srs-context/architecture/class-diagram.md](srs-context/architecture/class-diagram.md) | Concrete classes and interfaces |
| 8 | [srs-context/architecture/state-diagrams.md](srs-context/architecture/state-diagrams.md) | Lifecycles and state machines |
| 9 | Layer contexts under `srs-context/model/`, `controller/`, `view/` | Implementation detail per area |
| 10 | [srs-context/requirements/traceability.md](srs-context/requirements/traceability.md) | Requirement to context, test, and phase mapping |
| 11 | [migration-from-current-implementation.md](migration-from-current-implementation.md) | What the rewrite removes and why |

---

## File Index

### Entry points

| File | Purpose |
|------|---------|
| [README.md](README.md) | Locked decisions, contracts, reading order |
| [agent-quickstart.md](agent-quickstart.md) | Repository orientation and task-to-file map |
| [migration-from-current-implementation.md](migration-from-current-implementation.md) | Explicit exclusions carried over from the current code |

### Requirements

| File | Purpose |
|------|---------|
| [srs-context/requirements/functional-requirements.md](srs-context/requirements/functional-requirements.md) | FR-1 through FR-8 with acceptance criteria |
| [srs-context/requirements/non-functional-requirements.md](srs-context/requirements/non-functional-requirements.md) | NFR-1 through NFR-7 with measurable criteria |
| [srs-context/requirements/traceability.md](srs-context/requirements/traceability.md) | Owner context, phase, and planned test per requirement |

### Architecture

| File | Purpose |
|------|---------|
| [srs-context/architecture/architecture-overview.md](srs-context/architecture/architecture-overview.md) | System context, containers, components, dependency rules, deployment |
| [srs-context/architecture/class-diagram.md](srs-context/architecture/class-diagram.md) | Target classes, interfaces, responsibilities |
| [srs-context/architecture/state-diagrams.md](srs-context/architecture/state-diagrams.md) | Request lifecycle, UI states, mode transitions, map loading |

### Model

| File | Purpose |
|------|---------|
| [srs-context/model/domain-contracts.md](srs-context/model/domain-contracts.md) | Domain entities and value objects |
| [srs-context/model/route-planning.md](srs-context/model/route-planning.md) | Place resolution, route construction, scoring |
| [srs-context/model/traffic-simulation.md](srs-context/model/traffic-simulation.md) | BPR model, segments, time-of-day factor |
| [srs-context/model/pricing.md](srs-context/model/pricing.md) | Fare estimation and factor breakdown |
| [srs-context/model/weather-scenarios.md](srs-context/model/weather-scenarios.md) | Weather severity and scenario semantics |
| [srs-context/model/heatmaps.md](srs-context/model/heatmaps.md) | P3 congestion heatmap design |
| [srs-context/model/google-integrations.md](srs-context/model/google-integrations.md) | Places, Routes, and polyline adapters |
| [srs-context/model/configuration.md](srs-context/model/configuration.md) | Settings and coefficient catalog |

### Controller

| File | Purpose |
|------|---------|
| [srs-context/controller/api-contracts.md](srs-context/controller/api-contracts.md) | Endpoint contracts and schemas |
| [srs-context/controller/orchestration.md](srs-context/controller/orchestration.md) | `PlanningService` workflow |
| [srs-context/controller/mode-policies.md](srs-context/controller/mode-policies.md) | Simulated and Real-Time policy rules |
| [srs-context/controller/validation-error-handling.md](srs-context/controller/validation-error-handling.md) | Validation layers and error mapping |
| [srs-context/controller/external-service-boundaries.md](srs-context/controller/external-service-boundaries.md) | Google boundaries, timeouts, credentials |

### View

| File | Purpose |
|------|---------|
| [srs-context/view/app-composition.md](srs-context/view/app-composition.md) | Layout, state ownership, data flow |
| [srs-context/view/route-scenario-forms.md](srs-context/view/route-scenario-forms.md) | Trip form and scenario controls |
| [srs-context/view/map-rendering.md](srs-context/view/map-rendering.md) | Maps JavaScript API rendering path |
| [srs-context/view/results-analysis.md](srs-context/view/results-analysis.md) | Route cards, pricing, segment table |
| [srs-context/view/loading-error-states.md](srs-context/view/loading-error-states.md) | Loading, empty, error, degraded states |
| [srs-context/view/accessibility.md](srs-context/view/accessibility.md) | Keyboard, semantics, contrast, non-visual parity |

---

## Conventions For PROJECT2 Documents

- Reference code by concrete target path, for example `app/api/planning.py`, not by prose description.
- Mark every requirement with a status and a phase.
- Never describe a P2 or P3 capability in the present tense as if it exists.
- Mermaid diagrams use identifiers without spaces, quote any label containing punctuation, and avoid
  color, `style`, `classDef`, and `click` directives.
- Python is four-space indented and `snake_case`; TypeScript and TSX are two-space indented with
  `PascalCase` components and types and `camelCase` values, per repo-root `AGENTS.md`.
