# Controller Context — API Contracts

**Layer:** Controller  
**Target modules:** `TrafficSImulation/app/api/models.py`, `TrafficSImulation/app/api/routes.py`, `TrafficSImulation/main.py`  
**Related:** [orchestration.md](orchestration.md), [mode-policies.md](mode-policies.md), [validation-error-handling.md](validation-error-handling.md), [external-service-boundaries.md](external-service-boundaries.md), [../model/domain-contracts.md](../model/domain-contracts.md), [../view/app-composition.md](../view/app-composition.md), [../requirements/functional-requirements.md](../requirements/functional-requirements.md)

## Purpose

Define the complete HTTP surface of TrafficScope: request schemas, response schemas, status codes, and
the guarantees the View may rely on. This file is the single wire-format authority for the Controller.
Any field not listed here does not exist.

## Requirements

| ID | Requirement | Status | Phase |
|----|-------------|--------|-------|
| FR-1.7 | Response reports resolved Places display names, not the raw user text | Target | P1 |
| FR-2.2 | Simulated mode returns up to three alternatives with the documented names and objectives | Target | P1 |
| FR-2.3 | Real-Time mode returns exactly one alternative | Target | P1 |
| FR-2.6 | Each route reports `adjusted_eta_minutes` computed by the active mode policy | Target | P1 |
| FR-2.8 | `recommended_route_id` exposes the best-ranked route | Target | P1 |
| FR-2.9 | Each route declares its provenance in `data_source` | Target | P1 |
| FR-3.3 | Route geometry is delivered as `route.polyline` for native polyline rendering | Target | P1 |
| FR-3.4 | `traffic_intervals` accompany each route so the View can slice its polyline | Target | P1 |
| FR-3.7 | Per-route `bounds` and plan-level `map_bounds` support camera fitting | Target | P1 |
| FR-4.3 | `scenario_applied` declares whether scenario inputs were applied | Target | P1 |
| FR-4.5 | Response carries a mode-specific `notice` describing where the numbers come from | Target | P1 |
| FR-5.6 | Out-of-range scenario values return 422 with code `validation_error` | Target | P1 |
| FR-5.7 | Response echoes the effective scenario actually used in `scenario` | Target | P1 |
| FR-6.2 | `price_factors` exposes all five fare terms on every route | Target | P1 |
| FR-7.1 | Every non-2xx response uses the `{detail, code}` envelope | Target | P1 |
| FR-7.2 | Each failure class maps to exactly one code and status | Target | P1 |
| NFR-1.1 | `POST /api/plan` p95 latency under 3 s with Google reachable | Target | P1 |
| NFR-3.7 | The SPA fallback serves only files resolved inside the build output directory | Target | P1 |
| NFR-6.1 | Every endpoint has an automated test asserting status codes and response field set | Target | P1 |
| NFR-6.4 | `src/types.ts` mirrors `app/api/models.py`, and a test fails when the field sets diverge | Target | P1 |
| NFR-6.7 | A contract test asserts the exact top-level and per-route field sets | Target | P1 |
| NFR-7.1 | `notice` is present and non-empty on every 200 plan response | Target | P1 |
| FR-8.1 | `POST /api/heatmap` returns congestion intensity cells for a submitted scenario | Target | P3 |
| FR-3.10 | Server-computed map camera state such as a center point and zoom level | Out of scope | — |
| — | Any endpoint beyond the four listed below | Out of scope | — |

## Endpoint Index

| Method | Path | Request model | Response model | Phase |
|--------|------|---------------|----------------|-------|
| `POST` | `/api/plan` | `PlanRequest` | `PlanResponse` | P1 |
| `GET` | `/api/health` | — | `HealthResponse` | P1 |
| `GET` | `/api/map/config` | — | `MapConfigResponse` | P1 |
| `POST` | `/api/heatmap` | `HeatmapRequest` | `HeatmapResponse` | P3 |

All four are mounted from `app/api/routes.py` onto a single `APIRouter` with prefix `/api`. `main.py`
includes that router and adds nothing else except static hosting and exception handlers. Request and
response models are declared in `app/api/models.py`; no route function returns an untyped `dict`.

---

## `POST /api/plan`

### Request — `PlanRequest`

| Field | Type | Required | Constraint | Default |
|-------|------|----------|------------|---------|
| `origin` | string | yes | 1–120 characters after trimming | — |
| `destination` | string | yes | 1–120 characters after trimming | — |
| `mode` | string | no | `simulated` or `realtime` | `simulated` |
| `hour` | int | no | 0–23 | 17 |
| `weather` | int | no | 0–3 | 1 |
| `congestion` | int | no | 0–100 | 56 |

Unknown fields are rejected rather than ignored, so a stale client cannot silently send a retired
field. In Real-Time mode the server accepts `hour`, `weather`, and `congestion` and then ignores them;
sending them is never an error.

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

### Response 200 — `PlanResponse`

| Field | Type | Notes |
|-------|------|-------|
| `origin` | string | Resolved Places display name for the origin |
| `destination` | string | Resolved Places display name for the destination |
| `mode` | string | Echo of the effective mode |
| `scenario_applied` | bool | `true` in Simulated mode, `false` in Real-Time mode |
| `scenario` | `Scenario` | Effective values used for this plan |
| `weather` | `WeatherState` | Weather state applied to the plan |
| `routes` | `RouteOption[]` | Up to 3 in Simulated mode, exactly 1 in Real-Time mode |
| `recommended_route_id` | string | `id` of one element of `routes` |
| `map_bounds` | `RouteBounds` | Union of the `bounds` of every element of `routes` |
| `notice` | string | Mode-specific data-provenance sentence, never empty |

### `RouteOption`

| Field | Type | Notes |
|-------|------|-------|
| `id` | string | `route-1`, `route-2`, `route-3`, assigned by position |
| `name` | string | `Fastest`, `Balanced`, `Low traffic` |
| `objective` | string | Human-readable routing goal for the alternative |
| `color` | string | Hex stroke color assigned by index, used by the polyline layer |
| `distance_miles` | float | One decimal place |
| `base_eta_minutes` | float | Google static duration in minutes, one decimal place |
| `adjusted_eta_minutes` | float | After mode and weather adjustment, one decimal place |
| `estimated_price` | float | US dollars, two decimal places |
| `congestion_score` | int | 0–100 |
| `normalized_score` | float | Four decimal places, lower is better |
| `data_source` | string | Provenance label, see the table below |
| `polyline` | `LatLngPoint[]` | Decoded geometry, ordered origin to destination, never empty |
| `traffic_intervals` | `TrafficInterval[]` | May be empty; indices refer to `polyline` |
| `segments` | `RoadSegment[]` | At least one element |
| `price_factors` | `PriceFactors` | Fare breakdown, all five fields present |
| `bounds` | `RouteBounds` | Bounding box of this route's `polyline` |

The fare breakdown field is named `price_factors`. There is no `factors` field.

| Mode | `data_source` |
|------|---------------|
| Simulated | `Google Routes with departure-hour traffic` |
| Real-Time | `Google Routes with live traffic` |

### Value objects

| Type | Fields |
|------|--------|
| `LatLngPoint` | `lat` float, `lng` float |
| `RouteBounds` | `north` float, `south` float, `east` float, `west` float |
| `TrafficInterval` | `start_index` int, `end_index` int, `speed` enum |
| `TrafficSpeed` | `NORMAL`, `SLOW`, `TRAFFIC_JAM`, `SPEED_UNSPECIFIED` |
| `Scenario` | `hour` int, `weather` int, `congestion` int |
| `WeatherState` | `severity` int, `label` string, `time_multiplier` float, `price_multiplier` float, `source` string |
| `PriceFactors` | `route_subtotal` float, `traffic_multiplier` float, `weather_multiplier` float, `time_multiplier` float, `unrounded_total` float |
| `RoadSegment` | `name` string, `length_miles` float, `lanes` int, `speed_limit_mph` int, `average_speed_mph` float, `volume_vehicles_hour` int, `congestion` float 0.0–1.0, `capacity_vehicles_hour` int, `free_flow_minutes` float, `adjusted_minutes` float, `traffic_ratio` float, `polyline` `LatLngPoint[]` |

`PriceFactors.time_multiplier` is `1.0` when no time-of-day factor applies. It is never absent and
never null, so the View can render the fare breakdown without conditional branches.

### Example 200 response, Simulated mode

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
  "routes": [
    {
      "id": "route-1",
      "name": "Fastest",
      "objective": "Minimum adjusted time",
      "color": "#55d6be",
      "distance_miles": 11.4,
      "base_eta_minutes": 18.0,
      "adjusted_eta_minutes": 22.5,
      "estimated_price": 27.22,
      "congestion_score": 56,
      "normalized_score": 0.8123,
      "data_source": "Google Routes with departure-hour traffic",
      "polyline": [
        { "lat": 30.2672, "lng": -97.7431 },
        { "lat": 30.2455, "lng": -97.7208 },
        { "lat": 30.1975, "lng": -97.6664 }
      ],
      "traffic_intervals": [
        { "start_index": 0, "end_index": 1, "speed": "SLOW" },
        { "start_index": 1, "end_index": 2, "speed": "NORMAL" }
      ],
      "segments": [
        {
          "name": "E Riverside Dr",
          "length_miles": 5.7,
          "lanes": 3,
          "speed_limit_mph": 45,
          "average_speed_mph": 27.4,
          "volume_vehicles_hour": 1310,
          "congestion": 0.56,
          "capacity_vehicles_hour": 1560,
          "free_flow_minutes": 7.6,
          "adjusted_minutes": 12.5,
          "traffic_ratio": 1.24,
          "polyline": [
            { "lat": 30.2672, "lng": -97.7431 },
            { "lat": 30.2455, "lng": -97.7208 }
          ]
        }
      ],
      "price_factors": {
        "route_subtotal": 23.767,
        "traffic_multiplier": 1.112,
        "weather_multiplier": 1.03,
        "time_multiplier": 1.0,
        "unrounded_total": 27.2217711
      },
      "bounds": { "north": 30.2672, "south": 30.1975, "east": -97.6664, "west": -97.7431 }
    }
  ],
  "recommended_route_id": "route-1",
  "map_bounds": { "north": 30.2672, "south": 30.1975, "east": -97.6664, "west": -97.7431 },
  "notice": "Simulated mode: Google Maps supplies route geometry and departure-hour traffic; scenario controls adjust planning estimates."
}
```

The `routes` array above shows one fully expanded element for readability. A Simulated response carries
up to three, each with the same shape, ids `route-1` through `route-3`.

### Example 200 response, Real-Time mode, abbreviated

```json
{
  "origin": "Downtown Austin",
  "destination": "Austin-Bergstrom International Airport",
  "mode": "realtime",
  "scenario_applied": false,
  "scenario": { "hour": 8, "weather": 0, "congestion": 0 },
  "weather": {
    "severity": 0,
    "label": "Clear",
    "time_multiplier": 1.0,
    "price_multiplier": 1.0,
    "source": "Simulated fallback"
  },
  "routes": [
    {
      "id": "route-1",
      "name": "Fastest",
      "data_source": "Google Routes with live traffic",
      "estimated_price": 26.93,
      "congestion_score": 4,
      "price_factors": {
        "route_subtotal": 21.9,
        "traffic_multiplier": 1.008,
        "weather_multiplier": 1.0,
        "time_multiplier": 1.22,
        "unrounded_total": 26.931744
      }
    }
  ],
  "recommended_route_id": "route-1",
  "map_bounds": { "north": 30.2672, "south": 30.1975, "east": -97.6664, "west": -97.7431 },
  "notice": "Real-Time mode: route, distance, and travel time come from Google Maps traffic-aware routing for the current departure time."
}
```

In Real-Time mode `scenario.hour` is the current local Austin hour, `scenario.weather` is `0`, and
`scenario.congestion` is `0`. Those are reported so the View can display what the server actually
used instead of what the inert controls happen to show.

### Notice strings

Exact text, byte for byte. The View never composes these.

| Mode | `notice` |
|------|----------|
| Simulated | `Simulated mode: Google Maps supplies route geometry and departure-hour traffic; scenario controls adjust planning estimates.` |
| Real-Time | `Real-Time mode: route, distance, and travel time come from Google Maps traffic-aware routing for the current departure time.` |

### Status codes

| Status | `code` | When |
|--------|--------|------|
| 200 | — | Plan computed |
| 400 | `invalid_location` | Places returned no usable result for `origin` or `destination` |
| 400 | `same_origin_destination` | Origin and destination resolved to the same place |
| 400 | `no_route_found` | Routes returned zero alternatives |
| 422 | `validation_error` | Body failed schema validation; adds a `fields` array |
| 502 | `upstream_unavailable` | Places or Routes returned an error status |
| 503 | `maps_not_configured` | Server Google credential is absent |
| 504 | `upstream_timeout` | Places or Routes exceeded the configured timeout |

---

## `GET /api/health`

No request body and no query parameters. Always returns 200, including when Google is unreachable;
reachability is reported inside the body rather than through the status code so that container health
probes do not restart a service that is merely degraded.

| Field | Type | Notes |
|-------|------|-------|
| `status` | string | Always `ok` |
| `service` | string | Always `TrafficScope` |
| `version` | string | Always `2.0` |
| `google_maps_configured` | bool | Whether the server Google credential is present |
| `google_maps` | object | `ok` bool, `message` string, `checked_at` ISO-8601 UTC string |

```json
{
  "status": "ok",
  "service": "TrafficScope",
  "version": "2.0",
  "google_maps_configured": true,
  "google_maps": { "ok": true, "message": "Places and Routes reachable.", "checked_at": "2026-07-30T21:00:00Z" }
}
```

`google_maps` is the cached result of the `GoogleApiProbe` run by the `main.py` lifespan startup hook.
The handler never performs a live Google call, which keeps health checks free of upstream quota cost.
`version` is bumped only for a breaking change to any contract in this file.

---

## `GET /api/map/config`

No request body. Supplies everything `MapConfigProvider.tsx` needs to initialize the Google Maps
JavaScript API through `@vis.gl/react-google-maps`. This is the only endpoint that returns a
credential, and the credential it returns is the referrer-restricted browser key, never the server
key. See [external-service-boundaries.md](external-service-boundaries.md).

| Field | Type | Notes |
|-------|------|-------|
| `maps_browser_api_key` | string | Referrer-restricted browser key, scoped to the Maps JavaScript API |
| `map_id` | string or null | Cloud-styled map identifier; null when unstyled |
| `default_center` | object | `lat` 30.2672, `lng` -97.7431 |
| `default_zoom` | int | 12 |
| `color_scheme` | string | `DARK` |
| `libraries` | string[] | `["core", "maps"]` |

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

| Status | `code` | When |
|--------|--------|------|
| 200 | — | Browser key configured |
| 503 | `maps_not_configured` | Browser key absent from `Settings` |

Responses carry `Cache-Control: no-store`. The browser key is a deployment secret in the sense that it
should not be archived by intermediaries, even though it is designed to be visible in the page.

---

## `POST /api/heatmap`

Provisional P3 contract. It is documented here so the shape is reserved, not because it is
implemented. The cell geometry and intensity semantics are owned by
[../model/heatmaps.md](../model/heatmaps.md); if the two disagree, that file wins for cell internals
and this file wins for envelope and status codes.

### Request — `HeatmapRequest`

| Field | Type | Required | Constraint | Default |
|-------|------|----------|------------|---------|
| `hour` | int | no | 0–23 | 17 |
| `weather` | int | no | 0–3 | 1 |
| `congestion` | int | no | 0–100 | 56 |
| `bounds` | `RouteBounds` | no | Viewport to cover; server default is the Austin metro box | null |

### Response 200 — `HeatmapResponse`

| Field | Type | Notes |
|-------|------|-------|
| `scenario` | `Scenario` | Effective values used |
| `bounds` | `RouteBounds` | Box the returned grid covers |
| `cells` | `HeatmapCell[]` | Grid cells, ordered row-major |
| `notice` | string | Non-empty provenance sentence |

`HeatmapCell` is provisionally `north`, `south`, `east`, `west` floats plus `congestion` float 0.0–1.0
and `intensity` float 0.0–1.0.

| Status | `code` | When |
|--------|--------|------|
| 200 | — | Grid computed |
| 422 | `validation_error` | Body failed schema validation |

---

## Static SPA Hosting

`main.py` mounts production frontend assets only when `TrafficSImulation/dist/` exists. In development
the directory is absent and both routes are unregistered, so a missing build never shadows the API.

| Method | Path | Behavior |
|--------|------|----------|
| `GET` | `/assets/*` | Serves hashed Vite build artifacts from `dist/assets/` |
| `GET` | `/{path}` | Serves `dist/{path}` when it resolves to a real file inside `dist/`, otherwise `dist/index.html` |

The fallback route is registered last so that `/api/*` always resolves to the router. Path candidates
are resolved and checked for containment inside `dist/` before being served, so `..` traversal cannot
read outside the build directory. The fallback returns `index.html` with status 200 rather than 404
because client-side routing owns unknown paths.

## Response Guarantees

The View may rely on all of the following for any 200 response from `POST /api/plan`. Contract tests
assert each one.

- `routes` has 1 element in Real-Time mode and up to 3 in Simulated mode. It is never empty; zero
  alternatives is a `no_route_found` error, not an empty success.
- `recommended_route_id` matches the `id` of an element of `routes`.
- `notice` is present, is a string, and is not empty.
- Array fields are `[]` rather than `null` when empty. This applies to `routes`, `polyline`,
  `traffic_intervals`, `segments`, and `libraries`.
- `polyline` and `segments` each have at least one element on every route.
- `price_factors` has all five fields on every route.
- `bounds` is present on every route and `map_bounds` contains every route's `bounds`.
- `scenario` reports effective values, so `scenario_applied` being `false` still yields a fully
  populated `scenario`.
- Route ids are dense and positional: a 3-route response is `route-1`, `route-2`, `route-3`.

## OpenAPI Exposure

FastAPI publishes the generated schema at `/openapi.json` and interactive documentation at `/docs`.
Because every handler declares a `response_model` from `app/api/models.py`, the published schema is
derived from the same declarations the runtime validates against, and there is no hand-maintained
specification to drift. Error responses are declared per route with the `responses=` argument so that
`/docs` lists each `code` an endpoint can return.

## Development Proxy

| Concern | Development | Production |
|---------|-------------|------------|
| Frontend origin | `http://127.0.0.1:5173` (Vite) | Same origin as the API |
| API origin | `http://127.0.0.1:8000` (Uvicorn) | Same origin as the frontend |
| `/api` routing | Vite dev server proxies `/api` to `http://127.0.0.1:8000` | Handled directly by FastAPI |
| CORS | Not required; the proxy makes requests same-origin | Not required; single origin |

Because both arrangements are same-origin from the browser's point of view, the frontend always calls
relative paths such as `/api/plan`. No absolute API base URL is compiled into the bundle, and no CORS
middleware is configured.

## Python to TypeScript Contract Sync

`app/api/models.py` and `src/types.ts` describe the same wire format in two languages and must be
edited together in one commit.

| Rule | Detail |
|------|--------|
| Naming | Wire fields stay `snake_case` in TypeScript. No camelCase remapping in `src/api/client.ts`. |
| Direction | `app/api/models.py` is the source of truth; `src/types.ts` mirrors it. |
| Additions | A new response field is optional in `src/types.ts` only until the next frontend release, then required. |
| Removals | Remove the field from `src/types.ts` consumers first, then from `app/api/models.py`. |
| Enums | `mode` and `TrafficSpeed` are string literal unions in TypeScript, matching the Python enum values exactly. |
| Verification | `npm run build` type-checks consumers; `python -m pytest` asserts the served shape. Both must pass. |

```python
class Scenario(BaseModel):
    hour: int = Field(default=17, ge=0, le=23)
    weather: int = Field(default=1, ge=0, le=3)
    congestion: int = Field(default=56, ge=0, le=100)
```

```typescript
export interface Scenario {
  hour: number;
  weather: number;
  congestion: number;
}
```

## Acceptance Criteria

- [ ] `GET /api/health` returns 200 with `version` `"2.0"` and a `google_maps` object containing `ok`, `message`, and `checked_at`.
- [ ] A valid Simulated request returns 200 with up to 3 routes, and every route carries `price_factors`, `segments`, `polyline`, `traffic_intervals`, and `bounds`.
- [ ] A valid Real-Time request returns 200 with exactly 1 route and `scenario_applied` `false`.
- [ ] `recommended_route_id` matches a returned route id in every 200 plan response.
- [ ] `notice` equals the verbatim mode string for the effective mode.
- [ ] No response body contains a `factors` key; the fare breakdown is `price_factors` everywhere.
- [ ] `weather=99` returns 422 with `code` `validation_error` and a `fields` array.
- [ ] Every non-2xx plan response body has exactly the `detail` and `code` keys, plus `fields` for 422.
- [ ] `GET /api/map/config` returns the browser key, center 30.2672 / -97.7431, zoom 12, `DARK`, and `["core", "maps"]`.
- [ ] `GET /api/map/config` returns 503 `maps_not_configured` when the browser key is absent.
- [ ] `/openapi.json` lists all four API paths and resolves `PlanResponse` without unresolved references.
- [ ] `src/types.ts` declares every field listed in this file with matching names.

## Planned Tests

| Test ID | Level | Target file | Assertion |
|---------|-------|-------------|-----------|
| T-24 | api | `tests/test_contracts.py` | The top-level and per-route field sets match this file exactly, with `price_factors` present and no `factors` key; `recommended_route_id` matches a returned route id in both modes; `routes`, `polyline`, `traffic_intervals`, and `segments` are lists rather than null, and `polyline` and `segments` are non-empty; `/openapi.json` lists all four API paths and resolves every model reference; and `src/types.ts` declares the same field set |
| T-10 | api | `tests/test_api.py` | `GET /api/health` returns 200 with `version` `"2.0"`, `service` `"TrafficScope"`, and a `google_maps` object carrying `ok`, `message`, and `checked_at` |
| T-01 | api | `tests/test_api.py` | A Simulated plan returns 200 with up to three routes, every documented top-level field, and `notice` equal to the verbatim Simulated string |
| T-02 | api | `tests/test_api.py` | A Real-Time plan returns 200 with exactly one route, `scenario_applied` `false`, and `notice` equal to the verbatim Real-Time string |
| T-11 | api | `tests/test_api.py` | `GET /api/map/config` returns exactly the six documented keys with the documented default values and the browser credential rather than the server credential, and returns 503 `maps_not_configured` when the browser key is absent |
| T-42 | api | `tests/test_static.py` | An unknown non-API path returns `index.html` when `dist/` exists, a traversal candidate is refused, and `/api/plan` is not shadowed |

## Agent Implementation Notes

- Declare every route with an explicit `response_model` in `app/api/routes.py`. A handler returning a bare `dict` is a contract regression even when the keys happen to be right.
- Keep `main.py` thin: create the app, register exception handlers from `app/api/errors.py`, include the router, mount static hosting, run the lifespan probe. Business logic belongs in `app/api/planning.py`.
- Register the `GET /{path}` fallback after the router. Adding it earlier makes every API 404 return `index.html`.
- When adding a response field, update `app/api/models.py`, `src/types.ts`, this file, and a test in the same commit. A field that exists in two of the four is a bug.
- Serialize floats already rounded to their documented precision in the Model rather than formatting in the View, so API consumers and the UI agree.
- Do not add CORS middleware. If a deployment ever needs a separate frontend origin, that is a contract change and belongs in this file first.
- Never widen an error body beyond `detail`, `code`, and the 422 `fields` array.
