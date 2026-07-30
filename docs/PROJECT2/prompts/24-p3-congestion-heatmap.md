# Prompt 24 — P3 Congestion Heatmap

**Wave:** 5 — Later phases
**Depends on:** prompt 23 with a clean P2
**Phase:** P3
**Read first:** [00-shared-context.md](00-shared-context.md)

## Read First

1. [00-shared-context.md](00-shared-context.md)
2. [../srs-context/model/heatmaps.md](../srs-context/model/heatmaps.md) — read all of it
3. [../README.md](../README.md), the provisional `POST /api/heatmap` endpoint and the statement that `demand` is out of scope
4. [../srs-context/requirements/traceability.md](../srs-context/requirements/traceability.md), FR-8.*
5. [../srs-context/view/map-rendering.md](../srs-context/view/map-rendering.md), so the overlay stays on the existing map instance
6. [../srs-context/model/configuration.md](../srs-context/model/configuration.md), the Heatmap (P3) constants

## Objective

Deliver the congestion heatmap: a `POST /api/heatmap` endpoint that returns congestion cells for a
scenario, a grid overlay on the existing Maps JavaScript API instance, and a legend. The metric is
congestion only. Demand and profitability are out of scope.

## Deliverables

| File | Responsibility |
|------|----------------|
| `TrafficSImulation/app/heatmap/grid.py` | Grid geometry over the Austin service area |
| `TrafficSImulation/app/heatmap/builder.py` | `HeatmapBuilder.build(scenario, metric) -> HeatmapGrid` |
| `TrafficSImulation/app/api/` heatmap route and schemas | Provisional contract for `POST /api/heatmap` |
| View overlay component and legend | Renders on the existing `RouteMap` instance |
| Tests | T-40, T-41, T-51 |

## Task

1. Define the P3 coefficients in `app/config/__init__.py` if prompt 02 deferred them:
   `HEATMAP_ROWS`, `HEATMAP_COLUMNS`, `HEATMAP_COVERAGE_BOUNDS`.
2. Implement `grid.py` and `HeatmapBuilder` for the congestion metric only. Reject or ignore any other
   metric name rather than inventing demand or profitability behavior.
3. Add `POST /api/heatmap` with the provisional contract from the heatmaps document and the README.
   Follow the same validation, error-envelope, and dependency-injection patterns as the P1 endpoints.
   Put orchestration in its own service class under `app/api/`, not as a branch inside
   `PlanningService.plan()`.
4. Render cells as an overlay on the existing map instance. Do not create a second map. Do not switch
   map technologies.
5. Add a legend that describes the intensity scale (FR-8.3).
6. Toggling the overlay preserves the current plan and camera (FR-8.4).
7. Write T-40, T-41, and T-51. Update the contract and architecture tests so the new endpoint and
   schemas are pinned without weakening P1 rules.
8. Update the traceability Progress column for FR-8.1 through FR-8.4.

## Boundaries

- Congestion is the only heatmap metric. Do not add demand or profitability modes.
- Do not introduce a second map path.
- Do not put heatmap logic into `PlanningService.plan()`.
- Do not present heatmap values as live observations; they are simulated planning estimates, and the
  UI must say so.
- Do not expand the endpoint set beyond what the README lists.

## Tests To Write

| Test ID | Level | Target file | Assertion |
|---------|-------|-------------|-----------|
| T-40 | unit | `tests/test_heatmap.py` | Grid values respond to congestion and hour |
| T-41 | api | `tests/test_api.py` | Heatmap endpoint shape and error envelope |
| T-51 | component | `src/components/HeatmapLayer.test.tsx` | Overlay renders on the existing map and toggles cleanly without disturbing plan or camera |

## Definition Of Done

- [ ] `POST /api/heatmap` returns congestion cells for a scenario under the provisional contract.
- [ ] Cells render as an overlay on the existing map instance.
- [ ] A legend describes the intensity scale.
- [ ] Toggling the overlay preserves the plan and camera.
- [ ] No demand or profitability metric exists.
- [ ] T-40, T-41, and T-51 pass.
- [ ] Contract and architecture tests still pass.
- [ ] Traceability Progress for FR-8.1 through FR-8.4 reflects passing tests.
- [ ] `python -m pytest`, `npm test`, and `npm run build` pass.

## Handoff

Report the final heatmap contract as implemented, the overlay component name, the legend copy, and
any provisional-contract decision that needs to be promoted into [../README.md](../README.md).
