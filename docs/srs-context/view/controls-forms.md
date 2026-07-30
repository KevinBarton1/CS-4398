# View Context — Controls & Forms

**Layer:** View  
**Codebase:** `RoutePlanner` and scenario section in `Analysis`, `TrafficSImulation/src/App.tsx`  
**Related:** [main-app-ui.md](main-app-ui.md), [controller/validation-error-handling.md](../controller/validation-error-handling.md)

## Purpose

Capture origin/destination input, optional geolocation, route search submission, and scenario variable adjustment (SRS use cases 3.3.1, 3.3.5).

## SRS Requirements

| ID | Requirement | Component |
|----|-------------|-----------|
| FR-1.1 | Origin input field | `#origin` input |
| FR-1.2 | Destination/zone input | `#destination` input |
| FR-1.3 | Current location when permitted | "Use my current location" button |
| FR-5.1 | Time-of-day control | Hour slider 0–23 |
| FR-5.2 | Weather severity control | Weather slider 0–3 |
| FR-5.3 | Congestion control | Congestion slider 0–100 |
| FR-5.4 | Demand control | Demand slider 0–100 |
| FR-5.7 | Reset to defaults | "Reset" in scenario card |
| FR-7.1 | GPS unavailable error | Toast on geolocation deny |
| FR-7.2 | Manual entry when GPS denied | Origin field remains editable |
| NFR-6.1 | Simple controls | Range inputs with live labels |

## Route Planner (`RoutePlanner`)

### Fields

- **Starting point** — required text input, default "Downtown Austin"
- **Destination or zone** — required text input, default "Austin Airport"
- **Hint text** — suggests: The Domain, UT Austin, Zilker Park, Mueller, South Congress

### Actions

| Action | Behavior |
|--------|----------|
| Plan routes (submit) | `preventDefault`, calls `calculate(false)` |
| Use my current location | `navigator.geolocation.getCurrentPosition` → sets origin to "Current location" |
| Geolocation denied | Toast: "Location permission was denied. Enter a starting point manually." (T-3) |

### Loading State

Submit button disabled while `loading`; label "Calculating…".

## Scenario Lab (`Analysis` scenario card)

Sliders bound to `Scenario` state:

| Control | Range | Display |
|---------|-------|---------|
| Time of day | 0–23 | 12-hour format via `hourLabel()` |
| Weather | 0–3 | Clear / Light rain / Heavy rain / Severe |
| Congestion | 0–100 | Percentage |
| Customer demand | 0–100 | Percentage |

**Reset button:** Restores `{ hour: 17, weather: 1, congestion: 56, demand: 68 }`.

Changes debounce 180ms then trigger API recalculation (FR-5.6, NFR-3.2).

## Mode Switch (header, not in RoutePlanner)

Reference vs Simulated — see [main-app-ui.md](main-app-ui.md).

## Input Validation

| Layer | Validation |
|-------|------------|
| HTML | `required` on origin/destination |
| Backend | Pydantic bounds on scenario integers |
| Backend | Geocoding validation → 400 with message |

Frontend displays API errors in toast (FR-1.5, FR-7.7).

## Acceptance Criteria

- [ ] Empty fields blocked by HTML5 required validation.
- [ ] Valid submit fetches routes (T-1).
- [ ] Invalid location shows API error message (T-2).
- [ ] GPS deny shows message; manual entry still works (T-3).
- [ ] Weather slider change updates ETA and price (T-4).
- [ ] Congestion/demand sliders update heatmap and metrics (T-5, T-6).
- [ ] Reset restores defaults and triggers recalculation.

## Error Messages (SRS 4.1.3)

| Scenario | Message pattern |
|----------|-----------------|
| Invalid address | From API: `Unknown location "…". Try …` |
| GPS unavailable | Location permission denied toast |
| Route calculation failed | Generic or API `detail` |

Not yet implemented in UI: explicit no-internet, map API failure messages (FR-7.3, FR-7.4) — would use fetch error handling.

## Agent Implementation Notes

- Geolocation sets text "Current location" which backend resolves via alias.
- Do not send scenario values outside 0–23 / 0–3 / 0–100 — backend returns 422.
- Consider extracting `ScenarioControls` component if adding more variables.
- For accessibility: all sliders have associated labels and `<output>` elements.
