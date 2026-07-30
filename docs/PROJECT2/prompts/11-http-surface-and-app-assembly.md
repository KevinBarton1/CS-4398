# Prompt 11 — HTTP Surface And App Assembly

**Wave:** 2 — Controller
**Depends on:** prompts 01 through 10
**Phase:** P1
**Read first:** [00-shared-context.md](00-shared-context.md)

## Read First

1. [00-shared-context.md](00-shared-context.md)
2. [../srs-context/controller/api-contracts.md](../srs-context/controller/api-contracts.md)
3. [../srs-context/controller/external-service-boundaries.md](../srs-context/controller/external-service-boundaries.md)
4. [../srs-context/architecture/architecture-overview.md](../srs-context/architecture/architecture-overview.md), sections "Containers", "Trust Boundaries And Credentials", "Deployment Assumptions"
5. [../README.md](../README.md), the three P1 endpoints and the error envelope
6. [../agent-quickstart.md](../agent-quickstart.md), "Run And Test"

## Objective

Expose the three P1 endpoints, assemble the FastAPI application, run the Google reachability probe at
startup without blocking, and serve the built single-page application from `dist/` in production. This
is the HTTP surface the View will talk to.

## Deliverables

| File | Responsibility |
|------|----------------|
| `TrafficSImulation/app/api/routes.py` | `APIRouter` for `POST /api/plan`, `GET /api/health`, `GET /api/map/config` |
| `TrafficSImulation/main.py` | App assembly, exception-handler registration, lifespan probe, static hosting |
| `TrafficSImulation/tests/test_api.py` | T-01 through T-11 |
| `TrafficSImulation/tests/test_static.py` | T-42 |

## Task

1. Declare the three P1 endpoints in `app/api/routes.py`. Each handler receives a validated body or
   injected dependency and does nothing else: no orchestration, no coefficient, no Google call.
   - `POST /api/plan` awaits `PlanningService.plan` and returns `PlanResponse`.
   - `GET /api/health` returns `HealthResponse` with `SERVICE_NAME`, `SERVICE_VERSION`,
     `google_maps_configured` from Settings, and the latest probe result.
   - `GET /api/map/config` returns `MapConfigResponse` with `maps_browser_api_key` from Settings and
     the map constants from configuration. When the browser credential is absent, raise
     `MapsNotConfiguredError` so the handler returns 503. Never return an empty key. Never return the
     server key. Never name a field `maps_api_key`.
2. Assemble the app in `main.py`:
   - Create the FastAPI instance.
   - Call `register_exception_handlers`.
   - Mount the API router.
   - Install a lifespan handler that runs `GoogleApiProbe.check` once, records the outcome for health,
     and logs a warning on failure without preventing startup.
   - Serve the built single-page application from `dist/` when the directory exists. A missing build
     logs a warning and does not prevent startup. The fallback route serves only files inside `dist/`
     and refuses path traversal (T-42, NFR-3.7).
   - Put no domain logic, no coefficient, and no Google call body in `main.py`.
3. Wire dependencies through `app/api/dependencies.py` from prompt 10. The route module imports
   providers; it does not construct gateways inline.
4. Write the API suite in `tests/test_api.py` using the FastAPI test client and the mocked transports
   from `tests/google_mocks.py`. Cover:
   - T-01 Simulated happy path: up to three routes, populated segments, echoed scenario, notice.
   - T-02 Real-Time happy path: exactly one route, `scenario_applied` false, mode notice.
   - T-03 Out-of-range scenario returns 422 with `validation_error` and `fields`.
   - T-04 Unresolvable location returns 400 with `invalid_location`.
   - T-05 Identical origin and destination returns 400 with `same_origin_destination`, and the
     routing stub is never called.
   - T-06 Zero alternatives returns 400 with `no_route_found`.
   - T-07 Absent server credential returns 503 with `maps_not_configured`, and no response contains
     the key value.
   - T-08 Upstream error status returns 502 with a sanitized `detail`.
   - T-09 Upstream timeout returns 504 with `upstream_timeout`.
   - T-10 Health response shape and probe reporting without failing when Google is unreachable.
   - T-11 Map configuration returns `maps_browser_api_key`, never the server credential, with the
     documented center, zoom, color scheme, and libraries; `map_id` is null when unset.
5. Write T-42 in `tests/test_static.py`: the SPA fallback refuses paths that resolve outside `dist/`.
6. Confirm the default suite makes zero live Google calls.

## Boundaries

- No logic in `main.py` beyond assembly, lifespan, and static hosting.
- No coefficient in `routes.py` or `main.py` (R2).
- No mode comparison outside the policy module (R4).
- No outbound Google call outside the three gateway modules (R6). The lifespan calls the probe; the
  probe is one of those three.
- Do not add `POST /api/heatmap` or any other endpoint. Heatmaps are P3.
- Do not introduce a second map-related endpoint. There is no embed endpoint in the target design.

## Tests To Write

| Test ID | Level | Target file | Assertion |
|---------|-------|-------------|-----------|
| T-01 through T-11 | api | `tests/test_api.py` | Happy paths, every error code, health, and map config |
| T-42 | api | `tests/test_static.py` | SPA fallback refuses paths outside `dist/` |

## Definition Of Done

- [ ] The three P1 endpoints exist at the locked paths and return the locked shapes.
- [ ] `GET /api/map/config` exposes `maps_browser_api_key` and never a field named `maps_api_key`.
- [ ] `GOOGLE_MAPS_API_KEY` does not appear in any response body produced by the test suite.
- [ ] A failed probe logs a warning and does not prevent startup; health still answers.
- [ ] A missing `dist/` logs a warning and does not prevent startup.
- [ ] The SPA fallback refuses path traversal.
- [ ] Every error code in the README table is covered by a test.
- [ ] The default suite makes zero live Google calls.
- [ ] T-01 through T-11 and T-42 pass.
- [ ] `python -m pytest` passes.
- [ ] `python main.py` starts and answers `GET /api/health`.

## Handoff

Report the three endpoint signatures, the lifespan behavior, how static hosting is mounted, and any
API-contracts sentence that disagreed with the README's locked shapes.
