# Prompt 07 — Route Scoring

**Wave:** 1 — Model
**Depends on:** prompts 01, 02
**Phase:** P1
**Read first:** [00-shared-context.md](00-shared-context.md)

## Read First

1. [00-shared-context.md](00-shared-context.md)
2. [../srs-context/model/route-planning.md](../srs-context/model/route-planning.md), the ranking section
3. [../srs-context/model/configuration.md](../srs-context/model/configuration.md), `ROUTE_SCORE_WEIGHTS`
4. [../README.md](../README.md), the `RouteOption` table and the statement that `demand` is out of scope
5. [../srs-context/architecture/class-diagram.md](../srs-context/architecture/class-diagram.md), `RouteScorer`

## Objective

Build `RouteScorer`, the Model service that normalizes a set of route candidates, assigns each its
`normalized_score`, and recommends the lowest-scoring route. Lower is better. The weight vector has
exactly three keys; there is no fourth term.

## Deliverables

| File | Responsibility |
|------|----------------|
| `TrafficSImulation/app/simulation/scoring.py` | `RouteScorer.score(...)`, `RouteScorer.recommend(...)` |
| `TrafficSImulation/tests/test_scoring.py` | T-17 |

## Task

1. Implement `RouteScorer` with two public methods:
   - `score(routes) -> list[RouteOption]` (or the internal shape orchestration will pass) that assigns
     every route its `normalized_score` using `ROUTE_SCORE_WEIGHTS` with keys `time`, `distance`, and
     `congestion` summing to 1.0.
   - `recommend(routes) -> str` that returns the `id` of the route with the lowest `normalized_score`.
2. Normalize each dimension across the set before weighting, so a single-route set receives a well-
   defined score rather than a division by zero. Document the single-route behavior in the test.
3. Tie-breaking: when two routes share the lowest score, pick the one that appears first in the input
   list. State the rule in a test so it cannot silently change.
4. Import `ROUTE_SCORE_WEIGHTS` from configuration. Do not redeclare the weights, and do not introduce
   a fourth term under any name. `demand` is out of scope.
5. Write T-17 covering:
   - a three-route set where the recommended id is the lowest-scoring one;
   - a single-route set that still produces a finite score and recommends that route;
   - a tie that resolves to the earlier input;
   - an assertion that the weights in use are exactly the three documented keys.

## Boundaries

- No HTTP, no FastAPI, no `app/api/` import (R1).
- Do not assign `color`, `name`, or `objective`. Those are index-based presentation values assigned by
  `PlanningService`.
- Do not introduce a `demand` term, a fourth weight, or a heatmap metric.
- Do not round `normalized_score` beyond the four decimal places the README specifies.

## Tests To Write

| Test ID | Level | Target file | Assertion |
|---------|-------|-------------|-----------|
| T-17 | unit | `tests/test_scoring.py` | Normalization, recommendation of the lowest score, single-route case, and tie-breaking |

## Definition Of Done

- [ ] `recommend` returns the id of the lowest-scoring route.
- [ ] A single-route set produces a finite score and recommends that route.
- [ ] Ties resolve to the earlier input, and a test pins that rule.
- [ ] `ROUTE_SCORE_WEIGHTS` is imported from configuration and has exactly three keys.
- [ ] No `demand` term exists anywhere in the module.
- [ ] T-17 passes with literal expected scores where practical.
- [ ] `python -m pytest` passes.

## Handoff

Report the public signatures, the normalization formula you implemented in one short paragraph, the
tie-breaking rule, and the fixture routes T-17 uses so prompt 10 can reuse them for
`recommended_route_id` assertions.
