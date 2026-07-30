# Prompt 04 — Google Gateways And Probe

**Wave:** 1 — Model
**Depends on:** prompts 01, 02, 03
**Phase:** P1
**Read first:** [00-shared-context.md](00-shared-context.md)

## Read First

1. [00-shared-context.md](00-shared-context.md)
2. [../srs-context/model/google-integrations.md](../srs-context/model/google-integrations.md) — read all of it
3. [../srs-context/controller/external-service-boundaries.md](../srs-context/controller/external-service-boundaries.md)
4. [../srs-context/architecture/architecture-overview.md](../srs-context/architecture/architecture-overview.md), section "Trust Boundaries And Credentials"
5. [../srs-context/architecture/class-diagram.md](../srs-context/architecture/class-diagram.md), the Model types and the Domain error hierarchy
6. [../srs-context/model/configuration.md](../srs-context/model/configuration.md), the Google integration constants

## Objective

Build the three modules that are allowed to make outbound Google HTTP calls: the Places gateway, the
Routes gateway, and the reachability probe. These are the only network seams in the Model. Every
failure they raise is a typed domain exception; they never construct an HTTP response.

## Deliverables

| File | Responsibility |
|------|----------------|
| `TrafficSImulation/app/map/places.py` | `GooglePlacesGateway.resolve(query) -> ResolvedPlace` |
| `TrafficSImulation/app/map/routing.py` | `GoogleRoutesGateway.compute(...) -> list[RawRoute]` |
| `TrafficSImulation/app/map/health.py` | `GoogleApiProbe.check() -> ProbeResult` |
| `TrafficSImulation/tests/test_google_places.py` | T-20 |
| `TrafficSImulation/tests/test_google_routes.py` | T-21 |
| `TrafficSImulation/tests/google_mocks.py` | Shared mocked-transport fixtures for both gateways and later API tests |

## Task

1. Define the domain exceptions this package raises. Prefer defining them in a Model-owned module that
   `app/api/errors.py` will later import and subclass or re-export, rather than defining HTTP-aware
   exceptions here. Every exception carries a `code` and a `status` as class attributes, matching the
   hierarchy in the class diagram: `InvalidLocationError`, `NoRouteFoundError`,
   `MapsNotConfiguredError`, `UpstreamUnavailableError`, `UpstreamTimeoutError`. Do not raise
   `HTTPException`. Do not choose a status at a call site.
2. Implement `GooglePlacesGateway`:
   - Accept `Settings` and an injectable `httpx` client through the constructor so tests substitute a
     mocked transport without patching module globals.
   - Call `GOOGLE_PLACES_SEARCH_URL` with `X-Goog-Api-Key` carrying the server key,
     `X-Goog-FieldMask` equal to `GOOGLE_PLACES_FIELD_MASK`, `maxResultCount` 1, `regionCode`
     `GOOGLE_REGION_CODE`, and the Austin circular location bias from `AUSTIN_LOCATION_BIAS`.
   - Apply `PLACES_TIMEOUT_SECONDS`.
   - Translate a zero-result payload or a result without coordinates into `InvalidLocationError`.
   - Translate an absent server key into `MapsNotConfiguredError` before any network call.
   - Translate an upstream error status into `UpstreamUnavailableError` and a timeout into
     `UpstreamTimeoutError`, with a sanitized detail that never contains the credential or the raw
     upstream body.
3. Implement `GoogleRoutesGateway`:
   - Same constructor injection pattern.
   - Call `GOOGLE_ROUTES_COMPUTE_URL` with `travelMode` `DRIVE`, `routingPreference` `TRAFFIC_AWARE`,
     `units` `IMPERIAL`, `regionCode` `US`, a `departureTime`, `extraComputations`
     `["TRAFFIC_ON_POLYLINE"]`, and the alternatives flag from the caller.
   - Apply the field mask from `GOOGLE_ROUTES_FIELD_MASK` and `ROUTES_TIMEOUT_SECONDS`.
   - Decode the polyline through `decode_polyline`. Extract speed reading intervals preferring
     leg-level then falling back to route-level, as the integrations document specifies.
   - Truncate to `ROUTE_ALTERNATIVES_MAX`. Translate zero alternatives into `NoRouteFoundError`. Map
     credential and upstream failures the same way Places does.
4. Implement `GoogleApiProbe`:
   - Check Places and Routes reachability once, cache the result for `HEALTH_PROBE_CACHE_SECONDS`, and
     return a `ProbeResult` with `ok`, `message`, and `checked_at`.
   - A failed probe logs a warning and does not raise. Lifespan and health reporting consume the
     recorded outcome; they do not block startup (NFR-2.4).
5. Build `tests/google_mocks.py` with transport fixtures that both gateway unit tests and the later
   API suite can share. The default suite makes zero live Google calls.
6. Write T-20 and T-21 against the documented payloads, headers, timeouts, and error translations.
   Assert that neither the server credential nor an upstream body appears in any raised exception's
   `detail`.
7. Leave the opt-in live-credential probe (T-57) for prompt 12 or a later package; note the marker
   name so it stays deselected by default.

## Boundaries

- These three modules are the only ones allowed to make outbound Google HTTP calls (R6). Do not put a
  Google call in any other file, including a helper you invent.
- The Model raises domain exceptions; it does not convert them to HTTP (R8). Prompt 08 owns the
  handlers.
- Never return, log, or embed the server credential. Presence is logged as a boolean.
- Do not introduce a silent local fallback for place resolution or routing. An absent credential or an
  unreachable upstream is an explicit error.
- Do not import FastAPI, `main`, or anything under `app/api/` beyond the shared exception base if you
  placed it there (R1). Prefer keeping the exception base under `app/map/` or a sibling Model module.
- Caching of place resolution is P2. Do not add it here.

## Tests To Write

| Test ID | Level | Target file | Assertion |
|---------|-------|-------------|-----------|
| T-20 | unit | `tests/test_google_places.py` | Payload, headers, bias, field mask, 8 s timeout, and error translation for zero-result and missing-coordinates |
| T-21 | unit | `tests/test_google_routes.py` | Payload including departure time and traffic extras, interval extraction, timeout, zero-alternatives translation |

## Definition Of Done

- [ ] Places is called with `maxResultCount` 1, `regionCode` `US`, the Austin bias, and the three-field mask.
- [ ] Routes is called with `DRIVE`, `TRAFFIC_AWARE`, `IMPERIAL`, a `departureTime`, and `TRAFFIC_ON_POLYLINE`.
- [ ] Speed intervals prefer leg-level and fall back to route-level.
- [ ] An absent server key raises `MapsNotConfiguredError` before any network call.
- [ ] Zero Places results raise `InvalidLocationError`; zero Routes alternatives raise `NoRouteFoundError`.
- [ ] Upstream error and timeout map to `UpstreamUnavailableError` and `UpstreamTimeoutError` with sanitized detail.
- [ ] The probe never raises and never blocks import.
- [ ] Every collaborator is constructor-injected; T-20 and T-21 use mocked transports only.
- [ ] No response, log line, or exception detail contains the server credential.
- [ ] T-20 and T-21 pass. `python -m pytest` passes.

## Handoff

Report the public method signatures, the exact exception hierarchy and where each class lives, the
mocked-transport fixture names in `tests/google_mocks.py`, and any payload field whose Google
documentation disagreed with the specification.
