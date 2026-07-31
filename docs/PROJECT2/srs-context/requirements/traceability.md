# Requirements Traceability And Progress — PROJECT2

**Purpose:** Give every requirement exactly one owning context file, one phase, and at least one planned
test, so that nothing is specified without an owner and nothing is claimed without a check.

**Authority:** [../../README.md](../../README.md).
**Related:** [functional-requirements.md](functional-requirements.md), [non-functional-requirements.md](non-functional-requirements.md), [../architecture/architecture-overview.md](../architecture/architecture-overview.md)

**Progress convention:** P1 rows verified in Prompt 22 (2026-07-31) are marked `Complete` when their
planned tests pass. Harness-only or deployment rows remain `Deferred` or `Partial` with the reason in
the Progress cell. P2 rows verified in Prompt 23 (2026-07-31) are marked `Complete` when their planned
tests pass. P3 rows stay `Not started` until prompt 24 lands. Do not mark a row
complete without a passing planned test.

Test levels:

| Level | Meaning | Location |
|-------|---------|----------|
| `unit` | A pure function or a single class with mocked collaborators | `tests/test_*.py` or `src/**/*.test.ts` |
| `api` | An HTTP request through the FastAPI test client | `tests/test_*.py` |
| `component` | Rendered React behavior in jsdom with Testing Library | `src/**/*.test.tsx` |
| `e2e` | A real browser against a running stack | `e2e/` |

---

## Functional Requirement Traceability

| ID | Owning context | Phase | Acceptance criterion | Planned tests | Progress |
|----|----------------|-------|----------------------|---------------|----------|
| FR-1.1 | [../view/route-scenario-forms.md](../view/route-scenario-forms.md) | P1 | A labeled origin input renders with the documented default | T-25 | Complete |
| FR-1.2 | [../view/route-scenario-forms.md](../view/route-scenario-forms.md) | P1 | A labeled destination input renders with the documented default | T-25 | Complete |
| FR-1.3 | [../view/route-scenario-forms.md](../view/route-scenario-forms.md) | P1 | Granted permission fills the origin with `lat, lng` text | T-35 | Complete |
| FR-1.4 | [../model/google-integrations.md](../model/google-integrations.md) | P1 | Both locations resolve through Places text search server-side | T-20, T-01 | Complete |
| FR-1.5 | [../controller/validation-error-handling.md](../controller/validation-error-handling.md) | P1 | An unresolvable location returns `400` with `invalid_location` | T-04 | Complete |
| FR-1.6 | [../controller/orchestration.md](../controller/orchestration.md) | P1 | Identical resolutions return `400` with `same_origin_destination` | T-05 | Complete |
| FR-1.7 | [../controller/api-contracts.md](../controller/api-contracts.md) | P1 | The response echoes resolved display names | T-01 | Complete |
| FR-1.8 | [../model/route-planning.md](../model/route-planning.md) | P2 | A scenario-only re-plan issues no new Places request | T-47 | Complete |
| FR-1.9 | — | — | Out of scope | — | Not planned |
| FR-1.10 | — | — | Out of scope | — | Not planned |
| FR-2.1 | [../model/google-integrations.md](../model/google-integrations.md) | P1 | Alternatives come from `computeRoutes` server-side | T-21, T-01 | Complete |
| FR-2.2 | [../model/route-planning.md](../model/route-planning.md) | P1 | Simulated returns up to three named alternatives with distinct objectives | T-01 | Complete |
| FR-2.3 | [../controller/mode-policies.md](../controller/mode-policies.md) | P1 | Real-Time returns exactly one alternative | T-02, T-22 | Complete |
| FR-2.4 | [../model/domain-contracts.md](../model/domain-contracts.md) | P1 | `distance_miles` present at one decimal place | T-24 | Complete |
| FR-2.5 | [../model/route-planning.md](../model/route-planning.md) | P1 | `base_eta_minutes` derives from the static duration | T-23 | Complete |
| FR-2.6 | [../controller/mode-policies.md](../controller/mode-policies.md) | P1 | `adjusted_eta_minutes` follows the active policy | T-22, T-23 | Complete |
| FR-2.7 | [../model/traffic-simulation.md](../model/traffic-simulation.md) | P1 | Every route carries at least one fully populated segment | T-14, T-01 | Complete |
| FR-2.8 | [../model/route-planning.md](../model/route-planning.md) | P1 | The recommended route has the lowest normalized score | T-17 | Complete |
| FR-2.9 | [../controller/mode-policies.md](../controller/mode-policies.md) | P1 | `data_source` matches the mode | T-22 | Complete |
| FR-2.10 | [../view/results-analysis.md](../view/results-analysis.md) | P1 | Selection persists across a re-plan when the id remains | T-29 | Complete |
| FR-2.11 | [../model/traffic-simulation.md](../model/traffic-simulation.md) | P2 | Segments cover the full step list | T-14 | Complete |
| FR-2.12 | — | — | Out of scope | — | Not planned |
| FR-2.13 | — | — | Out of scope | — | Not planned |
| FR-3.1 | [../view/map-rendering.md](../view/map-rendering.md) | P1 | The map is a Maps JavaScript API instance | T-31 | Complete |
| FR-3.2 | [../view/map-rendering.md](../view/map-rendering.md) | P1 | Both modes render through the same component | T-28, T-31 | Complete |
| FR-3.3 | [../view/map-rendering.md](../view/map-rendering.md) | P1 | Routes draw as native polylines from `polyline` | T-32 | Complete |
| FR-3.4 | [../view/map-rendering.md](../view/map-rendering.md) | P1 | One polyline per traffic interval, colored by speed | T-32, T-33 | Complete |
| FR-3.5 | [../view/map-rendering.md](../view/map-rendering.md) | P1 | Tint applies in Simulated only | T-33 | Complete |
| FR-3.6 | [../view/map-rendering.md](../view/map-rendering.md) | P1 | Selected route is emphasized | T-32 | Complete |
| FR-3.7 | [../view/map-rendering.md](../view/map-rendering.md) | P1 | Camera fits selected `bounds`, view-all fits `map_bounds` | T-34 | Complete |
| FR-3.8 | [../view/map-rendering.md](../view/map-rendering.md) | P2 | Origin and destination markers render with labels | T-48 | Complete |
| FR-3.9 | [../view/map-rendering.md](../view/map-rendering.md) | P2 | Clicking a polyline selects its route | T-48 | Complete |
| FR-3.10 | — | — | Out of scope | — | Not planned |
| FR-3.11 | — | — | Out of scope | — | Not planned |
| FR-4.1 | [../view/app-composition.md](../view/app-composition.md) | P1 | Two mode options with the locked labels | T-28 | Complete |
| FR-4.2 | [../view/app-composition.md](../view/app-composition.md) | P1 | A mode change issues a new plan request | T-28 | Complete |
| FR-4.3 | [../controller/mode-policies.md](../controller/mode-policies.md) | P1 | `scenario_applied` matches the mode | T-02, T-22 | Complete |
| FR-4.4 | [../view/route-scenario-forms.md](../view/route-scenario-forms.md) | P1 | Scenario controls are absent in Real-Time | T-28 | Complete |
| FR-4.5 | [../controller/mode-policies.md](../controller/mode-policies.md) | P1 | `notice` is mode-specific and non-empty | T-01, T-02 | Complete |
| FR-4.6 | — | — | Out of scope | — | Not planned |
| FR-5.1 | [../view/route-scenario-forms.md](../view/route-scenario-forms.md) | P1 | Hour control spans 0 to 23 with a 12-hour readout | T-26 | Complete |
| FR-5.2 | [../view/route-scenario-forms.md](../view/route-scenario-forms.md) | P1 | Weather control spans 0 to 3 with the locked labels | T-26 | Complete |
| FR-5.3 | [../view/route-scenario-forms.md](../view/route-scenario-forms.md) | P1 | Congestion control spans 0 to 100 with a percentage readout | T-26 | Complete |
| FR-5.4 | [../view/route-scenario-forms.md](../view/route-scenario-forms.md) | P1 | Reset restores the documented defaults | T-26 | Complete |
| FR-5.5 | [../view/app-composition.md](../view/app-composition.md) | P1 | Rapid changes coalesce into one request | T-27 | Complete |
| FR-5.6 | [../controller/validation-error-handling.md](../controller/validation-error-handling.md) | P1 | Out-of-range values return `422` with `validation_error` | T-03 | Complete |
| FR-5.7 | [../controller/api-contracts.md](../controller/api-contracts.md) | P1 | The response echoes the effective scenario | T-01, T-02 | Complete |
| FR-5.8 | — | — | Out of scope | — | Not planned |
| FR-5.9 | — | — | Out of scope | — | Not planned |
| FR-5.10 | — | — | Out of scope | — | Not planned |
| FR-6.1 | [../model/pricing.md](../model/pricing.md) | P1 | Every route carries a two-decimal `estimated_price` | T-15 | Complete |
| FR-6.2 | [../model/pricing.md](../model/pricing.md) | P1 | All five `price_factors` fields present | T-15, T-24 | Complete |
| FR-6.3 | [../model/pricing.md](../model/pricing.md) | P1 | The minimum fare floor applies | T-15 | Complete |
| FR-6.4 | [../model/pricing.md](../model/pricing.md) | P1 | Factors reproduce `unrounded_total` and the rounded price | T-15 | Complete |
| FR-6.5 | [../view/results-analysis.md](../view/results-analysis.md) | P1 | The illustrative-estimate disclaimer is always visible | T-38 | Complete |
| FR-6.6 | — | — | Out of scope | — | Not planned |
| FR-6.7 | — | — | Out of scope | — | Not planned |
| FR-7.1 | [../controller/validation-error-handling.md](../controller/validation-error-handling.md) | P1 | Every non-2xx body has `detail` and `code` | T-03 through T-09 | Complete |
| FR-7.2 | [../controller/validation-error-handling.md](../controller/validation-error-handling.md) | P1 | Each failure class maps to its documented code and status | T-03 through T-09 | Complete |
| FR-7.3 | [../view/loading-error-states.md](../view/loading-error-states.md) | P1 | Presentation branches on `code` and shows `detail` | T-30 | Complete |
| FR-7.4 | [../view/loading-error-states.md](../view/loading-error-states.md) | P1 | A failure preserves inputs and the previous plan | T-30 | Complete |
| FR-7.5 | [../view/loading-error-states.md](../view/loading-error-states.md) | P1 | Map failure is contained to the map region | T-31 | Complete |
| FR-7.6 | [../view/route-scenario-forms.md](../view/route-scenario-forms.md) | P1 | Denied geolocation shows a notice and leaves entry working | T-35 | Complete |
| FR-7.7 | [../view/loading-error-states.md](../view/loading-error-states.md) | P1 | A transport failure shows a connectivity message | T-30 | Complete |
| FR-7.8 | [../view/loading-error-states.md](../view/loading-error-states.md) | P1 | `upstream_timeout` presents retry guidance | T-09, T-30 | Complete |
| FR-7.9 | [../controller/validation-error-handling.md](../controller/validation-error-handling.md) | P1 | No body contains a traceback or credential | T-08, T-49 | Complete |
| FR-7.10 | [../controller/external-service-boundaries.md](../controller/external-service-boundaries.md) | P2 | One jittered retry before surfacing a transient failure | T-50 | Complete |
| FR-7.11 | — | — | Out of scope | — | Not planned |
| FR-7.12 | — | — | Out of scope | — | Not planned |
| FR-8.1 | [../model/heatmaps.md](../model/heatmaps.md) | P3 | `POST /api/heatmap` returns congestion cells | T-41 | Not started |
| FR-8.2 | [../model/heatmaps.md](../model/heatmaps.md) | P3 | Cells render as an overlay on the existing map instance | T-51 | Not started |
| FR-8.3 | [../model/heatmaps.md](../model/heatmaps.md) | P3 | A legend describes the intensity scale | T-51 | Not started |
| FR-8.4 | [../model/heatmaps.md](../model/heatmaps.md) | P3 | Toggling the overlay preserves the plan and camera | T-51 | Not started |
| FR-8.5 | — | — | Out of scope | — | Not planned |
| FR-8.6 | — | — | Out of scope | — | Not planned |

---

## Non-Functional Requirement Traceability

| ID | Owning context | Phase | Acceptance criterion | Planned tests | Progress |
|----|----------------|-------|----------------------|---------------|----------|
| NFR-1.1 | [../controller/orchestration.md](../controller/orchestration.md) | P1 | Server-measured p95 under 3 s with Google reachable | T-52 | Deferred — T-52 performance harness |
| NFR-1.2 | [../view/app-composition.md](../view/app-composition.md) | P1 | Rendered result within 2 s of the debounce firing | T-52 | Deferred — T-52 performance harness |
| NFR-1.3 | [../view/app-composition.md](../view/app-composition.md) | P1 | First contentful paint under 2 s on broadband | T-52 | Deferred — T-52 performance harness |
| NFR-1.4 | [../view/map-rendering.md](../view/map-rendering.md) | P1 | Polyline rebuild blocks the main thread under 100 ms | T-32 | Complete |
| NFR-1.5 | [../view/app-composition.md](../view/app-composition.md) | P1 | Superseded requests are aborted and discarded | T-27 | Complete |
| NFR-1.6 | [../model/route-planning.md](../model/route-planning.md) | P2 | Cached place resolution avoids repeat Places calls | T-47 | Complete |
| NFR-1.7 | [../view/app-composition.md](../view/app-composition.md) | P2 | Bundle under 400 kB gzipped excluding the Maps script | T-53 | Complete |
| NFR-2.1 | [../controller/external-service-boundaries.md](../controller/external-service-boundaries.md) | P1 | Places 8 s and Routes 10 s timeouts are applied | T-09, T-21 | Complete |
| NFR-2.2 | [../controller/validation-error-handling.md](../controller/validation-error-handling.md) | P1 | No unhandled exception or non-envelope body | T-06 through T-09 | Complete |
| NFR-2.3 | [../view/loading-error-states.md](../view/loading-error-states.md) | P1 | Map failure leaves planning usable | T-31 | Complete |
| NFR-2.4 | [../controller/api-contracts.md](../controller/api-contracts.md) | P1 | The probe reports status without blocking startup | T-10 | Complete |
| NFR-2.5 | [../controller/mode-policies.md](../controller/mode-policies.md) | P1 | No substituted data; degraded states are explicit | T-07 | Complete |
| NFR-2.6 | [../controller/external-service-boundaries.md](../controller/external-service-boundaries.md) | P2 | One jittered retry on a transient failure | T-50 | Complete |
| NFR-2.7 | [../controller/external-service-boundaries.md](../controller/external-service-boundaries.md) | P1 | Failed upstream calls log status, latency, and a sanitized error | T-49 | Complete |
| NFR-3.1 | [../controller/external-service-boundaries.md](../controller/external-service-boundaries.md) | P1 | The server credential appears in no response or log | T-11, T-49 | Complete |
| NFR-3.2 | [../controller/external-service-boundaries.md](../controller/external-service-boundaries.md) | P1 | Only the referrer-restricted browser credential is served | T-11 | Complete |
| NFR-3.3 | [../model/configuration.md](../model/configuration.md) | P1 | Credentials come only from the environment | T-54 | Complete |
| NFR-3.4 | [../controller/api-contracts.md](../controller/api-contracts.md) | P1 | No persistence of locations, plans, or positions | T-54 | Complete |
| NFR-3.5 | [../architecture/architecture-overview.md](../architecture/architecture-overview.md) | P1 | Deployment terminates TLS and serves HTTPS only | Manual review | Deferred — manual deployment review |
| NFR-3.6 | [../controller/validation-error-handling.md](../controller/validation-error-handling.md) | P1 | Error bodies are sanitized | T-08, T-49 | Complete |
| NFR-3.7 | [../controller/api-contracts.md](../controller/api-contracts.md) | P1 | The fallback route serves only files inside the build output | T-42 | Complete |
| NFR-3.8 | [../controller/external-service-boundaries.md](../controller/external-service-boundaries.md) | P2 | Credentials rotate without a code change | T-54 | Complete |
| NFR-4.1 | [../view/accessibility.md](../view/accessibility.md) | P1 | WCAG 2.1 AA target documented and reviewed | T-36, T-37 | Complete |
| NFR-4.2 | [../view/accessibility.md](../view/accessibility.md) | P1 | Every control is keyboard operable with visible focus | T-36 | Complete |
| NFR-4.3 | [../view/accessibility.md](../view/accessibility.md) | P1 | Map information is duplicated in text | T-39 | Complete |
| NFR-4.4 | [../view/accessibility.md](../view/accessibility.md) | P1 | Status and errors announce through a polite live region | T-37 | Complete |
| NFR-4.5 | [../view/accessibility.md](../view/accessibility.md) | P1 | Text contrast at least 4.5 to 1 | T-55 | Partial — contrast subset in src/utils/contrast.test.ts |
| NFR-4.6 | [../view/accessibility.md](../view/accessibility.md) | P1 | Traffic severity is conveyed in text as well as color | T-39 | Complete |
| NFR-4.7 | [../view/accessibility.md](../view/accessibility.md) | P2 | Reduced-motion preference honored | T-55 | Complete |
| NFR-4.8 | [../view/accessibility.md](../view/accessibility.md) | P2 | Automated audit passes with no critical violations | T-55 | Complete |
| NFR-5.1 | [../architecture/architecture-overview.md](../architecture/architecture-overview.md) | P1 | No Model to Controller import edge | T-45 | Complete |
| NFR-5.2 | [../controller/orchestration.md](../controller/orchestration.md) | P1 | Orchestration contains no coefficient | T-45 | Complete |
| NFR-5.3 | [../model/configuration.md](../model/configuration.md) | P1 | All coefficients defined once in `app/config/__init__.py` | T-54 | Complete |
| NFR-5.4 | [../architecture/architecture-overview.md](../architecture/architecture-overview.md) | P1 | The package set matches `AGENTS.md` | T-45 | Complete |
| NFR-5.5 | [../controller/mode-policies.md](../controller/mode-policies.md) | P1 | Only the mode policy module compares the mode string | T-46 | Complete |
| NFR-5.6 | [../architecture/architecture-overview.md](../architecture/architecture-overview.md) | P1 | No flat legacy module path exists | T-45 | Complete |
| NFR-5.7 | [../view/map-rendering.md](../view/map-rendering.md) | P1 | Exactly one map rendering path | T-31, T-56 | Complete |
| NFR-5.8 | [../architecture/architecture-overview.md](../architecture/architecture-overview.md) | P1 | Indentation and naming conventions hold | Lint | Deferred — no lint runner configured |
| NFR-5.9 | [../architecture/architecture-overview.md](../architecture/architecture-overview.md) | P1 | No unreachable module is retained | T-45 | Complete |
| NFR-6.1 | [../controller/api-contracts.md](../controller/api-contracts.md) | P1 | Every endpoint has a status and shape test | T-01, T-02, T-10, T-11 | Complete |
| NFR-6.2 | [../model/traffic-simulation.md](../model/traffic-simulation.md) | P1 | Every domain formula has a unit test with a boundary case | T-12 through T-19 | Complete |
| NFR-6.3 | [../model/google-integrations.md](../model/google-integrations.md) | P1 | The default suite makes no live Google call | T-20, T-21 | Complete |
| NFR-6.4 | [../controller/api-contracts.md](../controller/api-contracts.md) | P1 | A test fails when the Python and TypeScript field sets diverge | T-24 | Complete |
| NFR-6.5 | [../view/app-composition.md](../view/app-composition.md) | P1 | React behavior is asserted, not snapshotted | T-25 through T-39 | Complete |
| NFR-6.6 | [../view/app-composition.md](../view/app-composition.md) | P1 | `npm run build` type-checks clean and gates merges | T-43 | Complete |
| NFR-6.7 | [../controller/api-contracts.md](../controller/api-contracts.md) | P1 | A contract test pins the response field sets | T-24 | Complete |
| NFR-6.8 | [../view/app-composition.md](../view/app-composition.md) | P2 | An end-to-end flow covers plan, select, and mode switch | T-44 | Complete |
| NFR-6.9 | [../model/google-integrations.md](../model/google-integrations.md) | P1 | Live-credential tests are opt-in | T-57 | Complete |
| NFR-7.1 | [../controller/api-contracts.md](../controller/api-contracts.md) | P1 | `notice` is present and displayed | T-01, T-02, T-25 | Complete |
| NFR-7.2 | [../view/results-analysis.md](../view/results-analysis.md) | P1 | The disclaimer is visible whenever a price shows | T-38 | Complete |
| NFR-7.3 | [../view/results-analysis.md](../view/results-analysis.md) | P1 | `data_source` is surfaced in the selected-route summary | T-38 | Complete |
| NFR-7.4 | [../model/weather-scenarios.md](../model/weather-scenarios.md) | P1 | `weather.source` discloses a simulated origin | T-16 | Complete |
| NFR-7.5 | [../view/route-scenario-forms.md](../view/route-scenario-forms.md) | P1 | An inert control is hidden with an explanation | T-28 | Complete |
| NFR-7.6 | [../view/results-analysis.md](../view/results-analysis.md) | P1 | Every quantity carries its unit | T-39 | Complete |
| NFR-7.7 | [../view/results-analysis.md](../view/results-analysis.md) | P1 | Primary metrics are legible at a glance | T-55 | Partial — contrast subset in src/utils/contrast.test.ts |

---

## Test Catalog

| Test ID | Level | Target file | Covers |
|---------|-------|-------------|--------|
| T-01 | api | `tests/test_api.py` | Simulated plan happy path: three routes, populated segments, echoed scenario, notice |
| T-02 | api | `tests/test_api.py` | Real-Time plan happy path: one route, `scenario_applied` false, mode notice |
| T-03 | api | `tests/test_api.py` | Out-of-range scenario returns `422` with `validation_error` and `fields` |
| T-04 | api | `tests/test_api.py` | Unresolvable location returns `400` with `invalid_location` |
| T-05 | api | `tests/test_api.py` | Identical origin and destination returns `400` with `same_origin_destination` |
| T-06 | api | `tests/test_api.py` | Zero alternatives returns `400` with `no_route_found` |
| T-07 | api | `tests/test_api.py` | Absent server credential returns `503` with `maps_not_configured` |
| T-08 | api | `tests/test_api.py` | Upstream error status returns `502` with a sanitized `detail` |
| T-09 | api | `tests/test_api.py` | Upstream timeout returns `504` with `upstream_timeout` |
| T-10 | api | `tests/test_api.py` | Health response shape and probe reporting |
| T-11 | api | `tests/test_api.py` | Map configuration returns the browser credential and never the server credential |
| T-12 | unit | `tests/test_simulation.py` | BPR zero-flow identity and monotonic increase with flow |
| T-13 | unit | `tests/test_simulation.py` | Time-of-day factor bands and clamping |
| T-14 | unit | `tests/test_simulation.py` | Segment derivation: capacity, flow, average speed, polyline slices |
| T-15 | unit | `tests/test_pricing.py` | Fare formula, factor reproduction, minimum fare floor |
| T-16 | unit | `tests/test_weather.py` | Severity to label and multipliers, with clamping and `source` |
| T-17 | unit | `tests/test_scoring.py` | Normalization, recommendation, and the single-route case |
| T-18 | unit | `tests/test_polyline.py` | Polyline decoding against known encoded input |
| T-19 | unit | `tests/test_bounds.py` | `bounds_for_points` and `union_bounds` |
| T-20 | unit | `tests/test_google_places.py` | Places payload, field mask, location bias, error translation |
| T-21 | unit | `tests/test_google_routes.py` | Routes payload including departure time and traffic extras, interval extraction, timeout |
| T-22 | unit | `tests/test_mode_policy.py` | The full mode policy behavior table |
| T-23 | unit | `tests/test_planning.py` | Adjusted-ETA fallback chain and orchestration ordering |
| T-24 | api | `tests/test_contracts.py` | Exact top-level and per-route response field sets |
| T-25 | component | `src/App.test.tsx` | Initial load renders the default plan, notice, and route list |
| T-26 | component | `src/components/ScenarioControls.test.tsx` | Slider ranges, readouts, and reset |
| T-27 | component | `src/hooks/useRoutePlan.test.ts` | Debounce coalescing, abort of superseded requests |
| T-28 | component | `src/App.test.tsx` | Real-Time switch hides scenario controls and renders one route |
| T-29 | component | `src/App.test.tsx` | Selection updates analysis and reconciles across a re-plan |
| T-30 | component | `src/components/StatusBanner.test.tsx` | Error presentation by `code`, input and plan preservation |
| T-31 | component | `src/components/RouteMap.test.tsx` | Map configuration failure is contained; one map surface for both modes |
| T-32 | component | `src/components/RoutePolylineLayer.test.tsx` | One polyline per interval, emphasis, disposal on unmount |
| T-33 | unit | `src/utils/trafficSegmentColor.test.ts` | Speed to color mapping and tint behavior |
| T-34 | component | `src/components/MapBoundsController.test.tsx` | `fitBounds` targets and refit triggers |
| T-35 | component | `src/components/RoutePlannerForm.test.tsx` | Geolocation grant and denial paths |
| T-36 | component | `src/App.test.tsx` | Keyboard traversal of the mode switch and route cards |
| T-37 | component | `src/App.test.tsx` | Live-region announcements for loading and error |
| T-38 | component | `src/components/PriceSummary.test.tsx` | All five factors, currency formatting, disclaimer, `data_source` |
| T-39 | component | `src/components/SegmentTable.test.tsx` | Every segment row with units and textual severity |
| T-40 | unit | `tests/test_heatmap.py` | P3: grid values respond to congestion and hour |
| T-41 | api | `tests/test_api.py` | P3: heatmap endpoint shape |
| T-42 | api | `tests/test_static.py` | Fallback route refuses paths outside the build output |
| T-43 | e2e | Continuous integration | `npm run build` type-checks with zero errors |
| T-44 | e2e | `e2e/plan.spec.ts` | P2: plan, select, and switch mode in a real browser |
| T-45 | unit | `tests/test_architecture.py` | Import-graph rules and absence of legacy module paths |
| T-46 | unit | `tests/test_architecture.py` | Mode literals appear only in the mode policy module |
| T-47 | unit | `tests/test_planning.py` | P2: place resolution cache prevents repeat Places calls |
| T-48 | component | `src/components/RouteMap.test.tsx` | P2: markers render and polyline click selects |
| T-49 | unit | `tests/test_errors.py` | Sanitization of upstream messages and log content |
| T-50 | unit | `tests/test_google_routes.py` | P2: one jittered retry before surfacing a transient failure |
| T-51 | component | `src/components/HeatmapLayer.test.tsx` | P3: overlay renders on the existing map and toggles cleanly |
| T-52 | e2e | Performance harness | Plan latency and debounce-to-render timing |
| T-53 | e2e | Continuous integration | Bundle size budget |
| T-54 | unit | `tests/test_config.py` | Environment-only credentials, single coefficient definition, no persistence |
| T-55 | e2e | Accessibility harness | Contrast, reduced motion, automated audit |
| T-56 | unit | `tests/test_architecture.py` | Maps JavaScript API usage confined to the four map components |
| T-57 | unit | `tests/test_google_live.py` | Opt-in live-credential probe, excluded by default |

---

## Coverage Summary

| Group | Target requirements | Out of scope | Phase P1 | Phase P2 | Phase P3 |
|-------|--------------------|--------------|----------|----------|----------|
| FR-1 | 8 | 2 | 7 | 1 | 0 |
| FR-2 | 11 | 2 | 10 | 1 | 0 |
| FR-3 | 9 | 2 | 7 | 2 | 0 |
| FR-4 | 5 | 1 | 5 | 0 | 0 |
| FR-5 | 7 | 3 | 7 | 0 | 0 |
| FR-6 | 5 | 2 | 5 | 0 | 0 |
| FR-7 | 10 | 2 | 9 | 1 | 0 |
| FR-8 | 4 | 2 | 0 | 0 | 4 |
| NFR-1 | 7 | — | 5 | 2 | 0 |
| NFR-2 | 7 | — | 6 | 1 | 0 |
| NFR-3 | 8 | — | 7 | 1 | 0 |
| NFR-4 | 8 | — | 6 | 2 | 0 |
| NFR-5 | 9 | — | 9 | 0 | 0 |
| NFR-6 | 9 | — | 8 | 1 | 0 |
| NFR-7 | 7 | — | 7 | 0 | 0 |

Every `Target` requirement above has at least one owning context file and at least one planned test.
Rows whose planned test is `Manual review` or a named harness are the only ones not covered by an
automated check; each is a deployment or measurement concern rather than a behavior.

## Agent Implementation Notes

- When adding a requirement, add it to the FR or NFR catalog, add a row here with an owner and a
  planned test, and add the test to the catalog. A requirement with no test row is incomplete.
- When a test is implemented, keep its ID stable. Test IDs are referenced from the layer contexts.
- Update the progress column as work lands, and keep the coverage summary consistent with the tables.
