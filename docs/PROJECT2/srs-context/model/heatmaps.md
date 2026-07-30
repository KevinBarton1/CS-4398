# Model Context — Congestion Heatmap (P3)

**Layer:** Model  
**Target modules:** `app/heatmap/grid.py`, `app/heatmap/builder.py` (P3 only)  
**Related:** [README.md](../../README.md), [domain-contracts.md](domain-contracts.md), [route-planning.md](route-planning.md), [traffic-simulation.md](traffic-simulation.md), [weather-scenarios.md](weather-scenarios.md), [configuration.md](configuration.md)

## Status

This is a roadmap document for phase P3. Nothing described here is delivered behavior, and nothing in it is
part of P1 or P2.

| Statement | Detail |
|-----------|--------|
| No current behavior | There is no heatmap in the P1 product. No endpoint serves heatmap data, no response field carries it, and no component renders it |
| Unwired in the reference implementation | `app/heatmap/` exists in the current code under `TrafficSImulation/`, but nothing imports it and no route calls it. It is dead code that the rewrite does not carry forward as-is |
| Provisional contract | The request and response shapes below are a proposal. They are the only part of PROJECT2 not locked, and they may change when P3 is planned in detail |
| Single metric | Congestion is the only heatmap metric. There is no metric selector and no alternative metric |
| Not in the plan response | Heatmap data would be served by its own endpoint. `POST /api/plan` would not gain a heatmap field |

Every requirement in this file therefore reads as an intention for P3, not as a description of the product.

## Purpose

Describe the design a congestion heatmap would follow if P3 is taken up: a coarse grid of geographic cells,
each carrying a congestion intensity derived from the same scenario the planner uses, rendered as a vector
overlay layer on the Google Maps JavaScript API map that already displays routes.

## Requirements

| ID | Requirement | Status | Phase |
|----|-------------|--------|-------|
| FR-8.1 | Serve congestion intensity for a grid of Austin-area cells from `POST /api/heatmap` for a submitted scenario, giving every cell an explicit geographic bounding box and reusing the scenario variables rather than introducing heatmap-specific inputs | Target | P3 |
| FR-8.2 | Render cells as a vector overlay layer on the existing map | Target | P3 |
| FR-8.3 | Show a legend mapping color intensity to a congestion range and labelling the overlay as a simulated planning estimate | Target | P3 |
| FR-8.4 | Let the user turn the overlay on and off without losing the route display | Target | P3 |
| NFR-1.1 | A heatmap request completes within 500 milliseconds, since it makes no upstream call | Target | P1 |
| NFR-5.2 | Heatmap grid mathematics stay separate from the response builder | Target | P1 |
| NFR-6.2 | Cell values are deterministic for a fixed scenario | Target | P1 |
| — | Any heatmap metric other than congestion | Out of scope | — |
| — | Raster or image-tile heatmap rendering | Out of scope | — |
| — | A heatmap field on the plan response | Out of scope | — |

The `FR-8` rows are P3 because the feature itself is P3. The three `NFR` rows carry their canonical P1
phase: they are standing quality requirements that already govern the P1 product, and the rows above
state how this P3 feature must satisfy them when it lands. Nothing in this file is P1 work.

## Metric

Congestion, expressed as an integer intensity from 0 to 100, is the only metric.

| Aspect | Decision |
|--------|----------|
| Metric | Congestion intensity, 0–100 |
| Inputs | `Scenario.hour` and `Scenario.congestion` |
| Not an input | `Scenario.weather`, which affects travel time and fare but not the spatial congestion field |
| Relationship to routes | Independent. The heatmap describes an area; `RouteOption.congestion_score` describes one route |
| Relationship to `traffic_intervals` | Independent. Traffic intervals are Google readings along a polyline; heatmap cells are simulated area values |

A single metric keeps the legend readable, keeps the request shape small, and avoids a mode selector that
would need its own validation, its own error code, and its own set of formulas.

## Grid Design

A congestion field over a metro area needs to be coarse enough to read at a glance and fine enough to show
that downtown differs from the outskirts. The proposal is a small, fixed, axis-aligned lattice.

| Property | Proposed value | Rationale |
|----------|----------------|-----------|
| Rows | 5 | Readable at the default zoom without hiding the route beneath it |
| Columns | 8 | Matches the roughly 8-to-5 aspect ratio of the Austin service area |
| Cell count | 40 | Small enough to render as individual vector shapes with no clustering |
| Coverage | The Austin service area, a box around 30.2672, -97.7431 sized to the 35 km bias radius | Same service area the planner uses |
| Cell shape | Rectangle in latitude and longitude | Axis-aligned cells need no projection maths and tile the box exactly |
| Indexing | `row` 0 at the north edge increasing south, `column` 0 at the west edge increasing east | Reading order matches the screen |
| Value range | Integer 0–100 | Same scale as `Scenario.congestion`, so the legend needs no unit conversion |
| Determinism | The same scenario always yields the same 40 values | No clock and no randomness in the value function |

Row and column counts, and the service-area box, would live in `app/config/__init__.py` alongside every other
coefficient, so the grid resolution is tunable without touching the grid module.

Cells would tile the coverage box with no gaps and no overlaps: each cell's `north` is the previous row's
`south`, and each cell's `west` is the previous column's `east`. Adjacent cells sharing an edge value is
intentional and keeps the tiling exact.

### Cell shape

| Field | Type | Unit | Range | Meaning |
|-------|------|------|-------|---------|
| `row` | int | index | 0 to `rows - 1` | Grid row, 0 at the north edge |
| `column` | int | index | 0 to `columns - 1` | Grid column, 0 at the west edge |
| `value` | int | percent | 0–100 | Congestion intensity for the cell |
| `bounds` | `RouteBounds` | degrees | `north >= south`, `east >= west` | The cell's geographic extent |

`bounds` reuses the existing `RouteBounds` value object from [domain-contracts.md](domain-contracts.md)
rather than introducing a second box type. Carrying explicit bounds per cell, instead of only row and column
indices, means the View never reconstructs geography from indices and never needs to know the grid dimensions
to draw a cell.

### Value function

The shape a P3 value function would take, stated as intent rather than as a formula to implement now:

| Term | Role |
|------|------|
| Scenario congestion baseline | The dominant term, so moving the congestion control moves the whole field |
| Distance from the metro center | Reduces intensity toward the edges, so the core reads busier than the outskirts |
| Departure hour | Shifts the field, so a peak hour reads busier than an overnight hour |

Whatever the final terms are, three properties are required: values stay inside 0–100 after clamping, a
higher `Scenario.congestion` never lowers a cell value, and the output is a pure function of the scenario
with no clock read and no randomness.

## Provisional `POST /api/heatmap`

Provisional. Not implemented in P1 or P2.

### Request

```json
{
  "hour": 17,
  "congestion": 56
}
```

| Field | Type | Required | Constraint | Default |
|-------|------|----------|------------|---------|
| `hour` | int | no | 0–23 | 17 |
| `congestion` | int | no | 0–100 | 56 |

The request reuses two of the three scenario variables with the same names, ranges, and defaults as
`POST /api/plan`. It introduces no new variable. `weather` is not accepted, because weather does not enter the
congestion field.

The endpoint would take no origin, no destination, and no bounds. The grid covers the fixed service area, so
the request stays a pure scenario query.

### Response

```json
{
  "metric": "congestion",
  "rows": 5,
  "columns": 8,
  "scenario": { "hour": 17, "weather": 0, "congestion": 56 },
  "bounds": { "north": 30.58, "south": 29.95, "east": -97.38, "west": -98.11 },
  "cells": [
    {
      "row": 0,
      "column": 0,
      "value": 41,
      "bounds": { "north": 30.58, "south": 30.454, "east": -98.019, "west": -98.11 }
    }
  ],
  "notice": "Simulated congestion field for the selected departure hour. Planning estimate, not observed traffic."
}
```

| Field | Type | Notes |
|-------|------|-------|
| `metric` | string | Always `congestion` |
| `rows` | int | Grid row count |
| `columns` | int | Grid column count |
| `scenario` | `Scenario` | Effective values; `weather` reported as 0 because it is not an input |
| `bounds` | `RouteBounds` | The union of every cell's bounds, equal to the coverage box |
| `cells` | `HeatmapCell[]` | `rows * columns` elements, ordered by `row` then `column` |
| `notice` | string | Provenance sentence, non-empty |

Errors would use the same envelope and the same codes as every other endpoint. Only `validation_error` with
HTTP 422 applies, since the endpoint makes no upstream call and so cannot produce `maps_not_configured`,
`upstream_unavailable`, or `upstream_timeout`.

### Module split

| Module | Responsibility |
|--------|----------------|
| `app/heatmap/grid.py` | Geometry only: divide the coverage box into `rows` by `columns` cells and return each cell's indices and `RouteBounds`. No scenario knowledge |
| `app/heatmap/builder.py` | Assign a `value` to each cell from the effective scenario and assemble the response model |

Splitting geometry from valuation lets the tiling be tested against exact latitude and longitude arithmetic
while the value function is tested against monotonicity, with neither test needing the other.

## Rendering (View intent)

The heatmap would render on the same Google Maps JavaScript API map instance that already draws route
polylines, as a vector overlay layer.

| Aspect | Intent |
|--------|--------|
| Mechanism | One vector shape per cell, or an equivalent data layer of rectangular features, drawn on the existing map |
| Geometry source | Each cell's own `bounds`; the View performs no projection arithmetic |
| Not an image | No raster tile, no bitmap, no ground-image overlay, and no separate rendering surface |
| Layering | Beneath the route polylines, so the recommended route stays readable |
| Styling | Fill opacity scaled by `value`, with no stroke, so the road network below stays visible |
| Toggle | Turning the overlay off removes the shapes and leaves the routes, the markers, and the viewport untouched |
| Legend | A static scale mapping intensity bands to fill opacity, labelled as a simulated planning estimate |
| Accessibility | The legend and a text summary of the field carry the same information for non-visual use |

Vector shapes are the choice because the grid is only 40 cells, the map already runs the JavaScript API for
routes, and vector cells stay crisp through zoom and pan with no tile pipeline. There is one map rendering
path in the product, and a P3 heatmap would use it rather than adding a second.

## Acceptance Criteria

These would apply when P3 is delivered. None applies to P1 or P2.

- [ ] `POST /api/heatmap` returns `rows * columns` cells, ordered by `row` then `column`.
- [ ] Every cell carries `row`, `column`, `value`, and a `bounds` object with all four edges.
- [ ] Cells tile the coverage box with no gap and no overlap, and the response `bounds` equals the union of every cell's bounds.
- [ ] Every `value` is an integer between 0 and 100 inclusive.
- [ ] Raising `congestion` never lowers any cell value.
- [ ] Two identical requests return identical cell values.
- [ ] `metric` is always `congestion`, and the response carries no other metric and no metric selector.
- [ ] Out-of-range `hour` or `congestion` returns `validation_error` with HTTP 422.
- [ ] `POST /api/plan` gains no heatmap field.
- [ ] The overlay renders as vector cells on the existing map, beneath the route polylines.
- [ ] Toggling the overlay off leaves routes, markers, and viewport unchanged.
- [ ] The legend is present whenever the overlay is on and labels the values as simulated planning estimates.
- [ ] `app/heatmap/grid.py` contains no scenario logic and `app/heatmap/builder.py` contains no latitude or longitude arithmetic.

## Planned Tests

All P3. None of these tests would exist in P1 or P2.

| Test ID | Level | Target file | Assertion |
|---------|-------|-------------|-----------|
| T-40 | unit | `tests/test_heatmap.py` | The grid returns `rows * columns` cells that tile the coverage box exactly, with shared edges and no overlap; cell values stay within 0–100 and no value decreases when `congestion` rises from 10 to 90; and two identical scenarios produce identical cell values, confirming no clock or randomness |
| T-41 | api | `tests/test_api.py` | `POST /api/heatmap` returns `metric` `congestion` with the documented shape, and an out-of-range `hour` returns 422 |
| T-24 | api | `tests/test_contracts.py` | A successful `POST /api/plan` response contains no heatmap field |
| T-51 | component | `src/components/HeatmapLayer.test.tsx` | One vector cell is drawn per response cell using that cell's bounds, and toggling off removes the cells while leaving route polylines mounted |

## Agent Implementation Notes

- Do not implement any of this during P1 or P2 work. If a task appears to require a heatmap, the requirement
  is misfiled; check [README.md](../../README.md) first.
- Do not wire the existing `app/heatmap/` code from the current implementation into the rewrite. It carries a
  metric selector and formulas that PROJECT2 does not have. Treat it as reference material for the grid idea
  only.
- Keep `rows`, `columns`, the coverage box, and every value coefficient in `app/config/__init__.py`.
- `app/heatmap/grid.py` must import only geometry types. It must not import `app/simulation/`, `app/map/`, or
  `app/pricing/`.
- Reuse `RouteBounds` for cell bounds. Do not introduce a `CellBounds` type.
- Do not add a heatmap field to `PlanResponse`, and do not add a heatmap flag to `PlanRequest`. The heatmap is
  its own endpoint so that a heatmap failure can never degrade a plan.
- When P3 is planned in detail, replace the provisional contract in this file and in
  [README.md](../../README.md) in the same change, and add the cell type to
  [domain-contracts.md](domain-contracts.md) and `src/types.ts` together.
