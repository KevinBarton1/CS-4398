# P3 Verification Report — Prompt 24

**Date:** 2026-07-31  
**Verifier:** Prompt 24 congestion heatmap pass  
**Repository:** `TrafficSImulation/` under `CS-4398`

---

## Commands Run And Results

| Command | Result | Notes |
|---------|--------|-------|
| `python -m pytest` | **PASS** — 195 passed, 1 deselected | Includes T-40, T-41, contract/architecture |
| `npm test` | **PASS** — 70 tests in 19 files | Includes T-51 |
| `npm run build` | **PASS** | TypeScript + Vite production bundle |
| `npm run check:bundle` | **PASS** | Under 400 kB gzip budget |

---

## P3 Requirements Closed

| ID | Requirement | Test |
|----|-------------|------|
| FR-8.1 | `POST /api/heatmap` returns congestion cells | T-41 |
| FR-8.2 | Cells render as overlay on existing map | T-51 |
| FR-8.3 | Legend describes intensity scale | T-51 |
| FR-8.4 | Toggle preserves plan and camera | T-51 |

T-24 confirms `PlanResponse` carries no `heatmap` field.

---

## Implemented Contract

### `POST /api/heatmap`

**Request**

```json
{ "hour": 17, "congestion": 56 }
```

| Field | Type | Range | Default |
|-------|------|-------|---------|
| `hour` | int | 0–23 | 17 |
| `congestion` | int | 0–100 | 56 |

Weather is not accepted. Congestion is the only metric; there is no metric selector.

**Response**

| Field | Notes |
|-------|-------|
| `metric` | Always `"congestion"` |
| `rows` / `columns` | 5 × 8 from config |
| `scenario` | Effective hour/congestion; `weather` reported as `0` |
| `bounds` | Austin coverage box union |
| `cells` | 40 cells ordered by row then column, each with `row`, `column`, `value`, `bounds` |
| `notice` | `"Simulated congestion field for the selected departure hour. Planning estimate, not observed traffic."` |

Errors: HTTP 422 `validation_error` only (no upstream calls).

---

## Backend Modules

| Module | Responsibility |
|--------|----------------|
| `app/heatmap/grid.py` | Divides coverage box into axis-aligned cells (geometry only) |
| `app/heatmap/builder.py` | Assigns congestion values from hour + congestion scenario |
| `app/api/heatmap.py` | `HeatmapService` orchestration (separate from `PlanningService`) |
| `app/api/routes.py` | `POST /api/heatmap` route |
| `app/config/__init__.py` | `HEATMAP_ROWS`, `HEATMAP_COLUMNS`, `HEATMAP_COVERAGE_BOUNDS`, blend coefficients |

Value function: weighted blend of scenario congestion, distance from metro center, and departure-hour intensity. Deterministic, clamped 0–100, monotonic in congestion.

---

## Frontend Overlay

| Component | Role |
|-----------|------|
| `HeatmapLayer.tsx` | Draws one `google.maps.Rectangle` per cell beneath route polylines |
| `HeatmapLegend.tsx` | Static intensity scale labelled **Simulated congestion** |
| `RouteMap.tsx` | **Congestion map** toggle; legend appears when overlay is on |
| `useHeatmap.ts` | Fetches `/api/heatmap` when overlay enabled |

**Legend copy:** heading “Simulated congestion”; notice from API; Low (20), Moderate (50), High (80) swatches plus screen-reader summary stating values are planning estimates, not live observations.

Toggle off removes rectangles and legend without refitting bounds or clearing the plan.

---

## README Promotion

`TrafficSImulation/README.md` now documents all four API endpoints and the heatmap request shape. The provisional contract from `heatmaps.md` is implemented as documented with no field changes.

---

## Out Of Scope (Confirmed Absent)

- Demand or profitability metrics
- Heatmap field on `POST /api/plan`
- Second map rendering path
- Raster/tile heatmap rendering

---

## PROJECT2 Complete

Prompts 22 (P1), 23 (P2), and 24 (P3) are verified. All Target rows in traceability for P1–P3 phases are `Complete` except explicitly deferred/partial P1 harness items (T-52 performance, full T-55 manual audit, NFR-3.5 TLS review, NFR-5.8 lint runner).
