# Model Context — Traffic Simulation

**Layer:** Model  
**Target modules:** `app/simulation/traffic.py`, `app/simulation/segments.py`  
**Related:** [README.md](../../README.md), [domain-contracts.md](domain-contracts.md), [route-planning.md](route-planning.md), [pricing.md](pricing.md), [weather-scenarios.md](weather-scenarios.md), [google-integrations.md](google-integrations.md), [configuration.md](configuration.md)

## Purpose

Own the two traffic physics functions and the segment builder: the Bureau of Public Roads link-performance
function, the time-of-day factor, and `SegmentBuilder`, which derives per-segment road statistics from the
legs and steps of a Google route.

This document also draws the line that the whole product depends on: Google's traffic intervals are
observed data passed through unchanged, while the segment statistics are a simulated planning model built on
top of Google's geometry and timings.

## Requirements

| ID | Requirement | Status | Phase |
|----|-------------|--------|-------|
| FR-2.7 | Report per-segment length, lane count, speed limit, average speed, volume, capacity, and congestion | Target | P1 |
| FR-2.9 | Distinguish observed Google data from simulated planning estimates in `data_source` | Target | P1 |
| FR-3.4 | Provide polyline index ranges with a speed category so the map can color traffic | Target | P1 |
| FR-5.3 | Let the congestion control move the segment model | Target | P1 |
| FR-2.6 | Treat adverse weather as a time penalty on the mode-adjusted ETA | Target | P1 |
| NFR-5.1 | Traffic physics live in a module with no HTTP, no Google payload parsing, and no rendering | Target | P1 |
| NFR-6.2 | BPR and the time-of-day factor are unit-testable as pure functions | Target | P1 |
| NFR-7.3 | Simulated segment statistics are surfaced with their route provenance so they read as planning estimates | Target | P1 |
| — | Per-segment incident modelling and moving-jam animation | Out of scope | — |

## Observed Data Versus Simulated Statistics

One route carries two independent congestion representations. They are not derived from each other and they
must not be presented as the same thing.

| Aspect | `RouteOption.traffic_intervals` | `RouteOption.segments` |
|--------|--------------------------------|------------------------|
| Origin | Google Routes speed reading intervals | `SegmentBuilder`, from Google geometry plus scenario congestion |
| Nature | Observed or Google-predicted traffic state | Simulated planning model |
| Granularity | Polyline index range | A contiguous named stretch of road |
| Congestion expression | `speed` enum in `{NORMAL, SLOW, TRAFFIC_JAM, SPEED_UNSPECIFIED}` | `congestion` fraction 0.0–1.0 plus flow and capacity in vehicles per hour |
| Depends on the scenario | No | Yes, through `Scenario.congestion` |
| Consumed by | Polyline coloring on the map | The segment table and the ETA fallback |
| Present in Real-Time mode | Yes, and it is the primary congestion signal | Yes, computed from an effective congestion of 0 |
| Present when Google omits it | No; the array is `[]` | Yes; segments are always built |

Google traffic intervals are pass-through: `app/map/routing.py` normalizes indices and the enum, and nothing
downstream recomputes them. Segment statistics are model output: `app/simulation/segments.py` computes every
field. A single route can therefore show a `TRAFFIC_JAM` interval on the map while its segment table shows a
moderate congestion fraction, because the first is Google's reading of a short stretch and the second is the
planning model's average over a long one.

## BPR Link Performance

`app/simulation/traffic.py` exposes the link-performance function.

```python
def bpr_adjusted_time(free_flow_minutes: float, flow: float, capacity: float) -> float:
    """Bureau of Public Roads link-performance function."""
    if capacity <= 0:
        raise ValueError("Road capacity must be positive.")
    return free_flow_minutes * (1 + BPR_ALPHA * (flow / capacity) ** BPR_BETA)
```

```
adjusted = free_flow_minutes * (1 + BPR_ALPHA * (flow / capacity) ** BPR_BETA)
```

| Constant | Value | Source |
|----------|-------|--------|
| `BPR_ALPHA` | 0.15 | `app/config/__init__.py` |
| `BPR_BETA` | 4 | `app/config/__init__.py` |

| Property | Behavior |
|----------|-----------|
| Zero flow | Returns exactly `free_flow_minutes` |
| Monotonic | Higher flow at fixed capacity never lowers the adjusted time |
| At capacity | Returns `free_flow_minutes * 1.15` |
| Above capacity | Grows on the fourth power, so oversaturation is penalized sharply |
| `capacity <= 0` | Raises `ValueError`; a zero-capacity road is a programming error, not a traffic state |

| Volume-to-capacity ratio | Multiplier |
|--------------------------|------------|
| 0.00 | 1.0000 |
| 0.25 | 1.0006 |
| 0.50 | 1.0094 |
| 0.75 | 1.0475 |
| 0.90 | 1.0984 |
| 1.00 | 1.1500 |
| 1.20 | 1.3110 |

The fourth-power shape is why the model stays flat through moderate traffic and then rises quickly: below
about 60 percent of capacity the penalty is under one percent, which matches the intuition that a road with
spare capacity does not slow down much.

The function raises rather than clamping on non-positive capacity so a mis-derived lane count fails a test
instead of silently producing a free-flow time.

## Time-of-Day Factor

```python
def time_of_day_factor(hour: int) -> float:
    hour = max(0, min(23, int(hour)))
    if 7 <= hour <= 9 or 16 <= hour <= 18:
        return 1.22
    if hour < 6 or hour >= 22:
        return 0.92
    return 1.0
```

| Hours | Factor | Reading |
|-------|--------|---------|
| 7, 8, 9 and 16, 17, 18 | 1.22 | Peak commute |
| 0 to 5 and 22, 23 | 0.92 | Overnight |
| 6 and 10 to 15 and 19 to 21 | 1.0 | Ordinary |

The input is clamped to 0–23 at the Model boundary. The Controller has already rejected out-of-range values
with `validation_error`, so the clamp is defence in depth rather than the validation path.

Where the factor is used:

| Consumer | Uses `time_of_day_factor`? |
|----------|----------------------------|
| Simulated `adjusted_eta_minutes` | No. The departure hour already shaped Google's traffic-aware duration; applying it again would count rush hour twice |
| Simulated `PriceFactors.time_multiplier` | No. Simulated mode reports `1.0` |
| Real-Time `adjusted_eta_minutes` | No. The scenario is not applied in Real-Time mode |
| Real-Time `PriceFactors.time_multiplier` | Yes, evaluated at the local departure hour |

The full rationale for that split lives in [pricing.md](pricing.md). The function stays in
`app/simulation/traffic.py` because it is a traffic-physics coefficient, and `app/pricing/model.py` receives
its result as an argument rather than importing it.

## `SegmentBuilder`

`app/simulation/segments.py` exposes `SegmentBuilder`. It takes a `RawRoute`, the effective scenario
congestion, and the route index, and returns a non-empty list of `RoadSegment`.

```python
class SegmentBuilder:
    def build(
        self,
        route: RawRoute,
        congestion: int,
        route_index: int,
    ) -> list[RoadSegment]:
        ...
```

The builder never calls Google and never parses raw Google JSON. `RawRoute` is already normalized by
`app/map/routing.py`, which is what keeps `app/simulation/` free of upstream payload shapes.

### Step selection

Segments come from the steps of the first leg. The builder keeps the first two steps, producing two segments
per route. Two segments is the deliberate granularity: it gives the segment table a readable comparison of a
surface-street stretch against a highway stretch without turning the panel into a turn-by-turn list.

| Condition | Behavior |
|-----------|-----------|
| Two or more steps in the first leg | Two segments, from steps 0 and 1 |
| Exactly one step | One segment, from step 0 |
| No steps, or no legs | One synthetic segment covering the whole route, named `Route segment 1`, with the route distance and the route static duration as free-flow time |

A route always yields at least one segment, because `RouteOption.segments` is contractually non-empty.

### Per-segment derivation

For segment index `i` in `0, 1`:

| Field | Derivation |
|-------|------------|
| `name` | The step's navigation instruction text, truncated to 80 characters; `Segment {i + 1}` when absent |
| `length_miles` | `round(step.distance_meters / 1609.344, 1)`, floored at 0.1 so a rounded-to-zero step keeps a positive length |
| `free_flow_minutes` | `step.static_duration_seconds / 60`; when absent, `length_miles / speed_limit_mph * 60` |
| `speed_limit_mph` | `(45, 55)[i]` |
| `lanes` | `(3, 4)[i]` |
| `capacity_vehicles_hour` | `lanes * BASE_LANE_CAPACITY` |
| local congestion | `clamp(congestion + i * 11 - route_index * 9, 5, 98)` |
| `congestion` | `round(local_congestion / 100, 2)` |
| `volume_vehicles_hour` | `round(capacity_vehicles_hour * local_congestion / 100)` |
| `adjusted_minutes` | `bpr_adjusted_time(free_flow_minutes, volume_vehicles_hour, capacity_vehicles_hour)` |
| `average_speed_mph` | `max(MINIMUM_CRAWL_SPEED_MPH, length_miles / (adjusted_minutes / 60))` |
| `traffic_ratio` | The step's traffic-aware seconds divided by its static seconds, rounded to four decimals; the route-level traffic ratio when either step duration is missing |
| `polyline` | The step's own decoded polyline; the mapped slice of the route polyline when the step has none |

The index terms encode the presentation, not measured geography. `+ i * 11` makes the second segment busier
than the first, which is how a highway stretch behaves relative to the surface streets that feed it.
`- route_index * 9` makes later alternatives calmer, matching the `Low traffic` naming from
[route-planning.md](route-planning.md). Both coefficients and the 5–98 clamp bounds belong in
`app/config/__init__.py`.

`speed_limit_mph` and `lanes` are assigned by index rather than read from Google, because the Routes API
response used here carries neither posted limits nor lane counts. The values represent a typical Austin
arterial at index 0 and a typical highway link at index 1. This is the single largest simplification in the
model, and the View labels the segment table as a planning estimate because of it.

`MINIMUM_CRAWL_SPEED_MPH` of 6.0 floors the average speed so a heavily oversaturated short segment cannot
report a fraction of a mile per hour, which would read as an error rather than as congestion.

### Worked segment

Scenario congestion 56, route index 0, segment index 1, step distance 8046 meters, step static duration
420 seconds.

| Quantity | Value |
|----------|-------|
| `length_miles` | 5.0 |
| `free_flow_minutes` | 7.0 |
| `speed_limit_mph` | 55 |
| `lanes` | 4 |
| `capacity_vehicles_hour` | 2080 |
| local congestion | `clamp(56 + 11 - 0, 5, 98)` = 67 |
| `congestion` | 0.67 |
| `volume_vehicles_hour` | `round(2080 * 0.67)` = 1394 |
| volume-to-capacity ratio | 0.6702 |
| `adjusted_minutes` | `7.0 * (1 + 0.15 * 0.6702 ** 4)` = 7.2118 |
| `average_speed_mph` | `max(6.0, 5.0 / (7.2118 / 60))` = 41.6 |

### Mapping step polylines onto route polyline index ranges

Each segment carries its own polyline so the segment table can highlight a stretch on the map. When a step
supplies its own encoded polyline, the builder decodes it and uses it directly, which is the accurate path.

When a step has no polyline, the builder maps the step onto an index range of the route polyline by
cumulative distance share:

1. Collect the distances in meters of the selected steps.
2. Let `total` be their sum, or 1.0 if the sum is zero.
3. Walk the steps accumulating `distance / total`, and for each cumulative fraction `f` record the boundary
   index `min(len(route_polyline) - 1, round(f * (len(route_polyline) - 1)))`. Boundaries start at 0.
4. Segment `i` spans `boundaries[i]` to `boundaries[i + 1]`, and its polyline is the inclusive slice
   `route_polyline[start:end + 1]`.
5. If a boundary pair would be empty or inverted, widen the end to `start + 1` so every segment gets at
   least two points.
6. If the route polyline has fewer than two points, the whole range `(0, len - 1)` is used.

The mapping assumes polyline points are roughly evenly spaced along the route, which holds well enough for
highlighting and is not used for any distance or timing calculation. Distances and durations always come
from the step's own `distanceMeters` and `staticDuration`, never from counting polyline points.

Segment polyline index ranges and `TrafficInterval` index ranges are separate concepts on separate scales.
A `TrafficInterval` always indexes the route polyline. A `RoadSegment.polyline` is a list of coordinates, not
an index range, precisely so the two are never confused.

## Acceptance Criteria

- [ ] `bpr_adjusted_time` returns exactly the free-flow time when flow is zero.
- [ ] `bpr_adjusted_time` is monotonically non-decreasing in flow at fixed capacity.
- [ ] `bpr_adjusted_time` returns `free_flow_minutes * 1.15` when flow equals capacity.
- [ ] `bpr_adjusted_time` raises `ValueError` when capacity is zero or negative.
- [ ] `time_of_day_factor` returns 1.22 for hours 7 to 9 and 16 to 18, 0.92 for hours below 6 and 22 or above, and 1.0 otherwise.
- [ ] `time_of_day_factor` clamps inputs outside 0–23 rather than raising.
- [ ] Every route has at least one segment, and a route with two or more steps has exactly two.
- [ ] `capacity_vehicles_hour` equals `lanes * BASE_LANE_CAPACITY` for every segment.
- [ ] `volume_vehicles_hour` never exceeds `capacity_vehicles_hour`.
- [ ] Every segment's `congestion` is between 0.05 and 0.98 inclusive.
- [ ] `adjusted_minutes` is greater than or equal to `free_flow_minutes` for every segment.
- [ ] `average_speed_mph` is never below `MINIMUM_CRAWL_SPEED_MPH`.
- [ ] Raising `Scenario.congestion` never lowers any segment's `adjusted_minutes`.
- [ ] Every segment polyline has at least two points, and every mapped index range stays inside the route polyline.
- [ ] A Google response with no legs still yields one segment rather than an empty array.
- [ ] `SegmentBuilder` produces its output with no network call.

## Planned Tests

| Test ID | Level | Target file | Assertion |
|---------|-------|-------------|-----------|
| T-12 | unit | `tests/test_simulation.py` | Zero flow returns the free-flow time, flow equal to capacity returns a 1.15 multiplier, adjusted time increases monotonically across an ascending flow sequence, and non-positive capacity raises `ValueError` |
| T-13 | unit | `tests/test_simulation.py` | `time_of_day_factor` returns the documented value for all 24 hours and clamps -3 and 30 |
| T-14 | unit | `tests/test_simulation.py` | The worked segment reproduces the documented capacity, volume, adjusted minutes, and average speed; local congestion is clamped to 5 and 98 at the extremes of scenario congestion and route index; a step without its own polyline receives a route polyline slice of at least two points inside the polyline range; a `RawRoute` with no legs yields exactly one synthetic segment; and raising `congestion` from 10 to 90 does not lower any segment's `adjusted_minutes` |
| T-39 | component | `src/components/SegmentTable.test.tsx` | The segment table renders every documented column and labels the values as planning estimates |

## Agent Implementation Notes

- Keep `app/simulation/traffic.py` free of imports from `app/map/` and `app/api/`. It takes and returns
  numbers.
- `SegmentBuilder` accepts a `RawRoute`, never an `httpx` response and never a raw Google dictionary. If a
  new Google field is needed, add it to `RawRoute` in `app/map/types.py` first.
- Put the segment coefficients in `app/config/__init__.py`: the per-index congestion step of 11, the
  per-route decrement of 9, the clamp bounds 5 and 98, the speed-limit pair `(45, 55)`, the lane pair
  `(3, 4)`, and the segment count ceiling of 2.
- Do not apply `time_of_day_factor` inside `SegmentBuilder`. Segment times are free-flow-plus-BPR only; mode
  factors are applied at the route level by the orchestration layer.
- Never overwrite `traffic_intervals` with segment-derived values. They are separate representations and the
  contract keeps them separate.
- If richer per-step segmentation is taken up in P2, raise the ceiling through configuration and keep the
  contract's non-empty guarantee; do not change the `RoadSegment` field set without updating
  [domain-contracts.md](domain-contracts.md) and `src/types.ts`.
