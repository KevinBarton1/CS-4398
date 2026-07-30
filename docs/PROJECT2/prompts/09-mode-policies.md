# Prompt 09 — Mode Policies

**Wave:** 2 — Controller
**Depends on:** prompts 01, 02, 05, 06, 08
**Phase:** P1
**Read first:** [00-shared-context.md](00-shared-context.md)

## Read First

1. [00-shared-context.md](00-shared-context.md)
2. [../srs-context/controller/mode-policies.md](../srs-context/controller/mode-policies.md) — read all of it
3. [../README.md](../README.md), sections "Planning modes", "Where the time-of-day factor applies", and the locked notice and data-source strings
4. [../srs-context/architecture/class-diagram.md](../srs-context/architecture/class-diagram.md), `ModePolicy` and its implementations
5. [../srs-context/architecture/state-diagrams.md](../srs-context/architecture/state-diagrams.md), the mode transition diagram

## Objective

Build the only place in the system that interprets the mode string. `resolve_mode_policy` returns a
policy object; every mode-dependent decision is a method on that object. No other module may compare
against the literals `realtime` or `simulated`.

## Deliverables

| File | Responsibility |
|------|----------------|
| `TrafficSImulation/app/api/mode_policy.py` | `ModePolicy` interface, `SimulatedModePolicy`, `RealTimeModePolicy`, `resolve_mode_policy` |
| `TrafficSImulation/tests/test_mode_policy.py` | T-22 |

## Task

1. Declare the `ModePolicy` interface with the public surface from the class diagram:
   `mode`, `scenario_applied`, `alternatives`, `effective_scenario(request)`, `departure_time()`,
   `routing_preference()`, `adjusted_eta(route, weather, segments)`, `pricing_time_multiplier()`,
   `data_source()`, `notice()`.
2. Implement `SimulatedModePolicy`:
   - `scenario_applied` is `True`; `alternatives` is up to `ROUTE_ALTERNATIVES_MAX`.
   - `effective_scenario` passes the request's `hour`, `weather`, and `congestion` through.
   - `departure_time` is the next occurrence of `scenario.hour` in local Austin time.
   - `adjusted_eta` multiplies the chosen duration source by `weather.time_multiplier`. Duration
     source priority: traffic-aware duration, then static duration, then the sum of
     `RoadSegment.adjusted_minutes` plus `ETA_FALLBACK_BUFFER_MINUTES`.
   - `pricing_time_multiplier` returns `1.0`. The time-of-day factor is not applied to the Simulated
     fare, because the hour already shaped the ETA through Google's `departureTime`.
   - `data_source` is `DATA_SOURCE_SIMULATED`; `notice` is `NOTICE_SIMULATED`.
3. Implement `RealTimeModePolicy`:
   - `scenario_applied` is `False`; `alternatives` is exactly 1.
   - `effective_scenario` sets `hour` to the current local Austin hour, `weather` to 0, and
     `congestion` to 0. The request's scenario fields are accepted and then ignored.
   - `departure_time` is now.
   - `adjusted_eta` is the chosen duration source in minutes, with no weather factor and no
     time-of-day factor. Google's traffic-aware duration already reflects real congestion.
   - `pricing_time_multiplier` returns `time_of_day_factor` at the local departure hour. On the fare
     this factor represents time-of-day demand pricing, not travel time.
   - `data_source` is `DATA_SOURCE_REALTIME`; `notice` is `NOTICE_REALTIME`.
4. Implement `resolve_mode_policy(mode: str) -> ModePolicy`. This is the only function in the system
   that inspects the mode string. An unexpected value is a validation concern that should already have
   been rejected by `PlanRequest`; if one reaches here, raise rather than default.
5. Import every locked string and every coefficient from configuration. Import `time_of_day_factor`
   from `app/simulation/traffic.py`. Perform no arithmetic that belongs to a Model service beyond
   assembling the adjusted ETA from the documented sources.
6. Write T-22 as a behavior table covering both policies: alternatives count, `scenario_applied`,
   effective scenario shape, routing preference, adjusted-ETA formula including the three-level
   fallback, pricing time multiplier, data source, and notice. Expected notice and data-source strings
   are literals.

## Boundaries

- This is the only module that may contain a comparison against the literals `realtime` or
  `simulated` (R4). A grep of the rest of the repository for those literals must find them only in
  this file, in schema constraints, in tests, and in documentation.
- Do not put a coefficient literal here. Import from configuration.
- Do not raise HTTP exceptions. An unexpected mode is a programming error after validation.
- Do not call Google, build segments, or estimate fares. The policy decides; collaborators execute.

## Tests To Write

| Test ID | Level | Target file | Assertion |
|---------|-------|-------------|-----------|
| T-22 | unit | `tests/test_mode_policy.py` | The full mode policy behavior table for both policies, including the adjusted-ETA fallback chain |

## Definition Of Done

- [ ] `resolve_mode_policy` is the only production function that inspects the mode string.
- [ ] Simulated returns up to 3 alternatives with `scenario_applied` true; Real-Time returns exactly 1 with it false.
- [ ] Real-Time effective scenario is `{ hour: local, weather: 0, congestion: 0 }`.
- [ ] Simulated adjusted ETA multiplies by the weather time multiplier; Real-Time does not.
- [ ] Simulated pricing time multiplier is `1.0`; Real-Time uses `time_of_day_factor`.
- [ ] Notices and data sources match the locked strings exactly.
- [ ] The adjusted-ETA fallback prefers traffic-aware, then static, then segment sum plus buffer.
- [ ] T-22 passes with literal expected strings and numbers.
- [ ] `python -m pytest` passes.

## Handoff

Report the public surface, the Austin timezone you used for "local", and any mode-policies document
row that disagreed with the README's time-of-day table.
