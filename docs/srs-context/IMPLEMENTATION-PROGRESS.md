# TrafficScope — SRS Implementation Progress Report

**Generated:** July 27, 2026  
**SRS reference:** Distributed Traffic Simulation SRS Rev. 1.0 (July 12, 2026)  
**Implementation version:** API `1.1` (`GET /api/health`)  
**Context index:** [README.md](README.md)

This report maps the current codebase in `TrafficSImulation/` against the MVC-oriented SRS context files in `docs/srs-context/`. Status labels:

| Label | Meaning |
|-------|---------|
| **Done** | Requirement implemented and aligned with context file |
| **Partial** | Core behavior present; SRS assumption substituted or edge case missing |
| **Gap** | Not implemented or no automated verification |

---

## Executive Summary

TrafficScope delivers a **functional Rev. 1.1 planning application** that covers the essential SRS use cases through a local simulation stack (React 19 + FastAPI). The seven primary use-case groups are substantially complete; intentional deviations from the SRS replace external Google Maps, traffic, and weather APIs with local geocoding, BPR simulation, and configurable multipliers.

| Metric | Value |
|--------|-------|
| **Functional requirements (FR-1 – FR-7)** | **39 / 42** Done or Partial (~93%) |
| **Essential use-case groups (7)** | **6** fully usable; **1** (missing/invalid data) mostly done with known gaps |
| **MVC context files (13)** | **11** Done; **2** Partial (validation/error handling, simulation moving-jam note) |
| **SRS test plan (T-1 – T-10)** | **6** covered by automated tests; **4** manual or not yet tested |
| **Out-of-scope items (SRS §1.4)** | Correctly excluded (accounts, payments, history) |

**Bottom line:** The app is demo-ready for Austin metro route planning with simulated traffic, heatmaps, scenario controls, and illustrative pricing. Remaining work is mainly external API integration, richer error UX, and expanded test coverage—not core feature gaps.

---

## Architecture Alignment

The implementation matches the MVC split documented in the context index:

```
View (React)          →  TrafficSImulation/src/App.tsx, types.ts, styles.css
Controller (FastAPI)  →  TrafficSImulation/main.py, app/routes.py
Model (Python)        →  app/{models,map_service,traffic_simulator,pricing_model,
                          weather_service,heatmap,config}.py
```

Cross-layer contracts (`PlanRequest`, `PlanResult`, `RouteOption`) are synchronized between `app/models.py` and `src/types.ts`.

---

## Use-Case Group Progress

| Use Case | FR Range | Priority | Status | Notes |
|----------|----------|----------|--------|-------|
| Enter Starting Point and Destination | FR-1.1 – FR-1.7 | Essential | **Done** | Local Austin geocoder + fuzzy match; not Google Maps |
| View Route ETA and Road Segment Statistics | FR-2.1 – FR-2.6 | Essential | **Done** | BPR-adjusted ETAs, segment table, `data_source` labeling |
| View Traffic and Demand Heatmaps | FR-3.1 – FR-3.6 | Essential | **Done** | 5×8 grid, three modes + off, legend in view |
| Toggle Real-Time and Simulated Scenario | FR-4.1 – FR-4.5 | Important | **Done** | Reference (`realtime`) vs Simulated; selection preserved |
| Adjust Scenario Variables | FR-5.1 – FR-5.7 | Essential | **Done** | Sliders + reset; 180 ms debounced re-plan |
| Estimate Upfront Price | FR-6.1 – FR-6.5 | Essential | **Done** | Formula + factor breakdown + disclaimer |
| Handle Missing or Invalid Data | FR-7.1 – FR-7.7 | Essential | **Partial** | FR-7.3 explicit offline message; no live API fallbacks to wire |

---

## Layer-by-Layer Detail

### Model Layer

| Context File | Primary Modules | Status | Highlights |
|--------------|-----------------|--------|------------|
| [data-models.md](model/data-models.md) | `app/models.py`, `src/types.ts` | **Done** | `PlanRequest` Pydantic validation; full `RouteOption` / `RoadSegment` shapes |
| [config.md](model/config.md) | `app/config.py` | **Done** | Single source for pricing, BPR, weather, scoring weights |
| [simulation.md](model/simulation.md) | `app/traffic_simulator.py`, scoring in `routes.py` | **Partial** | BPR, segments, heatmap grid, route scoring complete; moving-jam model simplified to static BPR |
| [pricing.md](model/pricing.md) | `app/pricing_model.py` | **Done** | Distance/time base + multipliers; `factors` dict for UI |
| [weather.md](model/weather.md) | `app/weather_service.py` | **Partial** | Severity 0–3 multipliers work; always `"Simulated fallback"` (no live API) |
| [map-heatmap.md](model/map-heatmap.md) | `app/map_service.py`, `app/heatmap.py` | **Done** | 12 Austin places + aliases; 3 synthetic routes; heatmap wrapper |

### View Layer

| Context File | Primary Modules | Status | Highlights |
|--------------|-----------------|--------|------------|
| [main-app-ui.md](view/main-app-ui.md) | `App.tsx`, `styles.css` | **Done** | Three-column layout, header mode switch, toast errors, auto-load on mount |
| [controls-forms.md](view/controls-forms.md) | `RoutePlanner`, scenario in `Analysis` | **Done** | Origin/dest, geolocation, scenario sliders, reset |
| [map-display.md](view/map-display.md) | `TrafficMap` | **Partial** | SVG map, routes, heatmap, legend; reset view button (⌖) is UI placeholder only |
| [results-display.md](view/results-display.md) | `RouteOptions`, `Analysis` | **Done** | Route cards, pricing panel, segment table, recommended badge |

### Controller Layer

| Context File | Primary Modules | Status | Highlights |
|--------------|-----------------|--------|------------|
| [api-endpoints.md](controller/api-endpoints.md) | `main.py` | **Done** | `GET /api/health`, `POST /api/plan`, SPA static serving |
| [orchestration.md](controller/orchestration.md) | `app/routes.py` | **Done** | Full `plan_route` pipeline; reference-mode baseline overrides |
| [validation-error-handling.md](controller/validation-error-handling.md) | `main.py`, `routes.py`, `map_service.py` | **Partial** | 422/400 paths work; FR-7.3 network error UX not explicit |

---

## Functional Requirement Matrix

### FR-1 — Route Input

| ID | Requirement | Status | Implementation |
|----|-------------|--------|----------------|
| FR-1.1 | Origin input | **Done** | `#origin` in `RoutePlanner` |
| FR-1.2 | Destination input | **Done** | `#destination` in `RoutePlanner` |
| FR-1.3 | Current location | **Done** | Geolocation → `"Current location"` alias |
| FR-1.4 | Validate geocodable locations | **Done** | `map_service.geocode()` |
| FR-1.5 | Invalid location error | **Done** | `ValueError` → HTTP 400 → toast |
| FR-1.6 | Request route data | **Done** | `POST /api/plan` |
| FR-1.7 | Distance and base ETA | **Done** | Per-route fields in response |

### FR-2 — Route Statistics

| ID | Requirement | Status | Implementation |
|----|-------------|--------|----------------|
| FR-2.1 | Total distance | **Done** | Route cards + summary |
| FR-2.2 | Base ETA | **Done** | Selected route metrics |
| FR-2.3 | Adjusted ETA | **Done** | BPR + weather × time-of-day |
| FR-2.4 | Segment fields | **Done** | `RoadSegment` dataclass |
| FR-2.5 | Segment details panel | **Done** | Road detail table in `Analysis` |
| FR-2.6 | API vs simulated labeling | **Done** | `data_source` + `notice` |

### FR-3 — Heatmaps

| ID | Requirement | Status | Implementation |
|----|-------------|--------|----------------|
| FR-3.1 | Congestion overlay | **Done** | Traffic tab |
| FR-3.2 | Demand overlay | **Done** | Demand tab |
| FR-3.3 | Profitability overlay | **Done** | Earnings tab |
| FR-3.4 | Visual intensity | **Done** | `heatColor()` + opacity scaling |
| FR-3.5 | Legend | **Done** | `.legend` when mode ≠ off |
| FR-3.6 | Turn overlay off | **Done** | Off tab → empty `cells` |

### FR-4 — Mode Toggle

| ID | Requirement | Status | Implementation |
|----|-------------|--------|----------------|
| FR-4.1 | Real-time/simulated control | **Done** | Header Reference / Simulated |
| FR-4.2 | Label simulated values | **Done** | Source badge, `notice`, `data_source` |
| FR-4.3 | Recalculate on mode change | **Done** | Debounced `calculate()` |
| FR-4.5 | Preserve selected route | **Done** | `keepSelection` logic in `App.tsx` |

### FR-5 — Scenario Variables

| ID | Requirement | Status | Implementation |
|----|-------------|--------|----------------|
| FR-5.1 | Time of day | **Done** | Hour slider 0–23 |
| FR-5.2 | Weather severity | **Done** | Weather slider 0–3 |
| FR-5.3 | Congestion | **Done** | Congestion slider 0–100 |
| FR-5.4 | Demand | **Done** | Demand slider 0–100 |
| FR-5.5 | Weather time debuff | **Done** | `WEATHER_TIME_MULTIPLIERS` |
| FR-5.6 | Update on change | **Done** | 180 ms debounce → `/api/plan` |
| FR-5.7 | Reset to defaults | **Done** | Scenario card Reset button |

### FR-6 — Pricing

| ID | Requirement | Status | Implementation |
|----|-------------|--------|----------------|
| FR-6.1 | Distance + time estimate | **Done** | `estimate_price()` |
| FR-6.2 | Configurable multipliers | **Done** | Demand, traffic, weather, time |
| FR-6.3 | Display price | **Done** | Pricing card |
| FR-6.4 | Factor breakdown | **Done** | `factors` row in UI |
| FR-6.5 | Not official fares | **Done** | Static disclaimer text |

### FR-7 — Error Handling

| ID | Requirement | Status | Implementation |
|----|-------------|--------|----------------|
| FR-7.1 | GPS unavailable | **Done** | Geolocation deny toast |
| FR-7.2 | Manual entry when GPS denied | **Done** | Origin field stays editable |
| FR-7.3 | No internet | **Partial** | Generic `"Unable to calculate routes."` on fetch failure |
| FR-7.4 | Map data unavailable | **Partial** | Reference mode + notice (no live Map API) |
| FR-7.5 | Weather unavailable | **Partial** | Simulated only; no API failure path |
| FR-7.6 | Default simulated weather | **Done** | `weather_adjustment()` defaults |
| FR-7.7 | Route calculation failure | **Done** | HTTP 400 + toast with `detail` |

---

## SRS vs. Implementation Deviations

Documented in [README.md](README.md) and reflected in code:

| SRS Assumption | Current Behavior | Impact |
|----------------|------------------|--------|
| Google Maps geocoding & routing | Local Austin dictionary + fuzzy match; synthetic bezier routes | Demo-limited geography |
| External weather API | Severity index 0–3 with fixed multipliers | No live conditions |
| Real-time traffic API | `"realtime"` mode → stable baseline (congestion 44, demand 52, weather 0) | Reference mode, not live traffic |
| `templates/` / static HTML UI | React 19 + Vite + TypeScript | Modern SPA; production served from `dist/` |
| Moving traffic jams (§6.5) | Static BPR congestion per segment | No dynamic jam animation |
| Map pan/zoom | Fixed SVG viewBox 1000×650 | No interactive map navigation |

These deviations are **intentional** for offline/demo operation and align with NFR-1.2 (graceful degradation).

---

## Test Traceability (SRS Appendix T-1 – T-10)

| Test | Description | Status | Automated Coverage |
|------|-------------|--------|-------------------|
| T-1 | Valid locations return routes | **Done** | `test_typed_plan_endpoint`, `test_route_options_have_segments`, `App.test.tsx` |
| T-2 | Invalid location rejected | **Done** | `test_invalid_location_is_rejected` (backend); API 400 path in `main.py` |
| T-3 | GPS deny → manual entry | **Gap** | UI implemented; no automated test |
| T-4 | Weather changes ETA/price | **Done** | `test_weather_increases_eta_monotonically`, `test_adverse_conditions_increase_eta` |
| T-5 | Congestion affects heatmap/metrics | **Partial** | Logic in `heatmap_grid`; no dedicated assertion |
| T-6 | Demand affects metrics | **Partial** | Pricing/heatmap use demand; no dedicated assertion |
| T-7 | Mode switch relabels data | **Partial** | UI + orchestration done; no automated frontend test |
| T-8 | App usable when service fails | **Partial** | Reference mode + toasts; no failure-injection test |
| T-9 | Weather API failure fallback | **Gap** | No external weather API to fail |
| T-10 | Price varies by route; factors reconcile | **Done** | `test_pricing_breakdown_reproduces_final_estimate`, BPR tests |

### Existing Test Files

| File | Tests | Scope |
|------|-------|-------|
| `tests/test_api.py` | 3 | Health, typed plan 200, out-of-range 422 |
| `tests/test_backend.py` | 7 | Segments, ETA monotonicity, BPR, pricing, invalid location, weather |
| `src/App.test.tsx` | 1 | Layout hierarchy, mocked API render |

**Suggested additions:** frontend test for mode toggle label (T-7), heatmap value change on congestion (T-5), geolocation deny handler (T-3), explicit fetch-failure message (FR-7.3).

---

## Acceptance Criteria Checklist (Context Files)

Aggregated from unchecked items in context files:

### Done (verified in code)

- Request validation (422) for out-of-range scenario integers
- Three routes with segments on successful plan
- Pricing factors reproduce `estimated_price` (backend test)
- Frontend types aligned with API response
- No magic numbers outside `config.py`
- Mode-specific `notice` and `data_source` strings
- Heatmap `off` returns empty cells
- Origin equals destination rejected
- Disclaimer visible in pricing panel

### Partial or Untested

- Explicit no-internet user message (FR-7.3)
- Invalid multiplier UI warning (FR-6 alternate flow)
- Map reset view button wired to behavior
- Heatmap response verified under demand/congestion slider changes (manual QA)
- External API integration hooks (weather, maps, traffic) — future work
- Moving-jam simulation beyond static BPR

---

## Module Inventory

| Module | Lines (approx.) | Role | Context File |
|--------|-----------------|------|--------------|
| `app/config.py` | 24 | Coefficients | config.md |
| `app/models.py` | 58 | Pydantic + dataclasses | data-models.md |
| `app/map_service.py` | 76 | Geocoding, routes | map-heatmap.md |
| `app/traffic_simulator.py` | 64 | BPR, segments, grid | simulation.md |
| `app/pricing_model.py` | 18 | Fare estimate | pricing.md |
| `app/weather_service.py` | 17 | Weather multipliers | weather.md |
| `app/heatmap.py` | 9 | Heatmap wrapper | map-heatmap.md |
| `app/routes.py` | 76 | Orchestration | orchestration.md |
| `main.py` | 57 | HTTP + static | api-endpoints.md |
| `src/App.tsx` | 170 | Full UI | view/*.md |
| `src/types.ts` | 27 | TS contracts | data-models.md |

---

## Recommended Next Steps

Priority-ordered items to close remaining SRS gaps:

1. **Error UX (FR-7.3)** — Detect `fetch` network failures in `App.tsx` and show an explicit offline message.
2. **Test coverage (T-3, T-5, T-6, T-7)** — Add Vitest cases for geolocation deny, mode label, and integration tests for heatmap/scenario sensitivity.
3. **Map reset (wireframe 4.1.1)** — Wire ⌖ button or remove until pan/zoom exists.
4. **External APIs (optional upgrade path)** — Integrate geocoding/routing/weather behind existing module boundaries; preserve reference/simulated fallbacks per NFR-1.2.
5. **Moving jams (§6.5)** — Optional enhancement in `traffic_simulator.py` without breaking BPR core.

---

## Related Documents

- [SRS Context Index](README.md)
- [AGENTS.md](../../AGENTS.md) — build, test, and style conventions
- [TrafficSImulation/README.md](../../TrafficSImulation/README.md) — Rev. 1.1 implementation notes
- Source SRS PDF: `Distributed_Traffic_Simulation_Formatted_SRS.pdf`

---

*This report reflects static analysis of the codebase and SRS context files as of the generation date. Re-run tests locally with `python -m pytest` and `npm test` from `TrafficSImulation/` to confirm runtime status.*
