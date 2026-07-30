# Prompt 02 — Configuration And Coefficients

**Wave:** 0 — Foundation
**Depends on:** prompt 01
**Phase:** P1
**Read first:** [00-shared-context.md](00-shared-context.md)

## Read First

1. [00-shared-context.md](00-shared-context.md)
2. [../srs-context/model/configuration.md](../srs-context/model/configuration.md) — read all of it; it is the catalog you are transcribing
3. [../README.md](../README.md), sections "Scenario variables", "Shared value objects", "`GET /api/map/config` response", "Where the time-of-day factor applies"
4. [../srs-context/controller/external-service-boundaries.md](../srs-context/controller/external-service-boundaries.md)
5. [../srs-context/architecture/architecture-overview.md](../srs-context/architecture/architecture-overview.md), section "Trust Boundaries And Credentials"

## Objective

Build `app/config/__init__.py` as the single source of truth for every tunable number, every fixed
string that appears in a response body, and every environment-derived setting. Every later package
imports from here rather than declaring a literal.

This package lands before any domain module on purpose: a coefficient that arrives after its consumer
gets inlined at the call site with a plan to extract it later, and the extraction never happens.

## Deliverables

| File | Responsibility |
|------|----------------|
| `TrafficSImulation/app/config/__init__.py` | `Settings` plus every coefficient, URL, timeout, and locked response string |
| `TrafficSImulation/tests/test_config.py` | T-54 |

## Task

1. Declare `Settings` as a `BaseSettings` subclass with `google_maps_api_key`,
   `google_maps_browser_api_key`, and `google_maps_map_id`, bound to `GOOGLE_MAPS_API_KEY`,
   `GOOGLE_MAPS_BROWSER_API_KEY`, and `GOOGLE_MAPS_MAP_ID`, with the documented defaults. Add the
   derived `google_maps_configured` property, which treats an empty or whitespace-only server key as
   absent.
2. Load `TrafficSImulation/.env` at import so `python main.py` and `python -m pytest` behave
   identically. Instantiate `Settings` once at import. A missing credential must not raise at import:
   the application has to start, `GET /api/health` has to answer, and only `POST /api/plan` may fail
   with `maps_not_configured`.
3. Transcribe the entire coefficient catalog from
   [../srs-context/model/configuration.md](../srs-context/model/configuration.md) as module-level
   constants: pricing, traffic and segments, weather, route identity and scoring, scenario defaults,
   Google integration, response strings, and browser map configuration. Values must match the catalog
   exactly. Do not round, reorder, or rename.
4. Define the P3 heatmap constants only if the catalog marks them as defined when P3 is taken up;
   otherwise leave them for prompt 24 and say so in your handoff.
5. Keep `Settings` and the coefficients separate in the module, with a comment stating the distinction
   only if the code cannot: `Settings` is what the deployment supplies, constants are what the domain
   model asserts. A coefficient is never an environment variable, because making one configurable per
   deployment would make responses irreproducible across instances.
6. Never log, echo, or serialize `google_maps_api_key`. If a diagnostic needs it, log its presence as a
   boolean.
7. Write `tests/test_config.py` covering T-54 as described in the catalog's Planned Tests table:
   - every documented constant exists with its documented value, written as a literal in the test;
   - `WEATHER_TIME_MULTIPLIERS`, `WEATHER_PRICE_MULTIPLIERS`, and `WEATHER_LABELS` each have exactly
     four entries;
   - `SEGMENT_SPEED_LIMITS_MPH` and `SEGMENT_LANE_COUNTS` each have exactly `SEGMENT_COUNT_MAX` entries;
   - `ROUTE_COLORS`, `ROUTE_NAMES`, and `ROUTE_OBJECTIVES` each have exactly `ROUTE_ALTERNATIVES_MAX`
     entries;
   - `ROUTE_SCORE_WEIGHTS` has exactly the keys `time`, `distance`, and `congestion`, with values
     summing to 1.0;
   - `Settings` treats an empty and a whitespace-only server key as not configured;
   - a narrow source scan finds no fare rate, BPR coefficient, weather multiplier, score weight,
     timeout, or locked response string as a literal anywhere under `app/` outside
     `app/config/__init__.py`. Match the specific documented values so the scan does not fail on an
     unrelated numeric literal.
8. Leave the two assertions that need HTTP for prompt 11 and note them in your handoff: an absent
   server key yielding 503 `maps_not_configured` from `POST /api/plan`, and `GET /api/map/config`
   returning the browser key and never the server key.

## Boundaries

- This is the only module in the system that reads an environment variable (R5).
- Do not import anything from `app/api/`, FastAPI, or `main`. `Settings` is a Model type (R1).
- Do not add a coefficient the catalog does not list, and do not omit one it does.
- Do not add a runtime tuning interface or a per-request coefficient override. Both are out of scope.
- Do not put a scenario default in TypeScript here. `src/constants/scenario.ts` is prompt 13's
  deliberate duplication, and prompt 13 owns the test that keeps the two sets equal.

## Tests To Write

| Test ID | Level | Target file | Assertion |
|---------|-------|-------------|-----------|
| T-54 | unit | `tests/test_config.py` | Documented constants, tuple lengths, weight keys and sum, whitespace-key handling, and the no-literals source scan |

## Definition Of Done

- [ ] Every coefficient in the catalog is defined exactly once, with the catalog's value.
- [ ] `ROUTE_SCORE_WEIGHTS` has exactly three keys whose values sum to 1.0.
- [ ] The three weather tuples have exactly four entries each.
- [ ] `Settings` reads all three environment variables and treats a whitespace-only key as absent.
- [ ] Importing `app.config` with no credentials set does not raise.
- [ ] No code path logs or serializes the server credential.
- [ ] `map_id` resolves to `None` when `GOOGLE_MAPS_MAP_ID` is unset.
- [ ] `tests/test_config.py` passes and its expected values are written as literals.
- [ ] `python -m pytest` passes.

## Handoff

Report the constant list you defined grouped by catalog section, any catalog entry whose value or unit
was ambiguous, whether you deferred the P3 constants, and the T-54 assertions you left to prompt 11.
