# Model Context — Map, Geocoding & Heatmap

**Layer:** Model  
**Codebase:** `TrafficSImulation/app/map_service.py`, `TrafficSImulation/app/heatmap.py`  
**Related:** [simulation.md](simulation.md), [data-models.md](data-models.md)

## Purpose

Resolve user-entered locations to map coordinates, generate three route alternatives with geometry, and produce heatmap overlay data for the map view.

## SRS Requirements

| ID | Requirement | Implementation |
|----|-------------|----------------|
| FR-1.4 | Validate locations can be geocoded | `geocode()` with fuzzy match |
| FR-1.5 | Error on invalid location | `ValueError` → HTTP 400 |
| FR-1.6 | Request route data after valid locations | `build_route_options` |
| FR-1.7 | Display distance and base ETA | Returned per route |
| FR-3.1–3.3 | Congestion, demand, profitability heatmaps | `build_heatmap` / `heatmap_grid` |
| FR-3.4 | Visual intensity for relative values | Cell values 3–100 |
| FR-3.5 | Heatmap legend | View responsibility |
| FR-3.6 | Turn overlays on/off | `heatmap: "off"` mode |

## Geocoding (`map_service.geocode`)

### Supported Places (Austin metro)

Downtown Austin, UT Austin, Austin Airport, The Domain, Zilker Park, Mueller, South Congress, Round Rock, Cedar Park, East Austin, Barton Springs, Current location.

### Aliases

Examples: `downtown` → Downtown Austin, `airport`/`aus` → Austin Airport, `ut` → UT Austin, `domain` → The Domain, `zilker`, `soco`, `east`, `barton`, `roundrock`.

### Matching Logic

1. Normalize input (lowercase, collapse whitespace).
2. Resolve alias.
3. Exact match in `PLACES` dict → `(display_name, Point)`.
4. Fuzzy match via `difflib.get_close_matches` (cutoff 0.68).
5. Otherwise raise `ValueError` with suggested places (FR-1.5, T-2).

## Route Generation (`build_route_options`)

**Precondition:** Origin ≠ destination (else `ValueError`).

For each of 3 indices:

- Compute midpoint and perpendicular offset for curved SVG path (quadratic bezier: start, bend, end).
- Distance = base hypotenuse × scale + buffer, × (1 + index × 0.09).
- Base ETA from average speed (34/38/42 mph) + 2 min.
- Assign road name pair from rotating `ROAD_NAMES`.
- Colors: `#55d6be`, `#ffb35c`, `#8aa8ff`.

Distance scale: `hypot(dx, dy) × 0.018 + 0.8` miles.

## Heatmap (`heatmap.build_heatmap`)

| Input | Description |
|-------|-------------|
| `congestion`, `demand`, `hour` | Scenario values |
| `mode` | congestion, demand, profitability, off |

Returns `{ mode, cells: [{ row, column, value }] }`.

- Invalid mode → defaults to congestion.
- `off` → empty cells array (view hides overlay).

Grid: 5 rows × 8 columns. See [simulation.md](simulation.md) for value formulas.

## SRS vs. Current Implementation

| SRS assumption | Current behavior |
|----------------|------------------|
| Google Maps geocoding | Local dictionary + fuzzy match |
| Routing API alternatives | Three synthetic curves with documented objectives |
| Map rendering via Map API | Stylized SVG in React view |

## Acceptance Criteria

- [ ] Valid Austin place names resolve consistently (T-1).
- [ ] Unknown locations produce clear error with suggestions (T-2).
- [ ] Three distinct routes returned for any valid origin/destination pair.
- [ ] Heatmap mode switch changes cell values appropriately (T-5, T-6).
- [ ] `off` mode yields no overlay cells.
- [ ] Origin equals destination rejected.

## External Interface (SRS Part 4)

When integrating Map Service API:

- Replace or augment `geocode` with API calls.
- Preserve local fallback for offline/demo (NFR-2.4, NFR-2.5).
- Keep `Point` geometry compatible with view SVG viewBox 1000×650.

## Agent Implementation Notes

- `map_service.py` should remain free of simulation/pricing imports except `Point` from models.
- `heatmap.py` is a thin wrapper — grid math lives in `traffic_simulator.heatmap_grid`.
- Adding new places: update `PLACES`, optionally `ALIASES`, and view map labels in `TrafficMap`.
