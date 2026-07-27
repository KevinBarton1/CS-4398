# Model Context — Pricing Model

**Layer:** Model  
**Codebase:** `TrafficSImulation/app/pricing_model.py`, `TrafficSImulation/app/config.py`  
**Related:** [config.md](config.md), [weather.md](weather.md), [data-models.md](data-models.md)

## Purpose

Estimate an illustrative Uber/Lyft-like upfront price for route planning. The estimate is **not** an official fare (FR-6.5, scope constraint 6.6).

## SRS Requirements

| ID | Requirement | Implementation |
|----|-------------|----------------|
| FR-6.1 | Estimate using distance and travel time | `BASE_FARE + miles × PER_MILE + minutes × PER_MINUTE` |
| FR-6.2 | Configurable congestion, weather, time, demand multipliers | Applied in `estimate_price` |
| FR-6.3 | Display in pricing panel | View consumes `estimated_price` |
| FR-6.4 | Display major contributing factors | `factors` dict returned with route |
| FR-6.5 | State estimates are not official fares | UI disclaimer + response `notice` |
| T-10 | Price differs by distance/time across routes | Verified in test plan |

## Formula (`estimate_price`)

```python
subtotal = BASE_FARE + distance_miles × PER_MILE_RATE + minutes × PER_MINUTE_RATE
demand_multiplier = 1 + max(0, demand − 40) / 150
congestion_multiplier = 1 + congestion / 500
total = subtotal × demand_multiplier × congestion_multiplier × weather_multiplier × time_factor
final = max(MINIMUM_FARE, total)
return round(final, 2), factors
```

### Default Coefficients (config.py)

| Constant | Value |
|----------|-------|
| `BASE_FARE` | $2.20 |
| `PER_MILE_RATE` | $1.28 |
| `PER_MINUTE_RATE` | $0.31 |
| `MINIMUM_FARE` | $7.50 |

### Factors Dict (FR-6.4)

| Key | Description |
|-----|-------------|
| `route_subtotal` | Pre-multiplier base |
| `demand_multiplier` | From simulated demand 0–100 |
| `traffic_multiplier` | Congestion-based (named traffic in UI) |
| `weather_multiplier` | From weather service |
| `time_multiplier` | Time-of-day factor |
| `unrounded_total` | Final before display rounding |

## Inputs

Called from `plan_route` with:

- `distance_miles` — from route geometry
- `minutes` — raw adjusted ETA before rounding (for precision)
- `congestion` — route-level congestion score
- `demand` — scenario demand 0–100
- `weather_multiplier` — from `weather_adjustment`
- `time_factor` — from `time_of_day_factor`

## Acceptance Criteria

- [ ] `estimated_price` equals `round(subtotal × all multipliers, 2)` capped at minimum fare.
- [ ] Higher demand increases price when demand > 40.
- [ ] Higher congestion increases price.
- [ ] Severe weather increases price via weather multiplier.
- [ ] Rush-hour time factor increases price.
- [ ] UI shows factor breakdown and disclaimer text.
- [ ] Missing route values must not produce misleading estimates (FR-6 alternate flow) — orchestration should not call pricing without valid distance/time.

## Alternate Flows (SRS FR-6)

| Condition | Expected behavior |
|-----------|-------------------|
| Missing distance/time | Do not display estimate; handle at orchestration layer |
| Invalid multiplier | Use documented defaults; warn user (not yet implemented in UI) |

## Non-Functional

| ID | Requirement |
|----|-------------|
| NFR-4.2 | Pricing separated from UI — only `pricing_model.py` contains formula |
| NFR-4.5 | Unit test reproduces price from factors (`test_pricing_breakdown_reproduces_final_estimate`) |

## Agent Implementation Notes

- All rate constants belong in `config.py`.
- Do not claim official Uber/Lyft pricing anywhere in model or API strings.
- If adding surge or zone bonuses, extend `factors` dict and TS `PriceFactors` interface together.
- Reference mode uses same pricing formula with reference congestion/demand values.
