# Prompt 08 — API Schemas And Error Envelope

**Wave:** 2 — Controller
**Depends on:** prompts 01, 02, 03, 04
**Phase:** P1
**Read first:** [00-shared-context.md](00-shared-context.md)

## Read First

1. [00-shared-context.md](00-shared-context.md)
2. [../README.md](../README.md), sections "`POST /api/plan` request", "`POST /api/plan` response", "`GET /api/map/config` response", "`GET /api/health` response", "Error envelope", and every shared value object
3. [../srs-context/controller/api-contracts.md](../srs-context/controller/api-contracts.md)
4. [../srs-context/controller/validation-error-handling.md](../srs-context/controller/validation-error-handling.md)
5. [../srs-context/architecture/class-diagram.md](../srs-context/architecture/class-diagram.md), Controller types and the Domain error hierarchy
6. [../srs-context/model/domain-contracts.md](../srs-context/model/domain-contracts.md)

## Objective

Declare the locked HTTP contracts as Pydantic models and install the single error envelope. This
package is the Controller's type system: every later Controller package imports from here, and the
View will eventually mirror these shapes in TypeScript.

## Deliverables

| File | Responsibility |
|------|----------------|
| `TrafficSImulation/app/api/models.py` | `PlanRequest`, `PlanResponse`, `MapConfigResponse`, `HealthResponse`, `ErrorResponse`, and every nested value object the response carries |
| `TrafficSImulation/app/api/errors.py` | Domain error hierarchy (or re-exports from the Model), the `DomainError` handler, and the `RequestValidationError` handler that flattens into the locked envelope |
| Unit coverage inside `tests/test_errors.py` | T-49 for sanitization |

## Task

1. Declare `PlanRequest` with the locked fields and constraints: `origin` and `destination` 1–120
   characters after trimming; `mode` defaulting to `simulated` and accepting only `simulated` or
   `realtime`; `hour` 0–23 defaulting to `DEFAULT_HOUR`; `weather` 0–3 defaulting to
   `DEFAULT_WEATHER`; `congestion` 0–100 defaulting to `DEFAULT_CONGESTION`. Defaults are imported
   from configuration, never redeclared.
2. Declare `PlanResponse` with exactly the locked top-level fields. Nested types
   (`Scenario`, `WeatherState`, `RouteOption`, `RoadSegment`, `PriceFactors`, `RouteBounds`,
   `LatLngPoint`, `TrafficInterval`) match the README field for field. Arrays are always present,
   never null. `RawRoute` does not appear in any response model.
3. Declare `MapConfigResponse` with `maps_browser_api_key` (never a field named `maps_api_key`),
   `map_id`, `default_center`, `default_zoom`, `color_scheme`, and `libraries`.
4. Declare `HealthResponse` with `status`, `service`, `version`, `google_maps_configured`, and
   `google_maps` as a `ProbeResult`.
5. Declare `ErrorResponse` as `{ detail: string, code: string }` with an optional `fields` array used
   only by validation failures.
6. Install the domain error hierarchy. If prompt 04 already defined the exceptions under the Model,
   re-export or subclass them here so the handler has a single base. Every subclass declares both
   `code` and `status` as class attributes matching the class diagram table.
7. Register two handlers in a function that `main.py` will call:
   - one for `DomainError` that returns the locked envelope with the exception's `code`, `status`, and
     sanitized `detail`;
   - one for `RequestValidationError` that flattens the framework's list-shaped body into a string
     `detail`, code `validation_error`, status 422, and a `fields` array.
8. Sanitize every detail: no traceback, no credential, no upstream response body. Write T-49 against
   that rule.
9. Do not mount routers and do not create the FastAPI app in this package. Prompt 11 owns assembly.
   Export a `register_exception_handlers(app)` function that prompt 11 will call.

## Boundaries

- No coefficient and no formula in either file (R2). Defaults are imported from configuration.
- Do not put a mode comparison beyond the Pydantic literal constraint for `mode`. Policy decisions
  belong in prompt 09 (R4).
- Do not serialize `RawRoute`.
- Do not add a field the README does not list, and do not rename `maps_browser_api_key` to anything
  shorter.
- Do not catch and soften gateway failures. Handlers map; they do not invent.

## Tests To Write

| Test ID | Level | Target file | Assertion |
|---------|-------|-------------|-----------|
| T-49 | unit | `tests/test_errors.py` | Sanitization of upstream messages; no credential or traceback in detail or log content |

Schema-level validation is exercised end-to-end by T-03 in prompt 11; write focused unit tests here
only where a constraint is easier to pin without HTTP.

## Definition Of Done

- [ ] Every locked request and response field is declared with its documented type and constraint.
- [ ] `RawRoute` appears in no Pydantic response model.
- [ ] `maps_browser_api_key` is the field name; `maps_api_key` does not exist.
- [ ] Every `DomainError` subclass declares `code` and `status` as class attributes.
- [ ] The validation handler returns `422` with `validation_error` and a `fields` array.
- [ ] No handler body contains a coefficient or a formula.
- [ ] T-49 passes.
- [ ] `python -m pytest` passes.

## Handoff

Report the complete public type list, the exception class locations, the
`register_exception_handlers` signature, and any README field whose type was ambiguous when expressed
in Pydantic.
