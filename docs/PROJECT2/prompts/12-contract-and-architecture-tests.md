# Prompt 12 — Contract And Architecture Tests

**Wave:** 2 — Controller
**Depends on:** prompts 01 through 11
**Phase:** P1
**Read first:** [00-shared-context.md](00-shared-context.md)

## Read First

1. [00-shared-context.md](00-shared-context.md)
2. [../srs-context/architecture/architecture-overview.md](../srs-context/architecture/architecture-overview.md), sections "Dependency Rules" and "Acceptance Criteria"
3. [../srs-context/controller/api-contracts.md](../srs-context/controller/api-contracts.md)
4. [../README.md](../README.md), the locked response field sets
5. [../srs-context/requirements/traceability.md](../srs-context/requirements/traceability.md), the test catalog entries for T-24, T-45, T-46, T-56, T-57
6. [../migration-from-current-implementation.md](../migration-from-current-implementation.md), so the architecture tests know which legacy paths must stay gone

## Objective

Lock the contracts and the dependency rules with tests that fail the moment either drifts. This
package writes no production code. It is the mechanical enforcement of R1 through R8 and of the
locked field sets, so that Wave 3 and later cannot silently violate them.

## Deliverables

| File | Responsibility |
|------|----------------|
| `TrafficSImulation/tests/test_contracts.py` | T-24 |
| `TrafficSImulation/tests/test_architecture.py` | T-45, T-46, T-56 |
| `TrafficSImulation/tests/test_google_live.py` | T-57, marked opt-in and deselected by default |

## Task

1. Write T-24 in `tests/test_contracts.py`:
   - Pin the exact top-level `PlanResponse` field set against the README.
   - Pin the exact per-route `RouteOption` field set, including nested `PriceFactors`, `RoadSegment`,
     `TrafficInterval`, and `RouteBounds`.
   - Pin `MapConfigResponse` and `HealthResponse`.
   - Pin the error envelope.
   - When TypeScript types exist (after prompt 13), extend the test so a divergence between
     `app/api/models.py` and `src/types.ts` fails the suite (NFR-6.4). If TypeScript types do not yet
     exist, structure the test with a clear extension point and note it in the handoff; prompt 13 will
     complete the mirror assertion.
2. Write T-45 in `tests/test_architecture.py`:
   - Walk the import graph of every module under `app/map/`, `app/simulation/`, `app/pricing/`,
     `app/weather/`, and `app/heatmap/` and assert there is no edge into `app/api/` or `main` (R1).
   - Assert `app/api/planning.py` contains no numeric coefficient literal (R2).
   - Assert the backend package set is exactly `api`, `map`, `simulation`, `pricing`, `weather`,
     `heatmap`, `config` (NFR-5.4).
   - Assert none of the flat legacy paths exist on disk or as import targets:
     `app/routes.py`, `app/models.py`, `app/map_service.py`, `app/traffic_simulator.py`,
     `app/pricing_model.py`, `app/weather_service.py`, `app/heatmap.py` (NFR-5.6).
   - Assert `app/api/planning.py` imports only the documented modules, no transport library, and no
     flat legacy path.
3. Write T-46: a repository scan asserting that the literals `realtime` and `simulated` appear in
   production code only inside `app/api/mode_policy.py` (and the Pydantic literal constraint in
   `app/api/models.py` if you treat that as schema rather than branching). Document the allowlist in
   the test. Tests and docs are excluded from the scan.
4. Write T-56: a scan asserting that `google.maps` appears in the View only inside
   `MapConfigProvider.tsx`, `RouteMap.tsx`, `RoutePolylineLayer.tsx`, and `MapBoundsController.tsx`.
   If those files do not yet exist, structure the test so it will fail closed when they arrive, and
   note the deferred assertion in the handoff; prompt 15 will make it pass.
5. Write T-57 as an opt-in live-credential probe under the marker registered in prompt 01. It must not
   run in the default suite. Document the environment variable or marker a developer uses to opt in.
6. Run the full backend suite and confirm every architecture and contract test fails for the right
   reason when you temporarily break the rule, then passes when restored. Record one such
   negative-check per test file in the handoff.

## Boundaries

- Write no production code. If a test reveals a violation already in the tree, fix the smallest
  violation that unblocks the rule and report it; do not redesign a package.
- Do not weaken a rule to make a test pass. Adjust the allowlist only when the specification
  explicitly permits the exception, and quote the permission.
- Do not add a live Google call to the default suite.

## Tests To Write

| Test ID | Level | Target file | Assertion |
|---------|-------|-------------|-----------|
| T-24 | api | `tests/test_contracts.py` | Exact response field sets; Python and TypeScript mirror when available |
| T-45 | unit | `tests/test_architecture.py` | Import-graph rules, package set, absence of legacy paths, planning import allowlist |
| T-46 | unit | `tests/test_architecture.py` | Mode literals confined to the policy module |
| T-56 | unit | `tests/test_architecture.py` | Maps JavaScript API usage confined to the four map components |
| T-57 | unit | `tests/test_google_live.py` | Opt-in live-credential probe, excluded by default |

## Definition Of Done

- [ ] T-24 pins every locked response field set.
- [ ] T-45 enforces R1, R2, NFR-5.4, and NFR-5.6.
- [ ] T-46 enforces R4 with a documented allowlist.
- [ ] T-56 is in place, either passing against the map components or structured to fail closed when they arrive.
- [ ] T-57 is marked opt-in and is deselected by the default suite.
- [ ] A deliberate one-line violation of each rule fails the corresponding test.
- [ ] `python -m pytest` passes with T-57 deselected.

## Handoff

Report which assertions are fully live versus deferred to Wave 3, the allowlists used by T-46 and
T-56, the opt-in mechanism for T-57, and the negative checks you ran.
