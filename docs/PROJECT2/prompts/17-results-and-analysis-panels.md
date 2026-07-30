# Prompt 17 — Results And Analysis Panels

**Wave:** 3 — View
**Depends on:** prompts 13, 14
**Phase:** P1
**Read first:** [00-shared-context.md](00-shared-context.md)

## Read First

1. [00-shared-context.md](00-shared-context.md)
2. [../srs-context/view/results-analysis.md](../srs-context/view/results-analysis.md)
3. [../README.md](../README.md), the `RouteOption`, `PriceFactors`, and `RoadSegment` tables
4. [../srs-context/model/configuration.md](../srs-context/model/configuration.md), "The View Never Imports Coefficients"
5. [../srs-context/view/accessibility.md](../srs-context/view/accessibility.md), non-visual parity for route and segment data

## Objective

Build the presentation of plan results: the route cards, the selected-route analysis panel, the fare
breakdown with its disclaimer, and the segment statistics table. Every number on screen is a
server-computed value rendered, not recomputed.

## Deliverables

| File | Responsibility |
|------|----------------|
| `TrafficSImulation/src/components/RouteOptionList.tsx` | Route cards and selection |
| `TrafficSImulation/src/components/AnalysisPanel.tsx` | Selected-route container |
| `TrafficSImulation/src/components/PriceSummary.tsx` | Fare, `price_factors`, disclaimer |
| `TrafficSImulation/src/components/SegmentTable.tsx` | Per-segment statistics |
| Colocated tests | T-29 (selection wiring), T-38, T-39 |

## Task

1. Implement `RouteOptionList`:
   - Render one card per `RouteOption` showing name, objective, distance, base and adjusted ETA,
     estimated price, and congestion score, each with its unit.
   - Mark the route whose `id` equals `recommended_route_id`. Do not compare `normalized_score`
     values to pick a winner.
   - Selecting a card calls `selectRoute`. Keyboard selection works.
2. Implement `AnalysisPanel` as the selected-route container that hosts `ScenarioControls` (when
   applicable), `PriceSummary`, and `SegmentTable`, plus the mode `notice` and `data_source`.
3. Implement `PriceSummary`:
   - Render `estimated_price` and all five `price_factors` fields.
   - Always show the illustrative-estimate disclaimer (FR-6.5, NFR-7.2).
   - Surface `data_source` (NFR-7.3).
   - Perform no fare arithmetic. A fixture whose `estimated_price` disagrees with its factors must
     still render the response values, which is how T-38 proves the panel does not recompute.
4. Implement `SegmentTable`:
   - One row per `RoadSegment` with every documented field and its unit.
   - Convey traffic severity in text as well as any color cue (NFR-4.6).
5. Use `src/utils/format.ts` for currency, distance, and duration. Do not format by hand at call sites
   with divergent precision.
6. Write T-38 and T-39. Contribute selection-updates-analysis coverage that prompt 19's T-29 will
   exercise end-to-end; pin the panel-level selection wiring here so it cannot regress in isolation.

## Boundaries

- No fare, ETA, weather, or score arithmetic in TypeScript (R3).
- No coefficient import.
- No Maps JavaScript API.
- Do not hide the disclaimer behind a tooltip or a "more info" control. It is always visible when a
  price shows.
- Do not invent a demand score, a profitability metric, or a fourth factor.

## Tests To Write

| Test ID | Level | Target file | Assertion |
|---------|-------|-------------|-----------|
| T-38 | component | `src/components/PriceSummary.test.tsx` | All five factors, currency formatting, disclaimer, `data_source`; no recomputation |
| T-39 | component | `src/components/SegmentTable.test.tsx` | Every segment row with units and textual severity |
| Selection wiring | component | `src/components/RouteOptionList.test.tsx` | Selecting a card updates the analysis inputs |

## Definition Of Done

- [ ] Route cards render the documented primary metrics with units and mark the recommended route by id.
- [ ] Selection updates the analysis panel.
- [ ] `PriceSummary` renders all five factors and the disclaimer without recomputing the fare.
- [ ] `SegmentTable` renders every segment field with units and textual severity.
- [ ] `data_source` and `notice` are visible for the selected route's plan.
- [ ] No file in this package performs domain arithmetic.
- [ ] T-38, T-39, and the selection wiring test pass.
- [ ] `npm test` and `npm run build` pass.

## Handoff

Report the component props, the disclaimer copy you used (quoted from the owning document), and any
results-analysis sentence that required a judgment call about which metrics appear on the card versus
the panel.
