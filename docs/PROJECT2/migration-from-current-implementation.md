# Migration From The Current Implementation

**Purpose:** Record exactly what PROJECT2 removes, renames, or defers relative to the code in
`TrafficSImulation/`, so that a rewrite does not accidentally reintroduce it.

**This is the only PROJECT2 document permitted to name the legacy concepts below.** Every other
PROJECT2 file describes the target design and must contain none of these terms. If you find one of
these strings anywhere else under `docs/PROJECT2/`, that is a defect.

**Authority:** [README.md](README.md) holds the locked target contracts.
**Related:** [srs-context/architecture/architecture-overview.md](srs-context/architecture/architecture-overview.md), [srs-context/controller/api-contracts.md](srs-context/controller/api-contracts.md), [srs-context/view/map-rendering.md](srs-context/view/map-rendering.md)

---

## 1. Removed: The Second Map Rendering Path

The current application renders two different kinds of map depending on mode. Simulated mode already
uses the Google Maps JavaScript API through `@vis.gl/react-google-maps`. Real-Time mode instead
renders a Google Maps Embed API `iframe` whose URL arrives in the response as `directions_embed_url`.

PROJECT2 removes the second path entirely. There is one map surface and both modes use it.

| Legacy artifact | Legacy location | Disposition |
|-----------------|-----------------|-------------|
| Maps Embed API `iframe` branch | `src/components/TrafficMap.tsx` | Deleted. Replaced by `src/components/RouteMap.tsx`, used identically in both modes |
| `directions_embed_url` response field | `app/api/routes.py`, `src/types.ts` | Deleted from the contract |
| `map_embed_url` response field, per route and top level | `app/api/routes.py`, `src/types.ts` | Deleted from the contract |
| `build_directions_embed_url` | `app/map/google_embed.py` | Deleted |
| `build_map_embed_url` | `app/map/google_embed.py` | Deleted |
| `POST /api/map/embed` endpoint | `main.py` | Deleted. No replacement endpoint |
| `app/map/google_embed.py` module | — | Deleted |

Why: two rendering paths meant two visual languages, two failure modes, two accessibility stories, and
a mode-dependent feature set that was never documented. The Embed API also cannot draw
traffic-colored polylines, which is the core visualization of the product.

Consequence to accept deliberately: Real-Time mode loses the embedded Google directions panel. The
target design compensates by rendering the single Real-Time route with Google traffic colors on the
JavaScript API map and showing its statistics in the standard analysis panel.

---

## 2. Removed: Server-Computed Camera State

The current response carries a `map_view` object of `center_lat`, `center_lng`, and `zoom`, computed
server-side by `compute_map_view_for_polyline`. That is camera projection logic in the Model, and it
exists only because an Embed API URL needs a center and a zoom.

| Legacy artifact | Legacy location | Disposition |
|-----------------|-----------------|-------------|
| `map_view` field, per route and top level | `app/api/routes.py`, `src/types.ts` | Replaced by `bounds` per route and `map_bounds` at the top level |
| `MapView` TypeScript interface | `src/types.ts` | Deleted |
| `compute_map_view_for_polyline` | `app/map/google_embed.py` | Replaced by `bounds_for_points` and `union_bounds` in `app/map/bounds.py` |
| `MapEmbedRequest` model | `app/api/models.py` | Deleted |
| `app/map/projection.py` | — | Deleted |

Why: a geographic bounding box is a fact about the route; a center and a zoom level are a decision
about a viewport. The server should state the fact and let `map.fitBounds` make the viewport decision,
which also adapts correctly to the container size.

---

## 3. Removed: The SVG Map And Projection Overlay

An earlier design drew routes as SVG paths over a stylized illustration of Austin, projecting
latitude and longitude into SVG coordinates.

| Legacy artifact | Legacy location | Disposition |
|-----------------|-----------------|-------------|
| `RouteOverlay` component | `src/components/RouteOverlay.tsx` | Deleted. Route geometry is drawn by `google.maps.Polyline` in `src/components/RoutePolylineLayer.tsx` |
| Latitude and longitude to SVG projection helpers | `src/utils/mapProjection.ts` | Deleted |
| Projection unit tests | `src/utils/mapProjection.test.ts` | Deleted |
| `Point` domain type with `x` and `y` SVG coordinates | legacy `app/models.py` | Deleted. Geometry is `LatLngPoint` with `lat` and `lng` only |
| Stylized SVG road network, water shape, and zone labels | legacy `TrafficMap` markup | Deleted |

Why: the overlay duplicated map rendering that the Maps JavaScript API already does correctly, and it
required the backend to emit screen-space geometry. It is dead code in the current application.

---

## 4. Removed: Local Geocoding And A Local Routing Fallback

The current repository still contains a dictionary-based Austin place lookup with fuzzy matching, and
the legacy documentation describes a second planning mode backed by a local reference model.

| Legacy artifact | Legacy location | Disposition |
|-----------------|-----------------|-------------|
| Dictionary place lookup with fuzzy matching | `app/map/local.py` | Deleted. Place resolution is Google Places only |
| Synthetic route geometry generation | legacy `app/map_service.py` behavior | Deleted. Route geometry is Google Routes only |
| `"current location"` server-side alias | `app/map/places.py` | Deleted. The browser sends resolved coordinates as `lat, lng` text |
| `ResolvedPlace.source` values other than the Google source | `app/map/types.py` | Narrowed. There is one source |

Why: a silent fallback produces numbers that look real and are not, which conflicts with NFR-2.5 and
NFR-7.1. In PROJECT2 an absent credential or an unreachable upstream is an explicit error state with a
documented code, not substituted data.

Consequence to accept deliberately: PROJECT2 cannot plan a route without a working Google credential.
That is stated as a hard dependency rather than hidden behind a fallback.

---

## 5. Renamed: Mode Terminology

| Legacy term | Where it appears | PROJECT2 term |
|-------------|------------------|---------------|
| "Reference mode" | `docs/srs-context/controller/*.md`, `docs/srs-context/README.md` | Real-Time mode |
| "Local reference model" as a `data_source` value | legacy orchestration | `Google Routes with live traffic` |
| `realtime` wire value | `app/api/models.py` | Unchanged. The wire value stays `realtime`; only the human-readable label changes |

The wire value `realtime` is retained on purpose so the migration does not churn the request contract.
The user-facing label is always `Real-Time`.

---

## 6. Renamed: Response Fields

| Legacy field | PROJECT2 field | Reason |
|--------------|----------------|--------|
| `factors` on a route | `price_factors` | `factors` did not say what it factored |
| `maps_api_key` in the map configuration response | `maps_browser_api_key` | Names the credential class and makes the trust boundary visible |
| flat `hour` and `congestion` echoes on the response | `scenario` object plus `scenario_applied` | One place to read the effective scenario, and an explicit statement of whether it was applied |
| optional `factors.time_multiplier` | `price_factors.time_multiplier`, always present | Removes an optional numeric field from the contract |

---

## 7. Deferred: Heatmaps

`app/heatmap/builder.py` and `app/heatmap/grid.py` exist in the current repository but are not imported
by any endpoint or rendered by any component. The legacy documentation nonetheless describes
congestion, demand, and profitability heatmaps as implemented behavior with a map toolbar, a legend,
and an off switch.

PROJECT2 treats heatmaps as phase P3 roadmap work under FR-8, narrowed to a congestion metric.
Demand and profitability metrics are out of scope. See
[srs-context/model/heatmaps.md](srs-context/model/heatmaps.md).

---

## 8. Removed: The Demand Variable

The `demand` scenario variable was removed from the live code but persists throughout the legacy
documentation as a slider, a route field, a pricing factor, a scoring term, and a heatmap mode.

PROJECT2 decides this once: `demand` is out of scope. It is not a request field, not a response field,
not a scoring term, not a pricing factor, and not a heatmap metric. The route scoring weights are
`time` 0.47, `distance` 0.23, and `congestion` 0.30, summing to 1.0.

Legacy references that no longer apply: the `demand` field in `PlanRequest`, `demand_score` on a
route, the "Customer demand" slider, the demand and profitability heatmap modes, and the
`- w_demand * (demand / 100)` term in the scoring formula.

---

## 9. Removed: Flat Module Paths

The legacy documentation references module paths that no longer exist even in the current code.

| Legacy path in the old docs | PROJECT2 path |
|-----------------------------|---------------|
| `app/routes.py` | `app/api/routes.py` for HTTP, `app/api/planning.py` for orchestration |
| `app/models.py` | `app/api/models.py` |
| `app/map_service.py` | `app/map/places.py` and `app/map/routing.py` |
| `app/traffic_simulator.py` | `app/simulation/traffic.py` and `app/simulation/segments.py` |
| `app/pricing_model.py` | `app/pricing/model.py` |
| `app/weather_service.py` | `app/weather/service.py` |
| `app/heatmap.py` | `app/heatmap/builder.py` and `app/heatmap/grid.py` |
| `app/config.py` | `app/config/__init__.py` |

---

## 10. Restructured: Error Responses

| Legacy behavior | PROJECT2 behavior |
|-----------------|-------------------|
| Every domain failure became `400` with a `detail` string | Seven distinct codes across `400`, `422`, `502`, `503`, and `504` |
| A missing credential became `400` | `503` with `maps_not_configured` |
| An upstream Google error became `400` with the upstream text folded into `detail` | `502` with `upstream_unavailable` and a sanitized message |
| Framework validation returned a list-shaped `detail` | A handler flattens it to a string `detail` plus `code` and `fields` |
| The client branched on message text | The client branches on `code` |

See [srs-context/controller/validation-error-handling.md](srs-context/controller/validation-error-handling.md).

---

## 11. Carried Forward Unchanged

Not everything changes. These behaviors are deliberately preserved because they work and are already
Google-backed.

| Behavior | Current location | PROJECT2 location |
|----------|------------------|-------------------|
| Google Places API (New) text search with an Austin location bias | `app/map/google_places.py` | `app/map/places.py` |
| Google Routes `computeRoutes` with `TRAFFIC_AWARE`, a `departureTime`, and `TRAFFIC_ON_POLYLINE` | `app/map/google_routes.py` | `app/map/routing.py` |
| Speed reading interval extraction, leg level first with a route-level fallback | `app/map/google_routes.py` | `app/map/routing.py` |
| Encoded polyline decoding | `app/map/polyline.py` | `app/map/polyline.py` |
| BPR link performance and the time-of-day factor | `app/simulation/traffic.py` | `app/simulation/traffic.py` |
| Fare formula, factor breakdown, and minimum fare | `app/pricing/model.py` | `app/pricing/model.py` |
| Weather severity 0 to 3 with time and price multipliers | `app/weather/service.py` | `app/weather/service.py` |
| Centralized coefficients | `app/config/__init__.py` | `app/config/__init__.py` |
| `google.maps.Polyline` per traffic interval and `map.fitBounds` | `src/components/RoutePolylines.tsx` | `src/components/RoutePolylineLayer.tsx` and `src/components/MapBoundsController.tsx` |
| Google traffic speed colors and the slider tint | `src/utils/trafficSegmentColor.ts` | `src/utils/trafficSegmentColor.ts` |
| Debounced re-plan at 180 ms and selection preservation | `src/hooks/useRoutePlan.ts` | `src/hooks/useRoutePlan.ts` |

The Simulated-mode map in the current application is, in effect, a working prototype of the PROJECT2
rendering path. The rewrite generalizes it to both modes rather than replacing it.

---

## Validation Sweep For This Boundary

A PROJECT2 review should confirm that the following strings appear nowhere under `docs/PROJECT2/`
except in this file:

`iframe`, `embed`, `Maps Embed API`, `map_embed_url`, `directions_embed_url`, `map_view`,
`MapEmbedRequest`, `compute_map_view_for_polyline`, `build_map_embed_url`,
`build_directions_embed_url`, `google_embed`, `RouteOverlay`, `mapProjection`, `Reference mode`,
`local reference model`, `app/map/local.py`, `demand`, `demand_score`.

`google_startup_check` is likewise legacy; the target module is `app/map/health.py`.
