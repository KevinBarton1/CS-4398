# Model Context — Weather Service

**Layer:** Model  
**Codebase:** `TrafficSImulation/app/weather_service.py`, `TrafficSImulation/app/config.py`  
**Related:** [config.md](config.md), [simulation.md](simulation.md), [pricing.md](pricing.md)

## Purpose

Apply weather severity as configurable time and price debuffs (FR-5.5). Provide labeled weather state for the UI and orchestration layer.

## SRS Requirements

| ID | Requirement | Implementation |
|----|-------------|----------------|
| FR-5.2 | Weather severity control | Severity index 0–3 from request |
| FR-5.5 | Bad weather as configurable time debuff | `WEATHER_TIME_MULTIPLIERS` |
| FR-6.2 | Weather multiplier in pricing | `WEATHER_PRICE_MULTIPLIERS` |
| FR-7.5 | Error when weather data unavailable | Fallback to simulated (FR-7.6) |
| FR-7.6 | Support simulated default weather values | Current default implementation |
| T-4 | Change weather → ETA and price update | Backend monotonicity test |
| T-9 | Weather API failure → warning + fallback | Reference/simulated path |

## API

### `weather_adjustment(severity: int) -> dict`

Input clamped to 0–3.

| Field | Description |
|-------|-------------|
| `severity` | 0–3 index |
| `label` | Human-readable condition |
| `time_multiplier` | Applied to adjusted ETA |
| `price_multiplier` | Applied to price estimate |
| `source` | `"Simulated fallback"` (no live API yet) |

## Severity Levels (config.py)

| Severity | Label | Time × | Price × |
|----------|-------|--------|---------|
| 0 | Clear | 1.00 | 1.00 |
| 1 | Light rain | 1.08 | 1.03 |
| 2 | Heavy rain | 1.18 | 1.07 |
| 3 | Severe | 1.32 | 1.12 |

Frontend labels match in `App.tsx`: `["Clear", "Light rain", "Heavy rain", "Severe"]`.

## Usage in Orchestration

```python
weather = weather_adjustment(weather_level)
adjusted_eta_raw = bpr_minutes * weather["time_multiplier"] * time_factor
price, factors = estimate_price(..., weather["price_multiplier"], time_factor)
```

Response includes full `weather` object for display.

## Acceptance Criteria

- [ ] Severity 0–3 maps to monotonically increasing time and price multipliers.
- [ ] Invalid severity values are clamped, not rejected at model layer (controller validates 0–3).
- [ ] Weather increases ETA monotonically across severities (test_weather_increases_eta_monotonically).
- [ ] When external weather API is added, failed calls fall back to severity 0 or last-known with user warning (FR-7.5, FR-7.6).

## Assumptions (SRS 2.5)

- Weather data may be API-provided or mocked when unavailable.
- Effects are simplified multipliers, not physics-based road condition modeling.

## Non-Functional

| ID | Requirement |
|----|-------------|
| NFR-4.3 | Weather logic modular — isolated in `weather_service.py` |
| NFR-4.5 | Covered indirectly via ETA/price monotonicity tests |

## Agent Implementation Notes

- To integrate OpenWeather or similar: add fetch in `weather_service.py`, map API conditions to severity 0–3, retain `weather_adjustment` as the single multiplier lookup.
- Do not expose API keys in frontend (NFR-5.5).
- Reference mode (`realtime`) sets `weather_level = 0` in orchestration for stable baseline.
