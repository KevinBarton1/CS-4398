# Model Context — Traffic Simulation

**Layer:** Model  
**Codebase:** `TrafficSImulation/app/traffic_simulator.py`, scoring in `app/routes.py`  
**Related:** [config.md](config.md), [data-models.md](data-models.md), [controller/orchestration.md](../controller/orchestration.md)

## Purpose

Generate simulated traffic congestion, compute link travel times via the Bureau of Public Roads (BPR) function, derive road-segment statistics, and support heatmap intensity calculations.

## SRS Requirements

| ID | Requirement | Implementation |
|----|-------------|----------------|
| — | Generate simulated traffic using velocity, density, lane capacity, grid coordinates | `create_segments`, `heatmap_grid` |
| FR-2.3 | Display adjusted travel time after modifiers | BPR + weather × time-of-day in orchestration |
| FR-2.4 | Segment length, lanes, speed limit, average speed, volume, congestion | `create_segments` |
| FR-4.3 | Recalculate ETA when mode changes | Called from `plan_route` |
| FR-5.5 | Bad weather as configurable time debuff | Applied in orchestration via weather multipliers |
| FR-5.6 | Update results after variable changes | Frontend debounce triggers re-plan |
| 6.5 | Moving jams — simplified low-speed/high-density model | Partially via BPR at high flow/capacity ratios |

## Core Algorithms

### Time of Day Factor (`time_of_day_factor`)

| Hour range | Multiplier | Rationale |
|------------|------------|-----------|
| 7–9, 16–18 | 1.22 | Rush hour |
| 0–5, 22–23 | 0.92 | Off-peak |
| Other | 1.0 | Normal |

Input clamped to 0–23.

### BPR Link Performance (`bpr_adjusted_time`)

```
adjusted = free_flow × (1 + α × (flow / capacity)^β)
```

Constants from [config.md](config.md): `BPR_ALPHA = 0.15`, `BPR_BETA = 4`.

**Acceptance:**
- Zero flow → adjusted time equals free-flow time (T-10 backend test).
- Higher flow → monotonically higher adjusted time.

### Segment Creation (`create_segments`)

For each route (3 alternatives):

1. Split route distance ~47% / ~53% across two named roads from `route["road_names"]`.
2. Compute local congestion: `congestion + (segment_index × 11) − (route_index × 9)`, clamped 5–98.
3. Assign speed limit (45/55 mph) and lanes (3/4) by segment index.
4. Capacity = `lanes × BASE_LANE_CAPACITY` (520 veh/hr/lane).
5. Flow = `capacity × local_congestion / 100`.
6. Free-flow minutes = `length / speed_limit × 60`.
7. Average speed = max(`MINIMUM_CRAWL_SPEED_MPH`, length / (adjusted_minutes / 60)).

Route-level adjusted ETA = sum of segment `adjusted_minutes` + 2 min buffer, then × weather time multiplier × time-of-day factor.

### Route Scoring (`routes.py`)

Normalized score (lower is better):

```
score = w_time × (eta / max_eta)
      + w_distance × (distance / max_distance)
      + w_congestion × (congestion / max_congestion)
      − w_demand × (demand / 100)
```

Weights in `ROUTE_SCORE_WEIGHTS` ([config.md](config.md)). Recommended route = minimum score.

### Heatmap Grid (`heatmap_grid`)

5×8 grid of cells with values 3–100. Formula varies by mode:

| Mode | Formula (simplified) |
|------|---------------------|
| congestion | `congestion × 0.66 + wave + center × 0.35` |
| demand | `demand × 0.62 + wave + center` |
| profitability | `demand × 0.72 + wave + center − congestion × 0.25` |

`wave` = sinusoidal variation by row/column/hour; `center` = distance from grid center.

Wrapped by `heatmap.build_heatmap` which validates mode and returns empty cells when `off`.

## Three Route Objectives

From `map_service.build_route_options`:

| Index | Name | Objective | Offset |
|-------|------|-----------|--------|
| 0 | Fastest | Minimum adjusted time | 0 |
| 1 | Balanced | Weighted time, distance, congestion, demand | +68 |
| 2 | Low traffic | Minimum congestion exposure | −92 |

Each route has distinct distance (+9% per index), average speed, color, and road name pair.

## Acceptance Criteria

- [ ] Adverse conditions (high congestion, severe weather) increase adjusted ETA monotonically (T-4, T-5).
- [ ] Each route has ≥2 segments with plausible capacity, flow, and congestion values.
- [ ] BPR raises travel time as flow approaches capacity.
- [ ] Heatmap values respond to congestion/demand/hour changes (T-5, T-6).
- [ ] Simulation completes without external API calls (NFR-3.4 for local-only changes).

## Non-Functional

| ID | Requirement |
|----|-------------|
| NFR-3.2 | Scenario slider changes should reflect within ~2 seconds (frontend 180ms debounce + API) |
| NFR-4.1 | Map display separated from simulation (simulation has no rendering) |
| NFR-4.5 | Unit tests for BPR and ETA monotonicity in `test_backend.py` |

## Agent Implementation Notes

- Keep all coefficients in `app/config.py`, not inline.
- `traffic_simulator.py` must not import view or HTTP layers.
- SRS mentions "moving jams"; current model uses static BPR congestion per segment. A future enhancement could animate jam regions on the grid without changing the BPR core.
- When integrating live traffic APIs, preserve simulated fallback path for offline/reference mode.
