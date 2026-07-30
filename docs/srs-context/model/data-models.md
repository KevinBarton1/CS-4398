# Model Context — Data Models

**Layer:** Model  
**Codebase:** `TrafficSImulation/app/models.py`, `TrafficSImulation/src/types.ts`  
**Related:** [simulation.md](simulation.md), [controller/api-endpoints.md](../controller/api-endpoints.md)

## Purpose

Define the domain entities and API contract shapes shared between backend and frontend. All route planning inputs and outputs flow through these types.

## SRS Requirements

| ID | Requirement | Status |
|----|-------------|--------|
| FR-2.4 | Store/calculate segment length, lanes, speed limit, average speed, volume, congestion | Implemented in `RoadSegment` |
| FR-2.6 | Distinguish API data from simulated data | `data_source` on `RouteOption` |
| FR-4.2 | Label simulated values | `data_source`, response `notice` |
| FR-6.4 | Display major pricing factors | `PriceFactors` / `factors` dict |

## Backend Models (`app/models.py`)

### PlanRequest (Pydantic)

Inbound POST body for `/api/plan`. Validated at controller boundary.

| Field | Type | Default | Constraints | SRS mapping |
|-------|------|---------|-------------|-------------|
| `origin` | string | — | min 1, max 120 chars | FR-1.1 |
| `destination` | string | — | min 1, max 120 chars | FR-1.2 |
| `mode` | string | `"simulated"` | `"simulated"` or `"realtime"` | FR-4.1 |
| `heatmap` | string | `"congestion"` | congestion, demand, profitability, off | FR-3.1–3.3, FR-3.6 |
| `hour` | int | 17 | 0–23 | FR-5.1 |
| `weather` | int | 1 | 0–3 | FR-5.2 |
| `congestion` | int | 56 | 0–100 | FR-5.3 |
| `demand` | int | 68 | 0–100 | FR-5.4 |

Out-of-range values return HTTP 422 from FastAPI (FR-5 alternate flow: reject invalid input).

### Point (dataclass)

```python
x: float  # SVG/map coordinate
y: float
```

Used for route polyline geometry on the stylized Austin map.

### RoadSegment (dataclass)

Per-segment statistics for the details panel (FR-2.4, FR-2.5).

| Field | Description |
|-------|-------------|
| `name` | Road name (e.g., Lamar Blvd, I-35) |
| `length_miles` | Segment length |
| `lanes` | Lane count |
| `speed_limit_mph` | Posted limit |
| `average_speed_mph` | Computed from BPR-adjusted time |
| `volume_vehicles_hour` | Flow (veh/hr) |
| `congestion` | 0.0–1.0 fraction |
| `capacity_vehicles_hour` | lanes × BASE_LANE_CAPACITY |
| `free_flow_minutes` | Uncongested travel time |
| `adjusted_minutes` | BPR-adjusted travel time |

### RouteOption (dataclass)

One of three objective-based alternatives.

| Field | Description | SRS |
|-------|-------------|-----|
| `id` | e.g., `route-1` | — |
| `name` | Fastest / Balanced / Low traffic | Route comparison panel |
| `color` | Hex stroke color for map | — |
| `distance_miles` | Total distance | FR-2.1 |
| `base_eta_minutes` | Pre-modifier ETA | FR-2.2 |
| `adjusted_eta_minutes` | After weather, time, BPR | FR-2.3 |
| `estimated_price` | Upfront estimate | FR-6.3 |
| `congestion_score` | 0–100 | Route comparison |
| `demand_score` | 0–100 | Route comparison |
| `objective` | Human-readable routing goal | — |
| `normalized_score` | Weighted comparison score | — |
| `points` | List of `Point` | Map overlay |
| `segments` | List of `RoadSegment` | FR-2.5 |
| `factors` | Pricing breakdown dict | FR-6.4 |
| `data_source` | `"Simulated scenario"` or `"Local reference model"` | FR-2.6, FR-4.2 |

## Frontend Types (`src/types.ts`)

Mirror backend response shapes for strict TypeScript:

- `Mode`: `"realtime" | "simulated"`
- `HeatmapMode`: `"congestion" | "demand" | "profitability" | "off"`
- `Segment`, `PriceFactors`, `RouteOption`, `PlanResult`, `Scenario`

### PlanResult (API response)

| Field | Description |
|-------|-------------|
| `origin`, `destination` | Resolved place names |
| `mode` | Active planning mode |
| `hour`, `congestion`, `demand` | Echoed scenario values |
| `weather` | `{ label, severity, time_multiplier, price_multiplier }` |
| `routes` | `RouteOption[]` (always 3 when successful) |
| `recommended_route_id` | Lowest `normalized_score` |
| `heatmap` | `{ mode, cells[] }` |
| `notice` | User-facing data-source disclaimer |

## Acceptance Criteria

- [ ] Request validation rejects empty origin/destination and out-of-range scenario integers (422).
- [ ] Every successful plan response includes exactly 3 routes with non-empty `segments`.
- [ ] `factors.unrounded_total` reproduces `estimated_price` when multipliers are applied (see pricing tests).
- [ ] Frontend `types.ts` stays in sync with backend response keys.
- [ ] `data_source` and `notice` clearly indicate simulated vs. reference data (NFR-6.3).

## Constraints

- No persistence of user location or route history (NFR-5.1, NFR-5.2).
- Origin and destination must resolve to different places (`ValueError` → 400).
- Class names PascalCase; Python functions snake_case; TS types PascalCase, variables camelCase (SRS 6.2, AGENTS.md).

## Agent Implementation Notes

When adding fields:

1. Add to Pydantic `PlanRequest` or response assembly in `routes.py`.
2. Update dataclasses if domain entities change.
3. Update `src/types.ts` and any component consuming the field.
4. Add tests in `tests/test_api.py` and/or `tests/test_backend.py`.
