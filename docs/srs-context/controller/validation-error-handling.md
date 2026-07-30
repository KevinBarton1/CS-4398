# Controller Context — Validation & Error Handling

**Layer:** Controller  
**Codebase:** `TrafficSImulation/main.py`, `TrafficSImulation/app/routes.py`, `TrafficSImulation/app/map_service.py`  
**Related:** [api-endpoints.md](api-endpoints.md), [view/controls-forms.md](../view/controls-forms.md)

## Purpose

Validate inputs, translate domain errors to HTTP responses, and provide fallbacks when external data is unavailable (SRS use case 3.3.7, Part 5 robustness).

## SRS Requirements

| ID | Requirement | Handler |
|----|-------------|---------|
| FR-1.4 | Validate geocodable locations | `geocode()` in map_service |
| FR-1.5 | Invalid location error | ValueError → HTTP 400 |
| FR-5 (alt) | Reject out-of-range inputs | Pydantic → HTTP 422 |
| FR-7.1 | GPS unavailable error | View toast (client) |
| FR-7.2 | Manual entry when GPS denied | View keeps form editable |
| FR-7.3 | No internet error | Not fully implemented |
| FR-7.4 | Map data unavailable | Reference mode + notice |
| FR-7.5 | Weather unavailable | Simulated fallback |
| FR-7.6 | Default simulated weather | weather_service |
| FR-7.7 | Route calculation failure | HTTP 400 / toast |
| NFR-1.2 | Continue if one service fails | App stays usable |
| NFR-1.3 | Preserve inputs after failure | View state unchanged |
| NFR-2.1–2.5 | Robustness cases | See below |

## Validation Layers

### 1. Pydantic (`PlanRequest`)

| Field | Rule | Error code |
|-------|------|------------|
| origin, destination | min_length=1, max_length=120 | 422 |
| hour | 0–23 | 422 |
| weather | 0–3 | 422 |
| congestion, demand | 0–100 | 422 |

FastAPI returns standard validation error body for 422.

### 2. Domain (`plan_route` / map_service)

| Condition | Exception | HTTP |
|-----------|-----------|------|
| Unknown location | `ValueError("Unknown location …")` | 400 |
| Same origin and destination | `ValueError("Origin and destination must be different.")` | 400 |
| BPR capacity ≤ 0 | `ValueError` | 500 if uncaught |

Controller catch in `main.py`:

```python
try:
    return plan_route(request.model_dump())
except ValueError as error:
    raise HTTPException(status_code=400, detail=str(error)) from error
```

### 3. Soft Clamping (`_bounded` in routes.py)

For non-Pydantic dict access (legacy path): invalid int strings fall back to default, then clamp to range. Pydantic path is preferred for API.

## Fallback Behaviors

### Reference / Realtime Mode

When `mode == "realtime"`:

- Sets congestion=44, demand=52, weather_level=0 (stable baseline)
- Notice: "External traffic APIs are not configured; reference mode uses stable local baseline data."
- data_source: "Local reference model"

Simulates FR-7.4 / T-8 graceful degradation without crashing.

### Simulated Mode

- Uses client-provided scenario values
- Notice: "Traffic, demand, weather, and prices are simulated planning estimates."

### Weather

No external API — always simulated with `source: "Simulated fallback"`. Future API failure should default to severity 0 with warning (T-9).

## Client Error Display

`App.tsx`:

```typescript
catch (error) {
  setMessage(error instanceof Error ? error.message : "Unable to calculate routes.");
}
```

Toast with dismiss button; does not clear form state (NFR-1.3).

## Error Message Catalog (SRS 4.1.3)

| Scenario | Expected message | Status |
|----------|------------------|--------|
| Invalid address | API detail with suggestions | Implemented |
| No route found | Same as invalid / same OD | Implemented |
| GPS unavailable | Client toast | Implemented |
| Internet unavailable | Generic fetch error | Partial |
| Map API failure | Reference mode notice | Partial (offline baseline) |
| Weather API failure | Fallback weather | Simulated only |
| Simulation unavailable | Map note warning | Partial |

## Acceptance Criteria

- [ ] Invalid destination "Mars Colony" → 400 (test_invalid_location_is_rejected).
- [ ] weather=99 → 422.
- [ ] App does not crash on API errors (T-8 spirit).
- [ ] User can retry after error by correcting input or resubmitting.
- [ ] Reference mode explains missing external APIs clearly.

## Agent Implementation Notes

- Add explicit network error detection in frontend (`fetch` failure → FR-7.3 message).
- When integrating external APIs, wrap calls with timeout handling (SRS 4.4).
- Never expose stack traces to client in production.
- Log server-side details separately from user-facing `detail` strings.
