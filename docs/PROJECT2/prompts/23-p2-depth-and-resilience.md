# Prompt 23 — P2 Depth And Resilience

**Wave:** 5 — Later phases
**Depends on:** prompt 22 with a clean P1
**Phase:** P2
**Read first:** [00-shared-context.md](00-shared-context.md)

## Read First

1. [00-shared-context.md](00-shared-context.md)
2. [../README.md](../README.md), "Roadmap phases"
3. [../srs-context/requirements/traceability.md](../srs-context/requirements/traceability.md), every row whose Phase is P2
4. The owning context for each P2 requirement you touch: route-planning (FR-1.8, NFR-1.6), traffic-simulation (FR-2.11), map-rendering (FR-3.8, FR-3.9), external-service-boundaries (FR-7.10, NFR-2.6, NFR-3.8), accessibility (NFR-4.7, NFR-4.8), app-composition (NFR-1.7, NFR-6.8)
5. [../srs-context/controller/orchestration.md](../srs-context/controller/orchestration.md), section "Idempotency and Caching"

## Objective

Deliver the P2 depth and resilience slice: place-resolution caching, richer segments, degraded-mode
experience already sketched in P1 where gaps remain, accessibility hardening, one jittered upstream
retry, and the expanded test matrix including an end-to-end flow. Do not start heatmaps.

## Deliverables

| Area | Target modules | Planned tests |
|------|----------------|---------------|
| Place resolution cache | `app/map/places.py` seam, possibly a small cache helper under `app/map/` | T-47 |
| Full-step segment coverage | `app/simulation/segments.py` | T-14 expansion for FR-2.11 |
| Origin and destination markers; polyline click-to-select | `RouteMap.tsx`, `RoutePolylineLayer.tsx` | T-48 |
| One jittered retry on transient upstream failure | `app/map/places.py`, `app/map/routing.py` | T-50 |
| Credential rotation without code change | `app/config/__init__.py` and docs | T-54 extension |
| Reduced motion and automated accessibility audit | `styles.css`, View components | T-55 |
| Bundle size budget | build tooling | T-53 |
| End-to-end plan, select, mode switch | `e2e/plan.spec.ts` | T-44 |

## Task

1. Implement place-resolution caching keyed by normalized query text, at the `GooglePlacesGateway`
   seam, so a scenario-only re-plan issues no additional Places request (FR-1.8, NFR-1.6). Real-Time
   responses are never cached at the plan level. Follow the orchestration document's cache constraints.
2. Expand `SegmentBuilder` so segments cover the full step list (FR-2.11), still importing every
   coefficient from configuration.
3. Add origin and destination markers with labels, and make clicking a polyline select its route
   (FR-3.8, FR-3.9), still on the single Maps JavaScript API path.
4. Add one jittered retry before surfacing a transient upstream failure (FR-7.10, NFR-2.6). Timeouts
   and non-transient errors do not retry endlessly. Keep sanitization intact.
5. Confirm credentials rotate by environment change without a code change (NFR-3.8).
6. Honor `prefers-reduced-motion` (NFR-4.7) and land the automated accessibility audit with no
   critical violations (NFR-4.8).
7. Enforce the bundle size budget under 400 kB gzipped excluding the Maps script (NFR-1.7).
8. Add the end-to-end flow covering plan, select, and mode switch in a real browser (NFR-6.8).
9. Update the traceability Progress column for every P2 row you complete. Leave P3 rows untouched.
10. Keep every P1 non-negotiable: one map path, two credentials, no substituted data, three scenario
    variables, mode policy isolation, configuration isolation, Model-to-Controller import ban.

## Boundaries

- Do not implement `POST /api/heatmap` or any heatmap overlay. That is prompt 24.
- Do not reintroduce Embed API, SVG maps, local geocoding, or `demand`.
- Do not cache Real-Time plan responses.
- Do not add an endpoint the README does not list.

## Tests To Write

| Test ID | Level | Target file | Assertion |
|---------|-------|-------------|-----------|
| T-47 | unit | `tests/test_planning.py` | Place resolution cache prevents repeat Places calls on scenario-only re-plan |
| T-48 | component | `src/components/RouteMap.test.tsx` | Markers render; polyline click selects |
| T-50 | unit | `tests/test_google_routes.py` (and Places equivalent) | One jittered retry before surfacing a transient failure |
| T-53 | e2e / CI | build tooling | Bundle under 400 kB gzipped excluding Maps |
| T-44 | e2e | `e2e/plan.spec.ts` | Plan, select, and switch mode in a real browser |
| T-55 | e2e | accessibility harness | Contrast, reduced motion, automated audit |

## Definition Of Done

- [x] Every P2 Target row you claim has a passing planned test and an updated Progress cell.
- [x] Scenario-only re-plans issue no additional Places requests.
- [x] Segments cover the full step list.
- [x] Markers and polyline click-to-select work on the single map path.
- [x] Transient upstream failures see exactly one jittered retry.
- [x] Reduced motion is honored; the automated audit reports no critical violations.
- [x] Bundle budget holds.
- [x] The e2e flow passes.
- [x] `python -m pytest`, `npm test`, and `npm run build` pass.
- [x] No P3 behavior was introduced.

## Handoff

Report the P2 rows completed, the cache key design, the retry policy, the e2e command, and any P2
requirement you could not close with the reason.

Attach [23-p2-verification-report.md](23-p2-verification-report.md).
