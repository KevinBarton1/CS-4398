# View Context — Main Application UI

**Layer:** View  
**Codebase:** `TrafficSImulation/src/App.tsx`, `TrafficSImulation/src/main.tsx`, `TrafficSImulation/src/styles.css`  
**Related:** [controls-forms.md](controls-forms.md), [map-display.md](map-display.md), [results-display.md](results-display.md), [controller/api-endpoints.md](../controller/api-endpoints.md)

## Purpose

Browser-based graphical interface centered on a map with route input, mode selection, scenario controls, and analysis panels (SRS 4.1, 4.1.1).

## SRS Requirements

| ID | Requirement | UI element |
|----|-------------|------------|
| 4.1 | Map-centered GUI with route input, heatmap, scenario, pricing | Three-column `main` layout |
| 4.1.1 | Main map screen components | Header + planner aside + map + analysis aside |
| FR-4.1 | Real-time/simulated mode control | Header mode switch |
| FR-4.2 | Label simulated values | Source badge, notice text |
| NFR-6.1 | Simple controls | Sliders, form inputs |
| NFR-6.3 | Explain API vs simulated | Mode labels, `data_source`, `notice` |
| NFR-6.4 | Actionable error messages | Toast component |

## Layout Structure

```
┌──────────────────────────────────────────────────────────────┐
│ HEADER: brand | Reference/Simulated toggle | status indicator │
├──────────────┬─────────────────────────┬─────────────────────┤
│ RoutePlanner │                         │ Analysis panels     │
│ RouteOptions │   TrafficMap (SVG)      │ - Selected summary  │
│              │                         │ - Pricing           │
│              │                         │ - Scenario lab      │
│              │                         │ - Road detail table │
└──────────────┴─────────────────────────┴─────────────────────┘
│ Toast (errors)                                                │
└──────────────────────────────────────────────────────────────┘
```

## Application State (`App` component)

| State | Type | Purpose |
|-------|------|---------|
| `origin`, `destination` | string | Route inputs (FR-1.1, FR-1.2) |
| `mode` | `Mode` | realtime \| simulated (FR-4.1) |
| `heatmap` | `HeatmapMode` | Overlay selection (FR-3.1–3.6) |
| `scenario` | `Scenario` | hour, weather, congestion, demand |
| `data` | `PlanResult \| null` | Last API response |
| `selectedId` | string? | Active route |
| `loading` | boolean | Request in flight |
| `message` | string | Error toast text |

## Data Flow

1. **Initial load:** `calculate(false)` on mount — loads default Downtown → Airport route.
2. **Form submit:** User clicks "Plan routes" → `calculate(false)` may reset selection to recommended.
3. **Scenario/mode/heatmap change:** Debounced 180ms → `calculate()` preserves selection when possible (FR-4.5).
4. **API call:** `POST /api/plan` with JSON body matching `PlanRequest`.

## Header

- **Brand:** TrafficScope logo/text.
- **Mode switch:** Labels "Reference" (realtime) and "Simulated" — maps to backend `mode`.
- **Status:** "Recalculating" vs "Simulation ready".

## Styling (`styles.css`)

SRS allows HTML/CSS/JS. Current implementation uses a dark teal map theme with:

- `.block`, `.card` — panel containers
- `.primary`, `.route-card`, `.analysis` — interactive elements
- Responsive layout for laptop/desktop (SRS 2.4)

## Acceptance Criteria

- [ ] App loads with default route visible without user action.
- [ ] Mode toggle updates labels and triggers recalculation (T-7).
- [ ] Loading state disables submit and shows status (NFR-3.1 feedback).
- [ ] Errors display in toast without crashing (NFR-2.1–2.4).
- [ ] Inputs preserved after failed request (NFR-1.3).
- [ ] No route history stored client-side beyond session state (NFR-5.2).

## Non-Functional

| ID | Requirement | Approach |
|----|-------------|----------|
| NFR-3.1 | Initial results within 5 seconds | Local API; loading indicator |
| NFR-3.2 | Control changes update within 2 seconds | 180ms debounce |
| NFR-6.2 | ETA, distance, price easy to read | Large metric typography in cards |

## Out of Scope (SRS 1.4, 6.6)

- User accounts, login, profiles
- Payment processing
- Saved route history

## Agent Implementation Notes

- Keep API types in `types.ts`; do not duplicate pricing logic in view.
- New screens should compose within existing `main` grid or extend header.
- Production build served by FastAPI from `dist/`; dev uses Vite proxy to `/api`.
- Component split: `RoutePlanner`, `RouteOptions`, `TrafficMap`, `Analysis` — can be moved to separate files if growing.
