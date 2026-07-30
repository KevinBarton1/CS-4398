# Non-Functional Requirements — PROJECT2

**Scope:** TrafficScope rewrite. Future-state quality attributes.
**Authority:** All names, fields, modes, and labels come from [../../README.md](../../README.md).
**Related:** [functional-requirements.md](functional-requirements.md), [traceability.md](traceability.md), [../architecture/architecture-overview.md](../architecture/architecture-overview.md)

Each requirement is stated so it can be checked. Where a threshold is given, it is the acceptance
threshold, not an aspiration. Status and phase columns follow the same rules as the functional
catalog.

---

## NFR-1 Responsiveness And Performance

| ID | Requirement | Status | Phase | Owner |
|----|-------------|--------|-------|-------|
| NFR-1.1 | `POST /api/plan` shall complete within 3 seconds at the 95th percentile when Google Places and Routes are reachable, measured server-side. | Target | P1 | Controller |
| NFR-1.2 | A scenario change shall be reflected in the rendered result within 2 seconds of the 180 ms debounce firing under NFR-1.1 conditions. | Target | P1 | View |
| NFR-1.3 | The application shell shall reach first contentful paint within 2 seconds on a broadband desktop connection. | Target | P1 | View |
| NFR-1.4 | The map shall remain pannable and zoomable while polylines are rebuilt; polyline rebuilds shall not block the main thread for more than 100 ms per plan. | Target | P1 | View |
| NFR-1.5 | Superseded in-flight plan requests shall be aborted so that only the newest response updates state. | Target | P1 | View |
| NFR-1.6 | Repeated plans for an unchanged origin and destination shall reuse cached place resolutions and issue no additional Places requests. | Target | P2 | Model |
| NFR-1.7 | The production bundle shall stay under 400 kB gzipped excluding the Google Maps JavaScript API itself. | Target | P2 | View |

---

## NFR-2 Reliability And External API Failure Handling

| ID | Requirement | Status | Phase | Owner |
|----|-------------|--------|-------|-------|
| NFR-2.1 | Outbound Google requests shall use explicit timeouts: 8 seconds for Places and 10 seconds for Routes, both configurable through `Settings`. | Target | P1 | Model |
| NFR-2.2 | No upstream failure shall produce an unhandled exception or a response body outside the documented error envelope. | Target | P1 | Controller |
| NFR-2.3 | A failure in the map surface shall not prevent planning, route selection, or analysis from working. | Target | P1 | View |
| NFR-2.4 | A startup probe shall report Google Places and Routes reachability through `GET /api/health` without preventing the service from starting. | Target | P1 | Controller |
| NFR-2.5 | The system shall have no silent data fallback. When a dependency is unavailable, the user shall see an explicit degraded state, never substituted numbers presented as real results. | Target | P1 | Controller |
| NFR-2.6 | Transient upstream failures shall be retried once with jittered backoff before being surfaced. | Target | P2 | Controller |
| NFR-2.7 | Server-side logs shall record the upstream status, latency, and sanitized error for every failed Google call. | Target | P1 | Controller |

---

## NFR-3 Security And API-Key Trust Boundaries

| ID | Requirement | Status | Phase | Owner |
|----|-------------|--------|-------|-------|
| NFR-3.1 | The server Google credential used for Places and Routes shall never appear in any HTTP response body, log line, or client bundle. | Target | P1 | Controller |
| NFR-3.2 | The browser shall receive only a separate Maps JavaScript API credential, restricted by HTTP referrer to the deployed origins and restricted by API to the Maps JavaScript API. | Target | P1 | Controller |
| NFR-3.3 | Credentials shall be supplied exclusively through environment variables and shall never be committed to the repository. | Target | P1 | Model |
| NFR-3.4 | The service shall not persist user-entered locations, coordinates, plans, or device positions. | Target | P1 | Controller |
| NFR-3.5 | Production deployments shall terminate TLS in front of the service and shall serve the application over HTTPS only. | Target | P1 | Controller |
| NFR-3.6 | Error bodies returned to clients shall be sanitized: no stack traces, no raw upstream payloads, no credential fragments. | Target | P1 | Controller |
| NFR-3.7 | The single-page-application fallback route shall serve only files resolved inside the build output directory. | Target | P1 | Controller |
| NFR-3.8 | Browser and server credentials shall be independently rotatable without a code change. | Target | P2 | Controller |

---

## NFR-4 Accessibility

| ID | Requirement | Status | Phase | Owner |
|----|-------------|--------|-------|-------|
| NFR-4.1 | The interface shall target WCAG 2.1 Level AA. | Target | P1 | View |
| NFR-4.2 | Every interactive control shall be reachable and operable by keyboard alone, with a visible focus indicator and no keyboard trap. | Target | P1 | View |
| NFR-4.3 | Every piece of information conveyed by the map shall also be available as text in the route list or the segment table. | Target | P1 | View |
| NFR-4.4 | Request status and error messages shall be announced through a polite live region. | Target | P1 | View |
| NFR-4.5 | Text and essential interface elements shall meet a contrast ratio of at least 4.5 to 1 against their background. | Target | P1 | View |
| NFR-4.6 | Color shall never be the only carrier of meaning; traffic severity shall also be conveyed in text. | Target | P1 | View |
| NFR-4.7 | Transitions and animations shall honor the `prefers-reduced-motion` user preference. | Target | P2 | View |
| NFR-4.8 | An automated accessibility audit shall run in continuous integration with zero critical violations. | Target | P2 | View |

---

## NFR-5 Maintainability And Architecture

| ID | Requirement | Status | Phase | Owner |
|----|-------------|--------|-------|-------|
| NFR-5.1 | Dependencies shall flow View to Controller to Model only. No Model module shall import the Controller, FastAPI, or any HTTP concern. | Target | P1 | Model |
| NFR-5.2 | Orchestration shall coordinate services without containing domain formulas. Every coefficient-bearing calculation shall live in a Model module. | Target | P1 | Controller |
| NFR-5.3 | All coefficients, rates, weights, multipliers, URLs, and timeouts shall be defined once in `app/config/__init__.py`. | Target | P1 | Model |
| NFR-5.4 | The backend package set shall remain `api`, `map`, `simulation`, `pricing`, `weather`, `heatmap`, and `config` as fixed by repo-root `AGENTS.md`. | Target | P1 | Model |
| NFR-5.5 | Branching on the planning mode shall occur only in `app/api/mode_policy.py`. No other module shall compare the mode string. | Target | P1 | Controller |
| NFR-5.6 | No module shall use a flat legacy path such as `app/routes.py`, `app/models.py`, `app/map_service.py`, `app/traffic_simulator.py`, `app/pricing_model.py`, `app/weather_service.py`, or `app/heatmap.py`. | Target | P1 | Model |
| NFR-5.7 | The product shall contain exactly one map rendering path. A second map technology shall not be introduced for any mode, state, or fallback. | Target | P1 | View |
| NFR-5.8 | Python shall use four-space indentation and `snake_case`; TypeScript and TSX shall use two-space indentation with `PascalCase` components and types and `camelCase` values. | Target | P1 | Model |
| NFR-5.9 | Dead code shall not be retained. A module that no runtime path reaches shall be deleted rather than kept for reference. | Target | P1 | Model |

---

## NFR-6 Testability And Contract Consistency

| ID | Requirement | Status | Phase | Owner |
|----|-------------|--------|-------|-------|
| NFR-6.1 | Every endpoint shall have an automated test asserting its status codes and response field set. | Target | P1 | Controller |
| NFR-6.2 | Every domain formula shall have a unit test, including a boundary or identity case. | Target | P1 | Model |
| NFR-6.3 | The default test suite shall make no live Google calls; gateways shall be tested against mocked transports. | Target | P1 | Model |
| NFR-6.4 | `src/types.ts` shall mirror the response models in `app/api/models.py`, and a test shall fail when the two field sets diverge. | Target | P1 | Controller |
| NFR-6.5 | User-visible React behavior shall be verified with Testing Library in jsdom rather than by snapshotting markup. | Target | P1 | View |
| NFR-6.6 | `npm run build` shall type-check with zero errors and shall gate merges. | Target | P1 | View |
| NFR-6.7 | A contract test shall assert the exact top-level and per-route response field sets so that additive or breaking changes are deliberate. | Target | P1 | Controller |
| NFR-6.8 | An end-to-end browser test shall cover the plan, select, and mode-switch flow. | Target | P2 | View |
| NFR-6.9 | Any live-credential test shall be opt-in and shall be excluded from the default run. | Target | P1 | Model |

---

## NFR-7 Transparency And Usability

| ID | Requirement | Status | Phase | Owner |
|----|-------------|--------|-------|-------|
| NFR-7.1 | Every successful plan response shall carry a non-empty `notice` describing the provenance of the numbers, and the View shall display it. | Target | P1 | Controller |
| NFR-7.2 | The illustrative-estimate disclaimer shall be visible whenever a price is shown. | Target | P1 | View |
| NFR-7.3 | Each route shall state its data provenance through `data_source`, and the View shall surface it in the selected-route summary. | Target | P1 | View |
| NFR-7.4 | `weather.source` shall disclose that weather is a simulated planning input rather than an observation. | Target | P1 | Model |
| NFR-7.5 | A control that has no effect in the active mode shall be hidden with an explanation rather than rendered in a silently disabled state. | Target | P1 | View |
| NFR-7.6 | Every displayed quantity shall carry its unit: miles, minutes, miles per hour, vehicles per hour, percent, or US dollars. | Target | P1 | View |
| NFR-7.7 | Primary metrics shall use typography large enough to be read at a glance on a laptop display. | Target | P1 | View |

---

## Explicitly Excluded Quality Attributes

These are recorded so the rewrite does not accumulate unstated obligations.

| Attribute | Decision |
|-----------|----------|
| Horizontal scaling and multi-instance session affinity | Out of scope; the service is stateless and single-instance for PROJECT2 |
| Internationalization and localization | Out of scope; the interface is US English with US units |
| Offline or service-worker operation | Out of scope |
| Native mobile applications | Out of scope; responsive web only |
| Authentication, authorization, and rate limiting per user | Out of scope; there are no user accounts |
| Long-term analytics, telemetry pipelines, or usage warehousing | Out of scope; only operational logging is required |
