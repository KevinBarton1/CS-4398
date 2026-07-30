# Prompt 15 — Map Rendering Path

**Wave:** 3 — View
**Depends on:** prompts 13, 14
**Phase:** P1
**Read first:** [00-shared-context.md](00-shared-context.md)

## Read First

1. [00-shared-context.md](00-shared-context.md)
2. [../srs-context/view/map-rendering.md](../srs-context/view/map-rendering.md) — read all of it
3. [../srs-context/architecture/architecture-overview.md](../srs-context/architecture/architecture-overview.md), the View components table and rule R7
4. [../srs-context/architecture/state-diagrams.md](../srs-context/architecture/state-diagrams.md), the map loading states
5. [../srs-context/architecture/class-diagram.md](../srs-context/architecture/class-diagram.md), the four map components
6. [../migration-from-current-implementation.md](../migration-from-current-implementation.md), sections 1 through 3, so you know what must not return

## Objective

Build the single map rendering path: one `google.maps.Map` through `@vis.gl/react-google-maps`, used
identically in both modes, with native polylines colored by traffic interval. There is no second map
technology for any mode, state, or degraded condition. The map-unavailable state is a text banner.

## Deliverables

| File | Responsibility |
|------|----------------|
| `TrafficSImulation/src/components/MapConfigProvider.tsx` | Supplies the browser credential to `APIProvider` |
| `TrafficSImulation/src/components/RouteMap.tsx` | The single `google.maps.Map` instance for both modes |
| `TrafficSImulation/src/components/RoutePolylineLayer.tsx` | Creates and disposes native polylines per traffic interval |
| `TrafficSImulation/src/components/MapBoundsController.tsx` | `fitBounds` policy |
| `TrafficSImulation/src/utils/trafficSegmentColor.ts` | Speed-to-color mapping and Simulated-mode tint |
| Colocated tests | T-31, T-32, T-33, T-34 |

## Task

1. Implement `MapConfigProvider`:
   - Own `useMapConfig`.
   - On success, render `APIProvider` from `@vis.gl/react-google-maps` with the browser key, libraries,
     and optional `map_id`.
   - On failure, render a contained map-unavailable state in the map region only. Do not attempt a
     different map technology. Do not leave the rest of the application unusable.
2. Implement `RouteMap` as the single map surface. Both Simulated and Real-Time render through this
   component. It creates one `google.maps.Map` using the configured center, zoom, and color scheme.
3. Implement `RoutePolylineLayer`:
   - One `google.maps.Polyline` per traffic interval slice of the selected or visible routes.
   - Color from `trafficSegmentColor` based on `TrafficSpeed`.
   - In Simulated mode, apply the scenario-driven tint; in Real-Time mode, leave Google speed colors
     untinted (FR-3.5).
   - Emphasize the selected route (FR-3.6).
   - Dispose every native polyline on unmount or when the input set changes (NFR-1.4).
4. Implement `MapBoundsController`:
   - Fit the selected route's `bounds` when a selection exists.
   - Fit `map_bounds` when showing all routes.
   - Do not invent a center or zoom on the server side; `fitBounds` is the viewport decision.
5. Implement `trafficSegmentColor.ts` as a View concern. Mapping the four `TrafficSpeed` values to
   stroke colors has no Model counterpart. Keep any tint math here; do not put it in a Model module.
6. Confirm T-56 from prompt 12 now passes: a grep for `google.maps` outside these four components
   returns nothing.
7. Write T-31, T-32, T-33, and T-34 against the documented assertions. Mock the Maps JavaScript API in
   jsdom; do not require a real browser key for the default suite.

## Boundaries

- Exactly one map rendering path (NFR-5.7, R7). Do not introduce an Embed API iframe, an SVG overlay,
  a static map image, or a second map library for any state.
- The map-unavailable state is a text banner inside the map region, not an alternative renderer.
- Do not put `google.maps` usage in a hook, a utility other than the color mapper's type imports, or a
  non-map component.
- Do not recompute fares, ETAs, or scores.
- Markers and polyline click-to-select are P2. Do not add them here.

## Tests To Write

| Test ID | Level | Target file | Assertion |
|---------|-------|-------------|-----------|
| T-31 | component | `src/components/RouteMap.test.tsx` | Map configuration failure is contained; one map surface for both modes |
| T-32 | component | `src/components/RoutePolylineLayer.test.tsx` | One polyline per interval, emphasis, disposal on unmount |
| T-33 | unit | `src/utils/trafficSegmentColor.test.ts` | Speed-to-color mapping and tint behavior |
| T-34 | component | `src/components/MapBoundsController.test.tsx` | `fitBounds` targets and refit triggers |

## Definition Of Done

- [ ] Both modes render through `RouteMap`; there is no mode-specific map component.
- [ ] Polylines are native `google.maps.Polyline` instances, one per traffic interval.
- [ ] Tint applies in Simulated only; Real-Time is untinted.
- [ ] Selected route is emphasized; camera fits selected `bounds` or `map_bounds`.
- [ ] Map failure is contained to the map region; planning remains usable.
- [ ] Every native polyline is disposed on unmount.
- [ ] T-56 passes: `google.maps` appears only in the four map components.
- [ ] T-31 through T-34 pass without a live browser key.
- [ ] `npm test` and `npm run build` pass.

## Handoff

Report the component public props, how the Maps API is mocked in tests, and any map-rendering
document sentence that required a judgment call about tint or emphasis.
