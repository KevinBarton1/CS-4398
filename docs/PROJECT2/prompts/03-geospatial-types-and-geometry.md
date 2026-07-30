# Prompt 03 — Geospatial Types And Geometry

**Wave:** 1 — Model
**Depends on:** prompts 01, 02
**Phase:** P1
**Read first:** [00-shared-context.md](00-shared-context.md)

## Read First

1. [00-shared-context.md](00-shared-context.md)
2. [../README.md](../README.md), section "Shared value objects"
3. [../srs-context/model/domain-contracts.md](../srs-context/model/domain-contracts.md)
4. [../srs-context/architecture/class-diagram.md](../srs-context/architecture/class-diagram.md), section "Domain Value Objects"
5. [../srs-context/model/google-integrations.md](../srs-context/model/google-integrations.md), the polyline decoding part
6. [../srs-context/view/map-rendering.md](../srs-context/view/map-rendering.md), for how bounds are consumed

## Objective

Build the geospatial vocabulary of the Model and the two pure geometry helpers that everything above
depends on: the internal types, polyline decoding, and bounds math. These are the first modules other
domain packages import, so their shapes must be right before anything is built on them.

## Deliverables

| File | Responsibility |
|------|----------------|
| `TrafficSImulation/app/map/types.py` | `ResolvedPlace`, `RawRoute`, `LatLngPoint`, `RouteBounds`, `TrafficInterval`, `TrafficSpeed` |
| `TrafficSImulation/app/map/polyline.py` | `decode_polyline(encoded: str) -> list[LatLngPoint]` |
| `TrafficSImulation/app/map/bounds.py` | `bounds_for_points(points) -> RouteBounds`, `union_bounds(bounds) -> RouteBounds` |
| `TrafficSImulation/tests/test_polyline.py` | T-18 |
| `TrafficSImulation/tests/test_bounds.py` | T-19 |

## Task

1. Declare the value objects in `app/map/types.py` with exactly the fields listed in the class diagram
   and the README's shared value objects table:
   - `LatLngPoint`: `lat`, `lng`.
   - `RouteBounds`: `north`, `south`, `east`, `west`.
   - `TrafficInterval`: `start_index`, `end_index`, `speed`.
   - `TrafficSpeed`: the four values `NORMAL`, `SLOW`, `TRAFFIC_JAM`, `SPEED_UNSPECIFIED`.
   - `ResolvedPlace`: `name`, `latitude`, `longitude`, `source`. There is exactly one source value.
   - `RawRoute`: `id`, `distance_miles`, `duration_seconds`, `static_duration_seconds`,
     `traffic_ratio`, `polyline`, `traffic_intervals`, `steps`.
2. Keep `RawRoute` free of presentation concerns. `color`, `name`, and `objective` are assigned by
   `PlanningService` from index position and never live on the raw route. `RawRoute` is internal to the
   Model and is never serialized.
3. Implement `decode_polyline` for Google's encoded polyline format, returning points ordered origin to
   destination. Handle an empty string by returning an empty list rather than raising.
4. Implement `bounds_for_points` and `union_bounds` in `app/map/bounds.py`. A geographic bounding box is
   a fact about the route; the viewport decision belongs to the browser's `fitBounds`, so these helpers
   emit no center and no zoom.
5. Decide and document the degenerate cases: `bounds_for_points` on an empty list, on a single point,
   and `union_bounds` on an empty list. Pick the behavior that keeps `PlanningService` free of guards
   and state it in your handoff.
6. Write `tests/test_polyline.py` for T-18: decode a known encoded input and assert the exact decoded
   coordinates, plus the empty-input case.
7. Write `tests/test_bounds.py` for T-19: `bounds_for_points` over a known point set, `union_bounds`
   over two disjoint boxes, and the degenerate cases from step 5. Include the assertion that a union
   over per-route bounds contains every input box, since prompt 10 relies on it for `map_bounds`.

## Boundaries

- No HTTP, no `httpx`, no FastAPI, no import from `app/api/` (R1).
- No outbound Google call. This package parses and computes; prompt 04 owns the network (R6).
- Do not put a coefficient here. `PLACE_MATCH_TOLERANCE_DEGREES` and every other constant is imported
  from `app/config/__init__.py`.
- Do not emit screen-space geometry, a projection, a center, or a zoom level. Geometry is latitude and
  longitude only.
- Do not add a field to any value object that the README's table does not list.

## Tests To Write

| Test ID | Level | Target file | Assertion |
|---------|-------|-------------|-----------|
| T-18 | unit | `tests/test_polyline.py` | Decoding against a known encoded input, plus the empty case |
| T-19 | unit | `tests/test_bounds.py` | `bounds_for_points` and `union_bounds`, including degenerate inputs and the containment property |

## Definition Of Done

- [ ] Every value object has exactly the documented field set, no more and no fewer.
- [ ] `TrafficSpeed` has exactly the four documented values.
- [ ] `RawRoute` carries no `color`, `name`, or `objective`.
- [ ] `decode_polyline` returns points ordered origin to destination and tolerates an empty string.
- [ ] `union_bounds` over a set of boxes contains every input box.
- [ ] Degenerate-input behavior is decided, tested, and reported.
- [ ] No module in this package imports FastAPI, `httpx`, `app/api/`, or reads the environment.
- [ ] T-18 and T-19 pass, with expected values written as literals.
- [ ] `python -m pytest` passes.

## Handoff

Report the exact public surface of each module, the degenerate-case decisions, and the encoded polyline
fixture you used so prompt 04 and prompt 12 can reuse it.
