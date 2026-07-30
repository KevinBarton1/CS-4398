# Prompt 05 — Traffic Physics And Segments

**Wave:** 1 — Model
**Depends on:** prompts 01, 02, 03
**Phase:** P1
**Read first:** [00-shared-context.md](00-shared-context.md)

## Read First

1. [00-shared-context.md](00-shared-context.md)
2. [../srs-context/model/traffic-simulation.md](../srs-context/model/traffic-simulation.md) — read all of it
3. [../srs-context/model/configuration.md](../srs-context/model/configuration.md), the traffic and segments catalog
4. [../README.md](../README.md), the `RoadSegment` fields and "Where the time-of-day factor applies"
5. [../srs-context/architecture/class-diagram.md](../srs-context/architecture/class-diagram.md), the free-function signatures

## Objective

Build the traffic physics: the BPR link-performance function, the time-of-day factor, and the segment
builder that turns a raw route into a list of fully populated `RoadSegment` values. These are pure
Model calculations. Orchestration will pass geometry and congestion in and take segments out; it will
never call these functions itself for formulas it owns.

## Deliverables

| File | Responsibility |
|------|----------------|
| `TrafficSImulation/app/simulation/traffic.py` | `bpr_adjusted_time`, `time_of_day_factor` |
| `TrafficSImulation/app/simulation/segments.py` | `SegmentBuilder.build(...)` |
| `TrafficSImulation/tests/test_simulation.py` | T-12, T-13, T-14 |

## Task

1. Implement `bpr_adjusted_time(free_flow_minutes, flow, capacity) -> float` using `BPR_ALPHA` and
   `BPR_BETA` from configuration. Zero flow must return free-flow time exactly. Adjusted time must
   increase monotonically with flow for a fixed capacity.
2. Implement `time_of_day_factor(hour) -> float` using the peak and off-peak constants. The documented
   bands are: `PEAK_TIME_FACTOR` for hours in `PEAK_HOURS_MORNING` and `PEAK_HOURS_EVENING`,
   `OFFPEAK_TIME_FACTOR` for hours before `OFFPEAK_HOUR_END` and from `OFFPEAK_HOUR_START`, and `1.0`
   otherwise. Clamp an out-of-range hour into 0–23 rather than raising, so a clock edge case cannot
   crash a plan.
3. Implement `SegmentBuilder`:
   - Accept a raw route, a congestion score, and a route index.
   - Produce at least one, and at most `SEGMENT_COUNT_MAX`, fully populated `RoadSegment` values whose
     fields match the README's `RoadSegment` table exactly.
   - Derive capacity from `BASE_LANE_CAPACITY` and `SEGMENT_LANE_COUNTS`, speed limits from
     `SEGMENT_SPEED_LIMITS_MPH`, and per-segment congestion from the score stepped by
     `SEGMENT_CONGESTION_INDEX_STEP` and clamped to `SEGMENT_CONGESTION_MIN` /
     `SEGMENT_CONGESTION_MAX`.
   - Apply BPR for `adjusted_minutes`. Enforce `MINIMUM_CRAWL_SPEED_MPH` when deriving average speed.
   - Slice the route polyline so every segment carries its own `polyline` ordered origin to
     destination.
4. Import every coefficient from `app/config/__init__.py`. Do not declare a rate, weight, floor, or
   ceiling as a literal in these modules.
5. Write T-12: BPR zero-flow identity and monotonic increase with flow.
6. Write T-13: time-of-day factor for a peak morning hour, a peak evening hour, an off-peak early hour,
   an off-peak late hour, a mid-day hour, and a clamped out-of-range hour. Expected values are the
   literals `1.22`, `0.92`, and `1.0`.
7. Write T-14: segment derivation produces a fully populated segment with capacity, flow, average
   speed, and polyline slices; every required field is present; segment count respects
   `SEGMENT_COUNT_MAX`. Leave the P2 assertion that segments cover the full step list for prompt 23.

## Boundaries

- No HTTP, no FastAPI, no `app/api/` import (R1).
- No coefficient literal. Every rate and threshold comes from configuration (R2's Model-side twin,
  NFR-5.3).
- Do not apply the time-of-day factor to an ETA. That decision belongs to the mode policy. This module
  exposes the factor; it does not decide where it is used.
- Do not score routes or estimate fares. Those are prompts 06 and 07.
- Prefer free functions for the two pure operations. `SegmentBuilder` is a class because it will be
  constructor-injected into `PlanningService`.

## Tests To Write

| Test ID | Level | Target file | Assertion |
|---------|-------|-------------|-----------|
| T-12 | unit | `tests/test_simulation.py` | BPR zero-flow identity and monotonic increase with flow |
| T-13 | unit | `tests/test_simulation.py` | Time-of-day factor bands and clamping |
| T-14 | unit | `tests/test_simulation.py` | Segment derivation: capacity, flow, average speed, polyline slices, field completeness |

## Definition Of Done

- [ ] Zero-flow BPR returns free-flow time exactly.
- [ ] Adjusted time increases monotonically with flow.
- [ ] Time-of-day factor returns exactly the documented values for the documented bands.
- [ ] Every route that goes through `SegmentBuilder` receives at least one fully populated segment.
- [ ] Segment count never exceeds `SEGMENT_COUNT_MAX`.
- [ ] Every coefficient is imported from `app/config/__init__.py`.
- [ ] No module in this package imports FastAPI, `httpx`, or `app/api/`.
- [ ] T-12, T-13, and T-14 pass with literal expected values.
- [ ] `python -m pytest` passes.

## Handoff

Report the public signatures, the sample inputs used by T-14 so prompt 10 can reuse them for
orchestration tests, and any traffic-simulation document sentence whose arithmetic disagreed with the
coefficient catalog.
