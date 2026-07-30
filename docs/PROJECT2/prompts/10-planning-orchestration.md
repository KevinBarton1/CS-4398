# Prompt 10 — Planning Orchestration

**Wave:** 2 — Controller
**Depends on:** prompts 01 through 09
**Phase:** P1
**Read first:** [00-shared-context.md](00-shared-context.md)

## Read First

1. [00-shared-context.md](00-shared-context.md)
2. [../srs-context/controller/orchestration.md](../srs-context/controller/orchestration.md) — read all of it
3. [../srs-context/architecture/architecture-overview.md](../srs-context/architecture/architecture-overview.md), section "Request And Data Flow"
4. [../srs-context/architecture/class-diagram.md](../srs-context/architecture/class-diagram.md), Key Collaborations
5. [../README.md](../README.md), the `RouteOption` table and the plan response shape

## Objective

Build `PlanningService`, the single coordinator that turns a validated `PlanRequest` into a
`PlanResponse`. Orchestration decides call order, mode branching through the policy, and error
propagation. It never performs arithmetic that belongs to the Model.

## Deliverables

| File | Responsibility |
|------|----------------|
| `TrafficSImulation/app/api/planning.py` | `PlanningService.plan(request) -> PlanResponse` |
| `TrafficSImulation/app/api/dependencies.py` | Constructors that wire gateways and services for injection |
| `TrafficSImulation/tests/test_planning.py` | T-23 |

## Task

1. Implement `PlanningService` with the constructor signature from the orchestration document:
   `places`, `routing`, `weather`, `segments`, `pricing`, `scorer`, `settings`. Every collaborator
   arrives through the constructor.
2. Implement `async def plan(self, request: PlanRequest) -> PlanResponse` performing the eight
   workflow steps in the documented order:
   1. Resolve the mode policy through `resolve_mode_policy`. This is the only mode-string inspection
      the service performs, and it is a single call.
   2. Build the effective `Scenario` from the policy.
   3. Resolve origin and destination concurrently with `asyncio.gather`. Reject identical resolutions
      with `SameOriginDestinationError` before any Routes call, using
      `PLACE_MATCH_TOLERANCE_DEGREES`.
   4. Compute route alternatives through the Routes gateway with the policy's departure time,
      alternatives flag, and traffic preference.
   5. Resolve the weather state from the effective scenario's severity.
   6. For each raw route: derive `congestion_score` from the effective congestion and route index
      using `ROUTE_CONGESTION_INDEX_STEP` and `ROUTE_CONGESTION_FLOOR`; build segments; ask the policy
      for `adjusted_eta_minutes`; estimate the fare; compute `bounds` with `bounds_for_points`;
      assign `id` as `route-N`, and `name`, `objective`, and `color` from the configuration tuples by
      index.
   7. Score and rank through `RouteScorer`; set `recommended_route_id` to the lowest score.
   8. Assemble the response: `union_bounds` into `map_bounds`, attach the policy's `notice` and
      `scenario_applied`, echo resolved display names, and return a fully populated `PlanResponse`.
3. Keep `plan()` short enough to read in one screen. Extract private helpers such as
   `_resolve_endpoints`, `_build_route_option`, and `_assemble_response` rather than growing one long
   body.
4. Build `RouteOption` objects as Pydantic models directly. Do not assemble dicts and patch keys
   afterward.
5. Do not catch gateway failures to soften them. Let typed domain errors escape to the handlers.
6. Wire constructors in `app/api/dependencies.py` so tests substitute stubs without patching module
   globals. Do not put construction logic in `main.py`.
7. Restrict imports in `planning.py` to the documented set: models, mode policy, the two gateways,
   bounds helpers, `SegmentBuilder`, `RouteScorer`, `PricingModel`, `WeatherService`, and `Settings`.
   Do not import `app/simulation/traffic.py`, `app/map/polyline.py`, `httpx`, or any flat legacy path.
8. The one calculation that stays in orchestration is `congestion_score` derivation from the effective
   scenario and route index. If it grows past a single expression, move it to scoring. Perform no
   other arithmetic on domain quantities and declare no coefficient literal.
9. Write T-23 with stub collaborators that record call order:
   - the eight workflow steps run in order;
   - both Places resolutions are in flight before either completes;
   - the adjusted-ETA fallback prefers traffic-aware, then static, then segment sum plus buffer;
   - a same-place trip raises `SameOriginDestinationError` and issues zero Routes calls.

## Boundaries

- No coefficient and no domain formula beyond the single `congestion_score` expression (R2, NFR-5.2).
- No mode-string comparison outside the one `resolve_mode_policy` call (R4).
- No transport library and no outbound Google call (R6).
- No `HTTPException` construction. Errors escape as domain exceptions (R8).
- Caching is P2. Do not add a place or plan cache.
- Do not add a second public method for a future heatmap flow. Heatmap planning is its own service in
  prompt 24.

## Tests To Write

| Test ID | Level | Target file | Assertion |
|---------|-------|-------------|-----------|
| T-23 | unit | `tests/test_planning.py` | Adjusted-ETA fallback chain, eight-step call order, concurrent Places resolution, and same-place short-circuit |

## Definition Of Done

- [ ] `plan()` performs the eight steps in order.
- [ ] Origin and destination Places calls are issued concurrently.
- [ ] A same-place trip fails with `same_origin_destination` and issues zero Routes calls.
- [ ] Simulated returns up to 3 routes; Real-Time returns exactly 1, through the policy.
- [ ] `recommended_route_id` is the id of the lowest-scoring route and always equals one element of `routes`.
- [ ] `map_bounds` equals `union_bounds` over the per-route bounds.
- [ ] `app/api/planning.py` contains no coefficient literal and no transport import.
- [ ] Every collaborator is constructor-injected.
- [ ] T-23 passes.
- [ ] `python -m pytest` passes.

## Handoff

Report the public surface of `PlanningService` and the dependency providers, the stub names T-23
uses, and any orchestration document step whose order you had to clarify against the sequence diagram.
