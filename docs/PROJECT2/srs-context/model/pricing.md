# Model Context — Pricing

**Layer:** Model  
**Target modules:** `app/pricing/model.py`  
**Related:** [README.md](../../README.md), [domain-contracts.md](domain-contracts.md), [route-planning.md](route-planning.md), [traffic-simulation.md](traffic-simulation.md), [weather-scenarios.md](weather-scenarios.md), [configuration.md](configuration.md)

## Purpose

Produce an illustrative rideshare-style fare estimate for one route, together with a breakdown that
reproduces it exactly. The estimate is a planning figure. It is not an Uber fare, not a Lyft fare, and not a
quote.

## Requirements

| ID | Requirement | Status | Phase |
|----|-------------|--------|-------|
| FR-6.1 | Estimate a fare from route distance and travel time and report it per route as `estimated_price` in US dollars | Target | P1 |
| FR-6.2 | Apply configurable traffic, weather, and time-of-day multipliers and report them as `price_factors` | Target | P1 |
| FR-6.3 | Never report an estimate below the configured minimum fare | Target | P1 |
| FR-6.4 | Make the breakdown reproduce the displayed estimate | Target | P1 |
| FR-6.5 | State that estimates are illustrative and not official rideshare fares | Target | P1 |
| NFR-2.5 | Do not report an estimate derived from a missing distance or duration | Target | P1 |
| NFR-5.2 | The fare formula exists in exactly one Model module | Target | P1 |
| NFR-6.2 | A unit test recomputes the estimate from `price_factors` alone | Target | P1 |
| NFR-7.2 | The View shows the breakdown and the disclaimer alongside the estimate | Target | P1 |
| — | Payment processing, surge pricing tied to real market data, and official carrier fares | Out of scope | — |

## `PricingModel`

`app/pricing/model.py` exposes one class with one public method. It is pure: no clock, no I/O, no
configuration lookups beyond the module-level coefficient imports.

```python
class PricingModel:
    def estimate(
        self,
        distance_miles: float,
        minutes: float,
        congestion_score: int,
        weather_price_multiplier: float,
        time_multiplier: float,
    ) -> PriceEstimate:
        ...
```

| Parameter | Unit | Source |
|-----------|------|--------|
| `distance_miles` | miles | `RouteOption.distance_miles`, from the Google route distance |
| `minutes` | minutes | the unrounded adjusted ETA from [route-planning.md](route-planning.md) |
| `congestion_score` | percent, 4–100 | `RouteOption.congestion_score` |
| `weather_price_multiplier` | dimensionless | `WeatherState.price_multiplier` |
| `time_multiplier` | dimensionless | `1.0` in Simulated mode, `time_of_day_factor(hour)` in Real-Time mode |

`PriceEstimate` carries the rounded `total` and the `PriceFactors` breakdown. The caller assigns them to
`RouteOption.estimated_price` and `RouteOption.price_factors`.

`time_multiplier` is a required parameter with no default. Making the caller state the value forces the mode
decision to be explicit at the call site rather than hidden behind an optional argument, and it is why
`PriceFactors.time_multiplier` is always present.

`minutes` is the unrounded adjusted ETA rather than the one-decimal display value, so the fare does not
inherit display rounding.

## Fare Formula

```
route_subtotal      = BASE_FARE + distance_miles * PER_MILE_RATE + minutes * PER_MINUTE_RATE
traffic_multiplier  = 1 + congestion_score / 500
unrounded_total     = max(MINIMUM_FARE,
                          route_subtotal * traffic_multiplier
                                         * weather_multiplier
                                         * time_multiplier)
estimated_price     = round(unrounded_total, 2)
```

### Coefficients

| Constant | Value | Unit | Meaning |
|----------|-------|------|---------|
| `BASE_FARE` | 2.20 | US dollars | Flat pickup charge |
| `PER_MILE_RATE` | 1.28 | dollars per mile | Distance rate |
| `PER_MINUTE_RATE` | 0.31 | dollars per minute | Time rate |
| `MINIMUM_FARE` | 7.50 | US dollars | Floor applied after all multipliers |

All four live in `app/config/__init__.py`. None is written as a literal in `app/pricing/model.py`.

### Multipliers

| Multiplier | Formula or source | Range | Notes |
|------------|-------------------|-------|-------|
| `traffic_multiplier` | `1 + congestion_score / 500` | 1.008 to 1.200 | Divisor 500 caps the traffic surcharge at 20 percent at full congestion |
| `weather_multiplier` | `WEATHER_PRICE_MULTIPLIERS[severity]` | 1.00 to 1.12 | See [weather-scenarios.md](weather-scenarios.md) |
| `time_multiplier` | `1.0` in Simulated mode, `time_of_day_factor(hour)` in Real-Time mode | 0.92, 1.0, or 1.22 | Never absent, never null |

Multipliers compose by multiplication, so the maximum combined uplift is `1.200 * 1.12 * 1.22`, about 1.64.
The composition is unordered: floating-point multiplication reorders harmlessly at this precision, and the
tests assert on the product rather than on an intermediate.

`traffic_multiplier` is named for what the user sees on the route card. It is derived from
`congestion_score`, which is a 0–100 integer, not from the 0.0–1.0 `RoadSegment.congestion` fraction.

### Why `time_multiplier` differs by mode

| Mode | `time_multiplier` | Reason |
|------|-------------------|--------|
| `simulated` | `1.0` | The scenario's departure hour is already sent to Google as `departureTime`, so it is reflected in the traffic-aware duration that feeds `minutes`. A time-of-day multiplier on top would price rush hour twice |
| `realtime` | `time_of_day_factor(local departure hour)` | Real-Time mode does not apply the scenario, so the peak-period uplift is not otherwise represented in the fare, and a rideshare fare at 8 AM is genuinely higher than the same trip at noon |

Both modes therefore report a real value in `price_factors.time_multiplier`; `1.0` in Simulated mode is a
stated result, not a missing value.

## Minimum Fare Behavior

`MINIMUM_FARE` is applied after every multiplier, so the floor is the last word.

| Step | Behavior |
|------|-----------|
| Apply all multipliers to the subtotal | Produces the raw total |
| Take `max(MINIMUM_FARE, raw_total)` | Produces `unrounded_total` |
| Round to two decimals | Produces `estimated_price` |

Consequences the tests pin down:

- When the floor binds, `unrounded_total` equals `MINIMUM_FARE` exactly and `estimated_price` is `7.50`.
- When the floor binds, raising congestion or weather severity does not change the estimate. This is
  correct: a very short trip prices at the minimum regardless of conditions.
- The floor is applied once. It is not applied to the subtotal and then again to the total.
- `route_subtotal` in the breakdown is always the pre-multiplier subtotal, never the floored value, so a
  reader can see why the floor bound.

Rounding uses a `1e-9` epsilon before `round`, because a total held as `29.504999999` would otherwise round
down and break the reproducibility assertion by a cent.

## `PriceFactors` Breakdown

All five fields are always present, at full float precision, in both modes.

| Field | Meaning | Unit |
|-------|---------|------|
| `route_subtotal` | `BASE_FARE + distance * PER_MILE_RATE + minutes * PER_MINUTE_RATE`, before any multiplier | US dollars |
| `traffic_multiplier` | Congestion surcharge factor | dimensionless |
| `weather_multiplier` | Weather surcharge factor | dimensionless |
| `time_multiplier` | Time-of-day factor, `1.0` when none applies | dimensionless |
| `unrounded_total` | Post-multiplier, post-floor total before display rounding | US dollars |

The breakdown holds unrounded values on purpose. Rounding the subtotal and the multipliers for display and
then multiplying them would not reproduce `estimated_price`, which is exactly the failure FR-6.4 forbids.
The View rounds for presentation and never recomputes the fare.

There is no field named `factors`. The contract name is `price_factors`.

## Reproducibility Requirement

Given only `price_factors`, this identity must hold:

```
round(max(MINIMUM_FARE,
          route_subtotal * traffic_multiplier * weather_multiplier * time_multiplier),
      2) == estimated_price
```

and, equivalently:

```
round(unrounded_total, 2) == estimated_price
```

Both are asserted, because the first proves the multipliers are the ones actually used and the second proves
`unrounded_total` is the value actually rounded. A change that satisfies only one of them is a regression.

### Worked examples

Simulated mode, distance 12.4 miles, adjusted ETA 24.8 minutes, congestion score 56, weather severity 1.

| Quantity | Value |
|----------|-------|
| `route_subtotal` | `2.20 + 12.4 * 1.28 + 24.8 * 0.31` = 25.76 |
| `traffic_multiplier` | `1 + 56 / 500` = 1.112 |
| `weather_multiplier` | 1.03 |
| `time_multiplier` | 1.0 |
| raw total | `25.76 * 1.112 * 1.03 * 1.0` = 29.5044736 |
| `unrounded_total` | 29.5044736 |
| `estimated_price` | 29.50 |

Real-Time mode, distance 12.4 miles, adjusted ETA 22.0 minutes, congestion score 4, weather severity 0,
local departure hour 17.

| Quantity | Value |
|----------|-------|
| `route_subtotal` | `2.20 + 12.4 * 1.28 + 22.0 * 0.31` = 24.892 |
| `traffic_multiplier` | `1 + 4 / 500` = 1.008 |
| `weather_multiplier` | 1.0 |
| `time_multiplier` | 1.22 |
| raw total | `24.892 * 1.008 * 1.0 * 1.22` = 30.6111859 |
| `unrounded_total` | 30.6111859 |
| `estimated_price` | 30.61 |

Minimum fare binding, distance 0.6 miles, adjusted ETA 3.0 minutes, congestion score 4, weather severity 0,
Simulated mode.

| Quantity | Value |
|----------|-------|
| `route_subtotal` | `2.20 + 0.6 * 1.28 + 3.0 * 0.31` = 3.898 |
| `traffic_multiplier` | 1.008 |
| raw total | 3.9291840 |
| `unrounded_total` | 7.50 |
| `estimated_price` | 7.50 |

## Missing Input Handling

`PricingModel` is not the guard for absent route data. The orchestration layer must not call it without a
positive distance and a positive duration; the duration fallback chain in
[route-planning.md](route-planning.md) guarantees a duration before pricing runs.

| Condition | Behavior |
|-----------|-----------|
| `distance_miles` <= 0 | Raises; a zero-length route is a `no_route_found` condition upstream |
| `minutes` <= 0 | Raises; the duration fallback chain should have produced a value |
| Any multiplier <= 0 | Raises; a non-positive multiplier is a programming error |

Raising is correct here rather than substituting a default, because a fare silently computed from a
defaulted duration is a misleading number presented as a price. NFR-2.5 requires the request to fail instead.

## Disclaimer Requirement

Every surface that shows a fare states that it is illustrative.

| Surface | Requirement |
|---------|-------------|
| Route card and price panel | A visible disclaimer accompanies `estimated_price`, stating that it is an illustrative planning estimate and not an official rideshare fare |
| Response `notice` | Names the data provenance for the mode, always present and non-empty |
| `data_source` per route | Names Google Routes as the source of geometry and timing |
| Model and API strings | Never claim, imply, or name an official Uber or Lyft fare |

The disclaimer text is a View string. The Model's obligation is that no field name, no `notice` value, and no
`data_source` value ever asserts an official fare.

## Acceptance Criteria

- [ ] `estimated_price` equals `round(route_subtotal * traffic_multiplier * weather_multiplier * time_multiplier, 2)` when that product is above `MINIMUM_FARE`.
- [ ] `estimated_price` equals `MINIMUM_FARE` when the product falls below it, and `unrounded_total` equals `MINIMUM_FARE` exactly.
- [ ] `round(unrounded_total, 2)` equals `estimated_price` for every route in every response.
- [ ] All five `PriceFactors` fields are present on every route in both modes.
- [ ] `price_factors.time_multiplier` is `1.0` for every route in Simulated mode.
- [ ] `price_factors.time_multiplier` equals `time_of_day_factor` at the local departure hour in Real-Time mode.
- [ ] Raising `congestion` raises `estimated_price` whenever the minimum fare is not binding.
- [ ] Raising weather severity raises `estimated_price` whenever the minimum fare is not binding.
- [ ] A longer route at equal conditions never prices below a shorter one.
- [ ] No response body contains a key named `factors`.
- [ ] `app/pricing/model.py` contains no numeric fare literal; every coefficient is imported from `app/config/__init__.py`.
- [ ] The price panel renders the subtotal, all three multipliers, the total, and the illustrative-estimate disclaimer.
- [ ] No Model or API string names an official Uber or Lyft fare.

## Planned Tests

| Test ID | Level | Target file | Assertion |
|---------|-------|-------------|-----------|
| T-15 | unit | `tests/test_pricing.py` | The three worked examples reproduce their documented subtotal, multipliers, `unrounded_total`, and `estimated_price`; recomputing from `price_factors` alone reproduces `estimated_price` and `round(unrounded_total, 2)` equals it; the minimum fare binds for a short trip and stays bound as congestion and weather severity rise; `estimated_price` increases monotonically across congestion scores 4, 40, and 100 above the fare floor; and a non-positive distance, duration, or multiplier raises rather than returning an estimate |
| T-22 | unit | `tests/test_mode_policy.py` | The mode policy yields `time_multiplier` `1.0` in Simulated mode and the time-of-day factor for the departure hour in Real-Time mode |
| T-38 | component | `src/components/PriceSummary.test.tsx` | The panel renders the subtotal, all three multipliers, the total, and the illustrative-estimate disclaimer |

## Agent Implementation Notes

- Keep every rate and the fare floor in `app/config/__init__.py`, including the traffic divisor of 500.
- `app/pricing/model.py` must not import `app/simulation/`, `app/map/`, `app/weather/`, or anything under
  `app/api/` beyond the shared `PriceFactors` model. It receives multipliers as arguments.
- Do not give `time_multiplier` a default value. An explicit argument is what keeps the mode decision visible
  and the breakdown complete.
- Compute from the unrounded adjusted ETA and round exactly once, when building the response model.
- Keep the `1e-9` epsilon in front of `round`; removing it reintroduces off-by-one-cent reproducibility
  failures on values that land just below a half cent.
- If a new factor is ever added, extend `PriceFactors`, `src/types.ts`, the reproducibility test, and the
  price panel in the same change, and update [domain-contracts.md](domain-contracts.md) and
  [README.md](../../README.md) first.
