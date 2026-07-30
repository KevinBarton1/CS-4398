# Controller Context — Validation and Error Handling

**Layer:** Controller  
**Target modules:** `TrafficSImulation/app/api/errors.py`, `TrafficSImulation/app/api/models.py`, `TrafficSImulation/main.py`  
**Related:** [api-contracts.md](api-contracts.md), [orchestration.md](orchestration.md), [external-service-boundaries.md](external-service-boundaries.md), [../view/loading-error-states.md](../view/loading-error-states.md), [../view/route-scenario-forms.md](../view/route-scenario-forms.md), [../requirements/non-functional-requirements.md](../requirements/non-functional-requirements.md)

## Purpose

Reject bad input as early as possible, translate every failure into one predictable HTTP envelope, and
keep server internals out of client responses. A client should be able to write one error handler that
covers every endpoint.

## Requirements

| ID | Requirement | Status | Phase |
|----|-------------|--------|-------|
| FR-1.5 | An unresolvable location returns 400 `invalid_location` naming the unresolved input | Target | P1 |
| FR-1.6 | Identical origin and destination resolutions return 400 `same_origin_destination` | Target | P1 |
| FR-5.6 | Out-of-range scenario values return 422 with code `validation_error` | Target | P1 |
| FR-7.1 | Every non-2xx response body is exactly `{detail, code}`, plus `fields` for 422 | Target | P1 |
| FR-7.2 | Each failure class maps to exactly one code and status | Target | P1 |
| FR-7.3 | The View displays `detail` and chooses its presentation from `code` | Target | P1 |
| FR-7.4 | A failed plan preserves the form inputs, the scenario, and the previous plan | Target | P1 |
| FR-7.8 | Upstream timeouts are surfaced as retryable with explicit retry guidance | Target | P1 |
| FR-7.9 | Responses never contain stack traces, credentials, or unsanitized upstream bodies | Target | P1 |
| NFR-2.2 | No upstream failure produces an unhandled exception or an off-contract body | Target | P1 |
| NFR-2.5 | There is no silent data fallback; a degraded dependency is stated, never substituted | Target | P1 |
| NFR-2.7 | Logs record upstream status, latency, and sanitized error for every failed Google call | Target | P1 |
| NFR-3.1 | No credential value appears in a response body or a log line | Target | P1 |
| NFR-3.6 | Error bodies are sanitized before they leave the server | Target | P1 |
| NFR-6.1 | Every endpoint has an automated test asserting its status codes and field set | Target | P1 |
| FR-7.10 | Automatic client-side retry with jittered backoff for timeouts and upstream failures | Target | P2 |
| NFR-2.6 | Transient upstream failures are retried once with jittered backoff before surfacing | Target | P2 |
| FR-7.11 | Offline operation or replaying a cached plan without network access | Out of scope | — |
| FR-7.12 | Any place-resolution or routing substitute that answers when Google is unavailable | Out of scope | — |

## Validation Layers

Four layers, cheapest first. Each layer assumes the previous one passed, so no layer re-checks what an
earlier one guarantees.

| Layer | Location | Catches | Client sees |
|-------|----------|---------|-------------|
| 1. Browser form constraints | `src/components/RoutePlannerForm.tsx`, `src/components/ScenarioControls.tsx` | Empty fields, over-length text, slider values outside range | Inline field messages; no request is sent |
| 2. Pydantic schema | `app/api/models.py` | Missing fields, wrong types, out-of-range numbers, unknown mode, unknown extra fields | 422 `validation_error` with `fields` |
| 3. Domain invariants | `app/api/planning.py`, `app/map/places.py`, `app/map/routing.py` | Unresolvable places, identical endpoints, zero alternatives | 400 with the specific code |
| 4. Upstream failures | `app/map/places.py`, `app/map/routing.py` | Missing credential, error statuses, timeouts, transport errors | 503, 502, or 504 |

### Layer 1 — Browser form constraints

Native constraints do the obvious work so a typo does not cost a round trip. `origin` and
`destination` are `required` with `maxLength` 120; scenario inputs are `range` inputs bounded to
0–23, 0–3, and 0–100. Client validation is a convenience, never a guarantee: the server repeats every
one of these checks, because the API is reachable without the UI.

The View trims before submitting but does not reject on trimmed length alone; a whitespace-only entry
is submitted and refused by layer 2, which keeps one authority for the rule.

### Layer 2 — Pydantic schema

| Field | Rule | Failure |
|-------|------|---------|
| `origin`, `destination` | Trimmed, then 1–120 characters | 422 |
| `mode` | One of `simulated`, `realtime` | 422 |
| `hour` | Integer 0–23 | 422 |
| `weather` | Integer 0–3 | 422 |
| `congestion` | Integer 0–100 | 422 |
| Any other key | Not permitted | 422 |

```python
class PlanRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    origin: str = Field(min_length=1, max_length=120)
    destination: str = Field(min_length=1, max_length=120)
    mode: PlanMode = PlanMode.SIMULATED
    hour: int = Field(default=17, ge=0, le=23)
    weather: int = Field(default=1, ge=0, le=3)
    congestion: int = Field(default=56, ge=0, le=100)
```

Out-of-range values are rejected, never clamped. Clamping is worse than refusing: a request for
`hour=25` that quietly plans for 23:00 returns numbers the caller did not ask for and cannot detect.
`extra="forbid"` catches a stale client still sending a retired field instead of silently ignoring it.
Trimming happens before length validation, so `"   "` fails the minimum length rather than reaching
Places as an empty query.

### Layer 3 — Domain invariants

These cannot be expressed in a schema because they depend on upstream results.

| Invariant | Raised by | Exception | Code |
|-----------|-----------|-----------|------|
| Places returned at least one usable result with coordinates | `app/map/places.py` | `PlaceNotFoundError` | `invalid_location` |
| Origin and destination resolved to different places | `app/api/planning.py` | `SameOriginDestinationError` | `same_origin_destination` |
| Routes returned at least one alternative | `app/map/routing.py` | `NoRouteFoundError` | `no_route_found` |

The same-place check compares resolved place identity, not the user's text. "Austin Airport" and "AUS"
are different strings that resolve to one place, and planning a trip from a location to itself is
refused before any Routes call. The check runs immediately after both resolutions complete.

### Layer 4 — Upstream failures

| Condition | Raised by | Exception | Code |
|-----------|-----------|-----------|------|
| `Settings.google_maps_api_key` empty, or `Settings.google_maps_browser_api_key` empty on `GET /api/map/config` | `app/config/__init__.py` | `MapsNotConfiguredError` | `maps_not_configured` |
| Places non-2xx | `app/map/places.py` | `PlacesUnavailableError` | `upstream_unavailable` |
| Places timeout or transport error | `app/map/places.py` | `PlacesTimeoutError` | `upstream_timeout` |
| Routes non-2xx | `app/map/routing.py` | `RoutesUnavailableError` | `upstream_unavailable` |
| Routes timeout or transport error | `app/map/routing.py` | `RoutesTimeoutError` | `upstream_timeout` |

The credential check happens before the HTTP call is built, so a misconfigured deployment fails fast
with 503 rather than sending an unauthenticated request and reporting Google's 403 as
`upstream_unavailable`. There is no planning path that works without the server credential; a missing
key is a configuration error, not a condition to degrade around.

## Error Envelope

Every non-2xx response from every endpoint, including 422 and unhandled 500, uses one shape.

```json
{ "detail": "Could not resolve \"Mars Colony\" to an Austin-area location.", "code": "invalid_location" }
```

| Key | Type | Presence |
|-----|------|----------|
| `detail` | string | Always; a complete sentence safe to display verbatim |
| `code` | string | Always; a stable machine-readable identifier |
| `fields` | array | Only on 422 `validation_error` |

### Error catalog

| `code` | Status | Cause | Example `detail` |
|--------|--------|-------|------------------|
| `validation_error` | 422 | Request body failed schema validation | `Request validation failed.` |
| `invalid_location` | 400 | Places returned no usable result | `Could not resolve "Mars Colony" to an Austin-area location.` |
| `same_origin_destination` | 400 | Origin and destination resolved to the same place | `Origin and destination resolved to the same place. Choose two different locations.` |
| `no_route_found` | 400 | Routes returned zero alternatives | `No drivable route was found between these locations.` |
| `maps_not_configured` | 503 | A required Google credential is absent: the server key on a planning call, the browser key on `GET /api/map/config` | `Google Maps is not configured on the server.` |
| `upstream_unavailable` | 502 | Places or Routes returned an error status | `The Google Routes service returned an error. Try again shortly.` |
| `upstream_timeout` | 504 | Places or Routes exceeded the configured timeout | `The Google Routes service did not respond in time. Try again shortly.` |

Codes are the client's contract; `detail` wording is not. The View switches behavior on `code` and
displays `detail`. It must never parse `detail` to decide anything.

### 422 field details

The custom handler flattens FastAPI's default list-shaped 422 body into the standard envelope plus a
`fields` array, so a client never has to special-case validation responses.

```json
{
  "detail": "Request validation failed.",
  "code": "validation_error",
  "fields": [
    { "field": "weather", "message": "Input should be less than or equal to 3" },
    { "field": "origin", "message": "String should have at least 1 character" }
  ]
}
```

`field` is the dotted path with the `body` prefix removed, so `["body", "weather"]` becomes `weather`
and the View can map an entry straight onto a form control. `message` is Pydantic's message with the
submitted input omitted, which keeps user text out of logs that record response bodies. One entry is
emitted per failure, and the order follows Pydantic's report order.

## Handler Wiring

Handlers are registered in `main.py` from factories defined in `app/api/errors.py`. `main.py` contains
no `try`/`except` around planning, and no route function in `app/api/routes.py` raises
`HTTPException` directly.

| Handler | Registered for | Produces |
|---------|----------------|----------|
| `validation_exception_handler` | `RequestValidationError` | 422 `validation_error` with `fields` |
| `domain_exception_handler` | `TrafficScopeError` and its subclasses | The code and status from the mapping table |
| `http_exception_handler` | `StarletteHTTPException` | Envelope form of framework errors such as 404 and 405 |
| `unhandled_exception_handler` | `Exception` | 500 `internal_error` with a fixed generic `detail` |

```python
ERROR_MAPPING: dict[type[Exception], tuple[str, int]] = {
    PlaceNotFoundError: ("invalid_location", 400),
    SameOriginDestinationError: ("same_origin_destination", 400),
    NoRouteFoundError: ("no_route_found", 400),
    MapsNotConfiguredError: ("maps_not_configured", 503),
    PlacesUnavailableError: ("upstream_unavailable", 502),
    RoutesUnavailableError: ("upstream_unavailable", 502),
    PlacesTimeoutError: ("upstream_timeout", 504),
    RoutesTimeoutError: ("upstream_timeout", 504),
}
```

`app/api/errors.py` owns the mapping and the handlers. It does not own the exception classes that the
Model raises: gateway failures are declared in the gateway modules that raise them, and
`MapsNotConfiguredError` lives beside `Settings` in `app/config/__init__.py`. That keeps the dependency
arrow pointing one way — the Controller imports Model exception types to map them, and no Model module
imports anything from `app/api/`. `SameOriginDestinationError` is the exception to that pattern and is
declared in `app/api/errors.py`, because it is a Controller-level invariant across two Model results
rather than a failure of either gateway.

Framework errors go through the envelope too. A request to an unknown `/api/*` path returns
`{"detail": "...", "code": "not_found"}` rather than FastAPI's default body, so no client ever sees two
error shapes.

## What Clients See and What They Do Not

| Never in a response body | Why |
|--------------------------|-----|
| Stack traces or exception class names | Reveals internal structure and dependency versions |
| File paths or line numbers | Same, and useless to the user |
| Raw Google response bodies | May carry quota, project, and account identifiers |
| Google endpoint URLs or field masks | Discloses upstream call structure |
| Any API credential, whole or partial | A leaked key is a billable incident |
| Internal timing, retry counts, or host names | Aids reconnaissance and confuses users |
| Python exception `repr` output | Frequently carries request payloads |

An upstream error yields a sanitized sentence only. Google's own message is extracted for the server
log, not for the response: the 502 body says the Routes service returned an error and suggests
retrying, while the log carries the upstream status and message. The current implementation's habit of
returning `f"Routes API HTTP {status}: {detail}"` straight to the caller is exactly what the rewrite
removes.

Two things clients do get: a stable `code`, and a `detail` written for a person. `detail` quotes the
user's own input when that is what makes the message actionable, as in `invalid_location`, and quoting
is safe because the value came from the client and is JSON-encoded on the way out.

## Server-Side Logging

Every non-2xx response emits exactly one structured log record at the boundary where it is converted.
Handlers log; orchestration and gateways do not log the same failure again.

| Field | Content |
|-------|---------|
| `code` | The error code returned |
| `status` | The HTTP status returned |
| `endpoint` | Method and path |
| `request_id` | Correlation identifier, also returned in an `X-Request-Id` response header |
| `mode` | Effective planning mode, on plan failures |
| `upstream` | `places` or `routes`, on layers 4 failures |
| `upstream_status` | Google's HTTP status, when there was one |
| `upstream_message` | Sanitized Google message, truncated to 800 characters |
| `duration_ms` | Time spent before the failure |
| `exception` | Full traceback, at `ERROR` level, for 500 only |

| Level | Used for |
|-------|----------|
| `INFO` | 400 and 422; these are normal user-input outcomes |
| `WARNING` | 502, 503, and 504; these are operational conditions |
| `ERROR` | 500 and adjusted-ETA fallback level 3; these are defects or degradations |

Credentials are never logged, not even truncated. Log the fact that a key is absent, never the value of
one that is present. User-entered location text is logged at `INFO` for `invalid_location` because it
is the only way to learn which real-world queries the Places bias fails to cover; nothing else from the
request body is logged.

## Retry Guidance

| `code` | Retry the same request | Client behavior |
|--------|----------------------|-----------------|
| `validation_error` | No | Highlight the fields from the `fields` array |
| `invalid_location` | No | Ask the user to rephrase the location |
| `same_origin_destination` | No | Ask the user to change one endpoint |
| `no_route_found` | No | Suggest different endpoints |
| `maps_not_configured` | No | Show an operator-facing message; the user cannot fix it |
| `upstream_unavailable` | Yes, once, after a pause | Offer a retry control; do not retry automatically |
| `upstream_timeout` | Yes, once, after a pause | Same |

The server does not retry Places or Routes in P1. A single retry inside the request would put the p95
target of 3 s at risk under exactly the conditions where the upstream is already slow, and the caller is
better placed to decide whether waiting is worthwhile. NFR-2.6 schedules one jittered-backoff server
retry for P2; when it lands it will apply only to timeouts and connection errors, never to a 4xx from
Google, will be capped at one attempt, and must keep the total request inside the latency budget.

In P1 the View offers an explicit retry control rather than retrying on its own, and preserves the form
state and the scenario values behind every error so that pressing it resubmits exactly what the user
meant. An error never clears the previous successful plan from the screen; the last good routes and map
stay visible beneath the message, which is what makes a transient 502 an interruption rather than a
reset. Automatic client-side retry with jittered backoff is FR-7.10, deferred to P2.

## Acceptance Criteria

- [ ] `weather=99` returns 422 with `code` `validation_error` and a `fields` entry naming `weather`.
- [ ] A whitespace-only `origin` returns 422, not a Places call.
- [ ] An unknown request key returns 422 rather than being ignored.
- [ ] `mode="reference"` returns 422 rather than defaulting to Simulated.
- [ ] Out-of-range scenario values are rejected, never clamped to the nearest valid value.
- [ ] An unresolvable destination returns 400 `invalid_location` with the submitted text quoted in `detail`.
- [ ] Two inputs that resolve to the same place return 400 `same_origin_destination` with zero Routes calls.
- [ ] Zero alternatives from Routes returns 400 `no_route_found`.
- [ ] An absent server credential returns 503 `maps_not_configured` with zero upstream calls.
- [ ] A Places or Routes non-2xx returns 502 `upstream_unavailable`; a timeout returns 504 `upstream_timeout`.
- [ ] No non-2xx body contains a traceback, a file path, a Google URL, a raw upstream body, or a credential.
- [ ] An unknown `/api/*` path returns the standard envelope, not FastAPI's default error body.
- [ ] An unexpected internal exception returns 500 with a generic `detail` while the traceback appears in the log.
- [ ] Every error code has at least one test that provokes it end to end.
- [ ] After a failed plan, the View keeps the form values, the scenario values, and the previous successful result on screen.

## Planned Tests

| Test ID | Level | Target file | Assertion |
|---------|-------|-------------|-----------|
| T-03 | api | `tests/test_api.py` | An out-of-range scenario value returns 422 `validation_error` with a `fields` array naming the field, and whitespace-only, over-length, unknown-key, and unknown-`mode` requests each return 422 with no gateway call |
| T-09 | api | `tests/test_api.py` | A simulated Routes timeout returns 504 `upstream_timeout` |
| T-30 | component | `src/components/StatusBanner.test.tsx` | A failed re-plan shows the error `detail`, offers retry, and retains the form, scenario, and previous plan |
| T-04 | api | `tests/test_api.py` | An unresolvable location returns 400 `invalid_location` with the submitted text quoted in `detail` |
| T-05 | api | `tests/test_api.py` | The same resolved place returns 400 `same_origin_destination` and the routing stub is never called |
| T-06 | api | `tests/test_api.py` | Zero alternatives returns 400 `no_route_found` |
| T-07 | api | `tests/test_api.py` | An empty server credential returns 503 `maps_not_configured` with zero upstream calls |
| T-08 | api | `tests/test_api.py` | A stubbed Places or Routes non-2xx returns 502 `upstream_unavailable` with a sanitized `detail` |
| T-49 | unit | `tests/test_errors.py` | No error body contains `Traceback`, a `.py` path, a Google host, or a credential value, and an unknown `/api` path and an internal exception both return the standard envelope |

## Agent Implementation Notes

- Register handlers on the app in `main.py`; keep their bodies in `app/api/errors.py` so they are unit-testable without a running server.
- Never raise `HTTPException` from `app/api/routes.py` or `app/api/planning.py`. Raise a domain exception and let the mapping decide the status; that is what keeps the code-to-status table true.
- Give every domain exception a `detail` message written for a user at the raise site. Do not build user-facing text inside the handler from an exception class name.
- Sanitize upstream messages at the gateway boundary and carry the sanitized text on the exception for logging. The handler must not receive an `httpx.Response`.
- Add new codes to the catalog in this file, to `ERROR_MAPPING`, to the `responses=` declarations in `app/api/routes.py`, to `src/types.ts`, and to a test — in one commit.
- Keep the 500 handler's `detail` a fixed constant. Interpolating an exception message into it is the most common way internals leak.
- Assert the absence of leaks positively: T-49 scans every error body for forbidden substrings rather than trusting review.
- When P2 adds retry behavior under FR-7.10 and NFR-2.6, it changes how often these responses reach the user and how the View presents them. It must not change any status, code, or body shape defined here.
