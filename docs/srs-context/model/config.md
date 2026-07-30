# Model Context — Configuration

**Layer:** Model  
**Codebase:** `TrafficSImulation/app/config.py`  
**Related:** All model context files

## Purpose

Single source of truth for simulation coefficients, pricing rates, weather multipliers, and route scoring weights (AGENTS.md, NFR-4.4).

## SRS Alignment

| SRS reference | Config responsibility |
|---------------|----------------------|
| FR-5.5, FR-6.2 | Configurable multipliers |
| 6.2 Naming | Constants UPPER_SNAKE_CASE |
| 6.5 Simulation constraints | Documented tunable parameters |
| NFR-4.4 | Consistent naming |

## Current Constants

### Pricing

```python
BASE_FARE = 2.20
PER_MILE_RATE = 1.28
PER_MINUTE_RATE = 0.31
MINIMUM_FARE = 7.50
```

### Traffic / BPR

```python
BPR_ALPHA = 0.15
BPR_BETA = 4
BASE_LANE_CAPACITY = 520      # vehicles per hour per lane
MINIMUM_CRAWL_SPEED_MPH = 6.0
```

### Weather

```python
WEATHER_TIME_MULTIPLIERS = (1.0, 1.08, 1.18, 1.32)
WEATHER_PRICE_MULTIPLIERS = (1.0, 1.03, 1.07, 1.12)
WEATHER_LABELS = ("Clear", "Light rain", "Heavy rain", "Severe")
```

### Route Recommendation Weights

```python
ROUTE_SCORE_WEIGHTS = {
    "time": 0.42,
    "distance": 0.18,
    "congestion": 0.25,
    "demand": 0.15,
}
```

Lower normalized score = better recommended route.

## Default Scenario Values

Used by frontend (`App.tsx`) and API defaults (`PlanRequest`):

| Parameter | Default |
|-----------|---------|
| hour | 17 (5 PM) |
| weather | 1 (Light rain) |
| congestion | 56 |
| demand | 68 |

Reference mode overrides in orchestration: congestion=44, demand=52, weather=0.

## Acceptance Criteria

- [ ] No magic numbers duplicated in simulator, pricing, or weather modules.
- [ ] Changing a constant affects behavior predictably (tests should still pass or be updated intentionally).
- [ ] Weather tuple lengths match severity range 0–3.

## Agent Implementation Notes

- Add new coefficients here first, then import where needed.
- Do not import config from view layer.
- If exposing admin tuning UI, still persist canonical values server-side.
