# View Context — Results Display

**Layer:** View  
**Codebase:** `RouteOptions` and `Analysis` components in `TrafficSImulation/src/App.tsx`  
**Related:** [data-models.md](../model/data-models.md), [pricing.md](../model/pricing.md)

## Purpose

Present route comparison cards, selected route summary, pricing breakdown, and road-segment statistics table (SRS 4.1.2, use cases 3.3.2, 3.3.6).

## SRS Requirements

| ID | Requirement | UI location |
|----|-------------|-------------|
| FR-2.1 | Total route distance | Route cards + selected summary |
| FR-2.2 | Base estimated travel time | Selected summary metrics |
| FR-2.3 | Adjusted travel time | Route cards + large ETA display |
| FR-2.5 | Segment statistics in details panel | Road detail table |
| FR-6.3 | Price in pricing panel | Pricing card |
| FR-6.4 | Major pricing factors | Factors row |
| FR-6.5 | Not official fares disclaimer | Pricing card footnote |
| FR-4.5 | Preserve selected route | Selection state across recalc |

## Route Comparison Panel (`RouteOptions`)

SRS Figure 4 — Route comparison wireframe.

### Per Route Card

| Display | Source field |
|---------|--------------|
| Route name | `route.name` |
| Recommended badge | when `id === recommended_route_id` |
| Objective text | `route.objective` |
| Adjusted ETA | `route.adjusted_eta_minutes` min |
| Distance | `route.distance_miles` mi |
| Price | `$route.estimated_price` |

Interaction: click selects route (`onSelect`), applies `.active` class and route color CSS variable.

Count badge shows number of routes (3).

## Selected Route Summary (`Analysis` — first card)

| Element | Content |
|---------|---------|
| Eyebrow | "Selected route" |
| Title | Route name |
| Source badge | "Reference" or "Simulated" from `data_source` |
| Recommended line | Shown if selected === recommended |
| Hero ETA | Large adjusted ETA + "min adjusted ETA" |
| Metrics grid | Distance, Base ETA, Congestion /100, Demand /100 |

Skeleton state when no route selected (initial edge case).

## Pricing Panel (`Analysis` — pricing card)

| Element | Content |
|---------|---------|
| Title | "Expected fare" |
| Amount | `$estimated_price.toFixed(2)` |
| Factors | Route subtotal, Demand ×, Traffic ×, Weather ×, Time × |
| Disclaimer | "Illustrative estimate only. Not an official Uber or Lyft fare." |

Factors from `route.factors` — mirrors backend pricing breakdown.

## Road Detail Table (`Analysis` — road-detail card)

Columns: Road, Length, Speed, Flow

Per segment row:

| Column | Fields |
|--------|--------|
| Road | `name`, `{lanes} lanes · {congestion}%` |
| Length | `{length_miles} mi` |
| Speed | `{average_speed_mph} mph`, limit subtext |
| Flow | `{volume_vehicles_hour}` veh/hr |

FR-2 alternate flow: if segment data incomplete, show available values — currently all segments populated by backend.

## Selection Behavior

- On plan success: keep current selection if route id still exists, else select recommended (FR-4.5).
- Selected route drives map highlight and all analysis panels.

## Acceptance Criteria

- [ ] Three route cards with distance, ETA, price visible after plan (T-1).
- [ ] Recommended route marked with badge.
- [ ] Selecting card updates map and analysis panels.
- [ ] Pricing factors multiply to match displayed price (backend test T-10).
- [ ] Segment table lists all segments for selected route.
- [ ] Disclaimer always visible in pricing panel (FR-6.5).
- [ ] Simulated vs reference clearly labeled (NFR-6.3).

## Test Traceability

| Test | Feature |
|------|---------|
| T-1 | Route cards populate |
| T-4 | Price/ETA update on weather change |
| T-6 | Demand reflected in metrics |
| T-7 | Simulated label on mode switch |
| T-10 | Price varies by route distance/time |

## Agent Implementation Notes

- Format currency with `toFixed(2)`; locale-aware formatting optional enhancement.
- If adding route comparison chart or sort, keep card list as primary selector.
- Extend table if FR-2.4 adds fields (e.g., speed limit column already in subtext).
