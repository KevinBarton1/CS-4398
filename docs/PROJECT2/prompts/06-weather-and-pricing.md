# Prompt 06 — Weather And Pricing

**Wave:** 1 — Model
**Depends on:** prompts 01, 02
**Phase:** P1
**Read first:** [00-shared-context.md](00-shared-context.md)

## Read First

1. [00-shared-context.md](00-shared-context.md)
2. [../srs-context/model/weather-scenarios.md](../srs-context/model/weather-scenarios.md)
3. [../srs-context/model/pricing.md](../srs-context/model/pricing.md)
4. [../srs-context/model/configuration.md](../srs-context/model/configuration.md), the pricing and weather catalogs
5. [../README.md](../README.md), the `WeatherState` and `PriceFactors` tables and "Where the time-of-day factor applies"

## Objective

Build the two Model services that turn scenario inputs into the weather state and the illustrative
fare. Both are pure: severity in, `WeatherState` out; distance, minutes, congestion, and multipliers
in, `PriceEstimate` out. Neither knows about modes, HTTP, or Google.

## Deliverables

| File | Responsibility |
|------|----------------|
| `TrafficSImulation/app/weather/service.py` | `WeatherService.state(severity) -> WeatherState` |
| `TrafficSImulation/app/pricing/model.py` | `PricingModel.estimate(...) -> PriceEstimate` |
| `TrafficSImulation/tests/test_weather.py` | T-16 |
| `TrafficSImulation/tests/test_pricing.py` | T-15 |

## Task

1. Implement `WeatherService.state(severity: int) -> WeatherState`:
   - Clamp severity into 0–3.
   - Look up `label` from `WEATHER_LABELS`, `time_multiplier` from `WEATHER_TIME_MULTIPLIERS`, and
     `price_multiplier` from `WEATHER_PRICE_MULTIPLIERS`.
   - Set `source` to `WEATHER_SOURCE_SIMULATED`. There is no live weather API in PROJECT2.
   - Return a fully populated `WeatherState` with every field always present.
2. Implement `PricingModel.estimate(distance_miles, minutes, congestion_score, weather_price_multiplier, time_multiplier) -> PriceEstimate`:
   - Compute the route subtotal from `BASE_FARE`, `PER_MILE_RATE`, and `PER_MINUTE_RATE`.
   - Compute the traffic multiplier as `1 + congestion_score / PRICE_CONGESTION_DIVISOR`.
   - Multiply by the weather and time multipliers supplied by the caller. Do not look up the
     time-of-day factor yourself; orchestration and the mode policy decide which value to pass.
   - Produce `PriceFactors` with all five fields always present: `route_subtotal`,
     `traffic_multiplier`, `weather_multiplier`, `time_multiplier`, `unrounded_total`.
     `time_multiplier` is `1.0` when no time-of-day factor applies, never absent and never null.
   - Apply `MINIMUM_FARE` as a floor on the rounded price. `estimated_price` is two decimal places.
   - The factors must reproduce `unrounded_total`, and rounding `unrounded_total` after the floor must
     equal `estimated_price`.
3. Import every coefficient and every fixed string from `app/config/__init__.py`.
4. Write T-16: severity 0 through 3 map to the documented labels and multipliers; an out-of-range
   severity clamps; `source` is the locked simulated string.
5. Write T-15: the fare formula against a known input, factor reproduction of `unrounded_total`, the
   minimum fare floor, and a case where `time_multiplier` is `1.0`. Expected money values are literals
   written to two decimal places.

## Boundaries

- No HTTP, no FastAPI, no `app/api/` import (R1).
- Do not decide the mode. Weather severity comes from the effective scenario; the time multiplier
  comes from the caller. Mode policy owns those decisions.
- Do not present a fare as an official Uber or Lyft quotation. The service produces an illustrative
  estimate; the View's disclaimer is prompt 17's job, but the numbers themselves must stay honest.
- Do not call a live weather API. Severity 0–3 is the whole interface.
- Do not omit a `PriceFactors` field. Every field is always present.

## Tests To Write

| Test ID | Level | Target file | Assertion |
|---------|-------|-------------|-----------|
| T-15 | unit | `tests/test_pricing.py` | Fare formula, factor reproduction, minimum fare floor |
| T-16 | unit | `tests/test_weather.py` | Severity to label and multipliers, clamping, and `source` |

## Definition Of Done

- [ ] Every severity 0–3 produces the documented label and both multipliers.
- [ ] Out-of-range severity clamps rather than raising.
- [ ] `WeatherState.source` is the locked simulated string.
- [ ] Every `PriceFactors` field is always present; `time_multiplier` is never null.
- [ ] Factors reproduce `unrounded_total`, and the floored, rounded price equals `estimated_price`.
- [ ] The minimum fare floor applies when the computed fare falls below it.
- [ ] Every coefficient is imported from configuration.
- [ ] T-15 and T-16 pass with literal expected values.
- [ ] `python -m pytest` passes.

## Handoff

Report the public signatures, the sample inputs and expected fares from T-15 so prompt 10 can reuse
them, and any formula wording in the pricing document that disagreed with the coefficient catalog.
