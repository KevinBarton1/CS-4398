# Controller Context — Orchestration

**Layer:** Controller  
**Codebase:** `TrafficSImulation/app/routes.py`  
**Related:** All model context files, [api-endpoints.md](api-endpoints.md)

## Purpose

Coordinate map routing, weather adjustment, traffic simulation, pricing, heatmap generation, and route recommendation into a single plan response (SRS Figure 5 sequence, Part 3 summary).

## Entry Point

`plan_route(payload: dict) -> dict`

Called from `main.plan` after Pydantic validation.

## Workflow

```
1. Parse & bound inputs (mode, hour, weather, congestion, demand, heatmap)
2. If mode == "realtime" → apply reference baseline overrides
3. build_route_options(origin, destination) → 3 raw routes
4. weather_adjustment(weather_level) → multipliers + label
5. time_of_day_factor(hour) → time multiplier
6. FOR each route:
     a. Adjust route_congestion by route index
     b. create_segments(route, congestion, index)
     c. Sum BPR minutes + buffer → adjusted_eta_raw
     d. Apply weather × time → adjusted_eta (rounded)
     e. estimate_price(...) → price + factors
     f. Build RouteOption dict
7. Compute normalized_score for each route
8. recommended_route_id = min score
9. build_heatmap(congestion, demand, hour, heatmap_mode)
10. Assemble response with notice string
```

## Input Processing

| Parameter | Processing |
|-----------|------------|
| `mode` | `"realtime"` if payload mode equals realtime, else `"simulated"` |
| `hour` | `_bounded(0, 23)`, default 17 |
| `weather` | `_bounded(0, 3)`, default 1; overridden to 0 in realtime |
| `congestion` | `_bounded(0, 100)`, default 56; 44 in realtime |
| `demand` | `_bounded(0, 100)`, default 68; 52 in realtime |
| `heatmap` | string passed to build_heatmap |

## Mode Handling (FR-4.x)

| Aspect | Simulated | Realtime (Reference) |
|--------|-----------|----------------------|
| Scenario values | From request | Fixed baseline |
| data_source | "Simulated scenario" | "Local reference model" |
| notice | Simulated disclaimer | External API not configured |
| ETA/heatmap/price | User-driven | Stable reference |

T-7: Mode toggle triggers full recalculation in frontend.

## Route Recommendation

After all routes computed:

```python
maxima = { time, distance, congestion max across routes }
normalized_score = weighted sum (see model/config.md)
recommended = route with minimum normalized_score
```

## Response Assembly

```python
{
    "origin": origin_name,
    "destination": destination_name,
    "mode": mode,
    "weather": weather,      # full dict from weather_service
    "hour": hour,
    "congestion": congestion,
    "demand": demand,
    "routes": routes,        # list of 3 dicts
    "recommended_route_id": recommended["id"],
    "heatmap": build_heatmap(...),
    "notice": "<mode-specific string>",
}
```

## Module Dependencies

```
routes.py
├── heatmap.build_heatmap
├── config.ROUTE_SCORE_WEIGHTS
├── map_service.build_route_options
├── models.RouteOption
├── pricing_model.estimate_price
├── traffic_simulator.create_segments, time_of_day_factor
└── weather_service.weather_adjustment
```

Maintains NFR-4.1 separation — orchestration only coordinates, does not embed formulas.

## Acceptance Criteria

- [ ] Always returns exactly 3 routes for valid input.
- [ ] Recommended route has lowest normalized score.
- [ ] Adverse scenario increases ETA vs clear baseline (integration tests).
- [ ] Mode switch changes notice and data_source labeling.
- [ ] Heatmap mode echoed in response matches request (or validated default).
- [ ] Invalid location never returns 200.

## Sequence (SRS Appendix 7.1)

Aligns with: User submits locations → validate → build routes → apply modifiers → compute price → return map data + statistics + estimate.

## Performance (NFR-3.4)

All steps are local computation — no external HTTP in orchestration. Scenario-only changes should not trigger map API calls (already satisfied).

## Agent Implementation Notes

- Keep `plan_route` as single orchestration function; split only if adding distinct workflows (e.g., zone-only planning).
- When adding caching, cache key should include origin, destination, mode, and scenario — not heatmap mode alone (heatmap is cheap to recompute).
- Any new response fields require updates to `types.ts` and view consumers.
- Moving jam simulation would hook into step 6b or a pre-segment pass in traffic_simulator.
