# View Context — Map Display

**Layer:** View  
**Codebase:** `TrafficMap` component in `TrafficSImulation/src/App.tsx`, `TrafficSImulation/src/styles.css`  
**Related:** [model/map-heatmap.md](../model/map-heatmap.md), [main-app-ui.md](main-app-ui.md)

## Purpose

Display a stylized Austin road network with route overlays, heatmap intensity cells, origin/destination markers, and heatmap mode toolbar (SRS 4.1.1, FR-3.x).

## SRS Requirements

| ID | Requirement | Implementation |
|----|-------------|----------------|
| FR-3.1–3.3 | Congestion, demand, profitability modes | Toolbar tabs |
| FR-3.4 | Visual intensity for relative values | `heatColor()` + cell opacity |
| FR-3.5 | Heatmap legend | `.legend` when mode ≠ off |
| FR-3.6 | Turn overlay on/off | "Off" tab |
| FR-1.7 | Route on map | SVG path per route |
| NFR-3.3 | Heatmaps don't block map interaction | SVG click handlers on routes |

## Component: `TrafficMap`

### Props

| Prop | Type | Purpose |
|------|------|---------|
| `data` | `PlanResult \| null` | Routes + heatmap cells |
| `selected` | `RouteOption?` | Highlighted route |
| `heatmap` | `HeatmapMode` | Active overlay mode |
| `setHeatmap` | setter | Mode change (FR-3) |
| `onSelect` | `(id) => void` | Route click handler |

### Map Toolbar

Tabs: **Traffic** (congestion), **Demand**, **Earnings** (profitability), **Off**.

Reset button (⌖) — placeholder for reset map view (wireframe 4.1.1).

### SVG Structure (viewBox 0 0 1000 650)

1. Dark background + grid pattern
2. Water shape (decorative)
3. Minor and major road paths (static decoration)
4. **Heatmap cells** — 5×8 rects from `data.heatmap.cells`
5. **Route lines** — paths from route `points`; selected route thicker stroke
6. **Origin marker** — teal circle + label
7. **Destination marker** — pin shape + label
8. **Zone labels** — DOWNTOWN, UT AUSTIN, AIRPORT, THE DOMAIN, ZILKER

### Heatmap Coloring

```typescript
function heatColor(value: number) {
  return value < 45 ? "#36d1b7"   // low (teal)
       : value < 72 ? "#f6c85f"   // medium (yellow)
       : "#ff7668";               // high (coral)
}
```

Opacity: `0.05 + value / 650` per cell.

### Route Path Geometry

- 3 points → quadratic bezier (`Q`)
- Otherwise → polyline (`L`)

Matches backend `build_route_options` point triplets.

### Map Note

Displays `data.notice` or placeholder: "Enter two locations to compare routes."

## Wireframe Alignment (SRS Figure 3)

| Wireframe element | Status |
|-------------------|--------|
| Map display area | SVG shell |
| Route overlays | Colored paths |
| Heatmap overlays | Grid rects |
| Heatmap legend | Shown when active |
| Zone labels | Static text |

## Acceptance Criteria

- [ ] All three routes visible with distinct colors.
- [ ] Selected route has thicker stroke and drives origin/dest markers.
- [ ] Heatmap tab changes overlay without full page reload (T-5, T-6).
- [ ] "Off" hides cells and legend (FR-3.6).
- [ ] Cell tooltips show mode and value on hover (`<title>`).
- [ ] Clicking route line selects that route.

## Alternate Flows (FR-3)

| Condition | Expected UI |
|-----------|-------------|
| Simulation data unavailable | Show warning in map note; base map remains |
| Overlay render failure | User can select "Off" and continue |

## Future Enhancements (SRS assumptions)

- Replace static SVG with Google Maps or Mapbox tile layer.
- Pan/zoom if using real map SDK (NFR-3.3).
- Keep heatmap cell overlay as separate layer.

## Agent Implementation Notes

- Map coordinates come from backend `Point` — do not hardcode route geometry in view.
- If integrating Map API, preserve heatmap as overlay layer using same cell grid or geo bounds.
- Accessibility: `role="img"`, `aria-label` on SVG; route selection also available via route cards.
