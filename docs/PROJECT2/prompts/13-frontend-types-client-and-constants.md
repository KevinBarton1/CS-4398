# Prompt 13 — Frontend Types, Client, And Constants

**Wave:** 3 — View
**Depends on:** prompts 01, 08, 11, 12
**Phase:** P1
**Read first:** [00-shared-context.md](00-shared-context.md)

## Read First

1. [00-shared-context.md](00-shared-context.md)
2. [../README.md](../README.md), every locked request and response shape and every shared value object
3. [../srs-context/architecture/class-diagram.md](../srs-context/architecture/class-diagram.md), section "Frontend type aliases"
4. [../srs-context/controller/api-contracts.md](../srs-context/controller/api-contracts.md)
5. [../srs-context/model/configuration.md](../srs-context/model/configuration.md), the scenario defaults and the "View Never Imports Coefficients" section
6. [../agent-quickstart.md](../agent-quickstart.md), "Contract synchronization"

## Objective

Give the View a typed vocabulary that mirrors the Controller one-to-one, a transport that speaks the
error envelope, and the one intentional duplication of scenario defaults. No component is built in
this package; every later View package imports from here.

## Deliverables

| File | Responsibility |
|------|----------------|
| `TrafficSImulation/src/types.ts` | Every TypeScript type in the mirror table |
| `TrafficSImulation/src/api/client.ts` | Typed fetch, abort handling, error-envelope parsing |
| `TrafficSImulation/src/constants/scenario.ts` | The three scenario defaults, matching Python |
| `TrafficSImulation/src/utils/format.ts` | Currency, distance, and duration formatting that change no value |
| Updates to `tests/test_contracts.py` | Complete the Python–TypeScript mirror assertion of T-24 |

## Task

1. Declare in `src/types.ts` exactly the types from the class diagram's mirror table:
   `Mode`, `TrafficSpeed`, `RequestState`, `LatLngPoint`, `RouteBounds`, `TrafficInterval`,
   `Scenario`, `WeatherState`, `PriceFactors`, `RoadSegment`, `RouteOption`, `PlanResult`,
   `MapConfig`, `ApiError`, plus any request body type the client needs. `PlanResult` is the
   TypeScript name for the `PlanResponse` body. `ApiError` is
   `{ detail: string; code: string; fields?: string[] }`. Do not add an API type the Python models do
   not have.
2. Field names on the wire stay snake_case to match the Python models. Do not camelCase a response
   field at the type boundary; formatting and presentation happen in components.
3. Implement `src/api/client.ts` with `postPlan`, `getMapConfig`, and `getHealth`. Each method:
   - accepts an `AbortSignal`;
   - parses a non-2xx body into `ApiError` by reading `detail` and `code` (and `fields` when present);
   - never branches on message text;
   - never logs or stores a credential;
   - talks only to `/api/...` so the Vite proxy and the production same-origin serve both work.
4. Put the three scenario defaults in `src/constants/scenario.ts` as `DEFAULT_HOUR = 17`,
   `DEFAULT_WEATHER = 1`, `DEFAULT_CONGESTION = 56`. This is the one intentional duplication with
   Python. Extend T-24 or add a small colocated test so a drift between the two sets fails the suite.
5. Implement `src/utils/format.ts` for currency (two decimal places, US dollars), distance (one
   decimal place, miles), and duration (one decimal place, minutes). Formatting changes no value and
   performs no fare, ETA, or score arithmetic.
6. Complete the T-24 mirror assertion so a field added to one side and missing from the other fails.

## Boundaries

- No coefficient, fare rate, BPR number, weather multiplier, or score weight in any file under `src/`
  (R3, NFR-5.3).
- No `fetch` call outside `src/api/client.ts`. Hooks will call the client; components will not.
- No Maps JavaScript API import (R7).
- No mode comparison that decides policy. A `Mode` union type is fine; branching on mode to hide
  scenario controls is presentation and belongs in a later component, not here.
- Do not invent a camelCase overlay type that renames wire fields.

## Tests To Write

| Test ID | Level | Target file | Assertion |
|---------|-------|-------------|-----------|
| T-24 (completion) | api / unit | `tests/test_contracts.py` and/or a colocated client test | Python and TypeScript field sets match; scenario defaults equal the Python defaults |
| Client unit coverage | unit | `src/api/client.test.ts` | Non-2xx bodies parse into `ApiError` by `code`; abort rejects cleanly |

## Definition Of Done

- [ ] `src/types.ts` declares every type in the mirror table and no extra API type.
- [ ] Wire field names match the Python models exactly.
- [ ] The client parses the error envelope by `code` and supports `AbortSignal`.
- [ ] Scenario defaults equal `DEFAULT_HOUR`, `DEFAULT_WEATHER`, and `DEFAULT_CONGESTION`.
- [ ] `format.ts` changes no numeric value and performs no domain arithmetic.
- [ ] T-24's mirror assertion fails when either side drifts.
- [ ] No file under `src/` contains a fare rate, BPR coefficient, weather multiplier, or score weight.
- [ ] `npm test` and `npm run build` pass for the files this package owns.
- [ ] `python -m pytest` still passes.

## Handoff

Report the complete TypeScript type list, the client method signatures, how the mirror assertion is
implemented, and any Python field whose TypeScript expression was ambiguous.
