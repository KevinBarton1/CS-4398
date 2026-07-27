# SRS Context — Distributed Traffic Simulation (Rev. 1.0)

This directory splits the **Software Requirements Specification** for the Distributed Traffic Simulation and Rideshare Driver Planning App into MVC-oriented context files. Each file is self-contained so an agent can implement or extend one layer without reading the full SRS.

## Project Summary

**TrafficScope** is a web-based planning tool for rideshare drivers and operations staff. Users enter an origin and destination (or zone), compare route alternatives, inspect road-segment statistics, view congestion/demand/profitability heatmaps, adjust scenario variables (time, weather, congestion, demand), and review an illustrative upfront price estimate.

**Version 1.0 scope excludes:** user accounts, login, driver profiles, payment processing, saved history, and official Uber/Lyft fare calculation.

**Primary stack (current implementation):**

| Layer | Location | Technology |
|-------|----------|------------|
| View | `TrafficSImulation/src/` | React 19 + TypeScript + CSS |
| Controller | `TrafficSImulation/main.py`, `TrafficSImulation/app/routes.py` | FastAPI |
| Model | `TrafficSImulation/app/` | Python domain modules |

Run commands from `TrafficSImulation/`. See repo-root `AGENTS.md` for build, test, and style conventions.

## MVC Mapping

```
┌─────────────────────────────────────────────────────────────┐
│  VIEW (React)                                               │
│  App.tsx, types.ts, styles.css                              │
│  Route input, map, heatmaps, route cards, analysis panels   │
└──────────────────────────┬──────────────────────────────────┘
                           │ POST /api/plan, GET /api/health
┌──────────────────────────▼──────────────────────────────────┐
│  CONTROLLER (FastAPI)                                       │
│  main.py — HTTP, validation, static hosting                 │
│  routes.py — orchestration, scoring, response assembly      │
└──────────────────────────┬──────────────────────────────────┘
                           │ calls
┌──────────────────────────▼──────────────────────────────────┐
│  MODEL (Python domain)                                      │
│  map_service, traffic_simulator, pricing_model,             │
│  weather_service, heatmap, models, config                   │
└─────────────────────────────────────────────────────────────┘
```

## Context File Index

### Model (`model/`)

| File | Purpose | Codebase modules |
|------|---------|------------------|
| [data-models.md](model/data-models.md) | Domain entities, API request/response shapes | `app/models.py`, `src/types.ts` |
| [simulation.md](model/simulation.md) | BPR traffic, segments, time-of-day, route scoring | `app/traffic_simulator.py`, `app/routes.py` |
| [pricing.md](model/pricing.md) | Upfront price estimation and factor breakdown | `app/pricing_model.py` |
| [weather.md](model/weather.md) | Weather severity, time/price multipliers | `app/weather_service.py` |
| [map-heatmap.md](model/map-heatmap.md) | Geocoding, route geometry, heatmap grid | `app/map_service.py`, `app/heatmap.py` |
| [config.md](model/config.md) | Centralized coefficients and weights | `app/config.py` |

### View (`view/`)

| File | Purpose | Codebase modules |
|------|---------|------------------|
| [main-app-ui.md](view/main-app-ui.md) | Layout, header, mode switch, app state | `src/App.tsx`, `src/styles.css` |
| [map-display.md](view/map-display.md) | Map SVG, route overlays, heatmap legend | `TrafficMap` in `App.tsx` |
| [controls-forms.md](view/controls-forms.md) | Route planner, geolocation, scenario sliders | `RoutePlanner`, `Analysis` in `App.tsx` |
| [results-display.md](view/results-display.md) | Route cards, pricing, segment table | `RouteOptions`, `Analysis` in `App.tsx` |

### Controller (`controller/`)

| File | Purpose | Codebase modules |
|------|---------|------------------|
| [api-endpoints.md](controller/api-endpoints.md) | REST endpoints, request/response contracts | `main.py`, `app/models.py` |
| [validation-error-handling.md](controller/validation-error-handling.md) | Input validation, error responses, fallbacks | `main.py`, `app/routes.py` |
| [orchestration.md](controller/orchestration.md) | Plan-route workflow, mode handling, scoring | `app/routes.py` |

## SRS Requirement Groups (Quick Reference)

| Use Case | FR IDs | Priority |
|----------|--------|----------|
| Enter Starting Point and Destination | FR-1.1 – FR-1.7 | Essential |
| View Route ETA and Road Segment Statistics | FR-2.1 – FR-2.6 | Essential |
| View Traffic and Demand Heatmaps | FR-3.1 – FR-3.6 | Essential |
| Toggle Real-Time and Simulated Scenario | FR-4.1 – FR-4.5 | Important |
| Adjust Scenario Variables | FR-5.1 – FR-5.7 | Essential |
| Estimate Upfront Price | FR-6.1 – FR-6.5 | Essential |
| Handle Missing or Invalid Data | FR-7.1 – FR-7.7 | Essential |

## Cross-Layer Dependencies

- **View → Controller:** `App.tsx` POSTs to `/api/plan` with origin, destination, mode, heatmap, hour, weather, congestion, demand.
- **Controller → Model:** `plan_route()` calls map, weather, simulation, pricing, and heatmap modules in sequence.
- **Model → View:** Response includes routes, heatmap cells, weather label, notice string, and recommended route ID.
- **Shared types:** Keep `src/types.ts` and `app/models.py` / response dict shapes aligned when changing contracts.

## Implementation Notes vs. SRS Assumptions

The SRS assumes Google Maps and external weather APIs. The current codebase uses:

- **Local geocoding** with a fixed Austin place dictionary (`map_service.py`) instead of a live Map API.
- **Reference mode** (`mode: "realtime"`) that applies stable baseline values when external APIs are unavailable.
- **Simulated weather** via severity index 0–3 rather than live OpenWeather calls.
- **React + Vite** frontend instead of SRS-mentioned `templates/` and `static/`.

Agents extending the app toward full SRS compliance should preserve the simulated/reference fallback behavior (NFR-1.2, FR-7.6, FR-7.7).

## Test Traceability

SRS Appendix 7.3 defines tests T-1 through T-10. Current coverage:

- `tests/test_api.py` — health, typed plan endpoint, out-of-range rejection (422)
- `tests/test_backend.py` — segments, ETA monotonicity, BPR, pricing reproduction, invalid location
- `src/App.test.tsx` — frontend behavior

See individual context files for requirement-to-test mapping per feature area.

## Related Documents

- Source SRS: `Distributed_Traffic_Simulation_Formatted_SRS.pdf` (Rev. 1.0, July 12, 2026)
- Project README: `TrafficSImulation/README.md` (documents Rev. 1.1 implementation)
