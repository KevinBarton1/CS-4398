# Prompt 19 — App Composition And Styles

**Wave:** 3 — View
**Depends on:** prompts 13 through 18
**Phase:** P1
**Read first:** [00-shared-context.md](00-shared-context.md)

## Read First

1. [00-shared-context.md](00-shared-context.md)
2. [../srs-context/view/app-composition.md](../srs-context/view/app-composition.md)
3. [../srs-context/architecture/class-diagram.md](../srs-context/architecture/class-diagram.md), the View collaboration diagram
4. [../srs-context/architecture/state-diagrams.md](../srs-context/architecture/state-diagrams.md)
5. [../agent-quickstart.md](../agent-quickstart.md), "Architecture At A Glance"

## Objective

Compose the application shell. `App.tsx` lays out the pieces and owns no fetching and no domain
rules. `AppHeader` carries brand, mode switch, and request status. `styles.css` is the single
presentation layer. `main.tsx` mounts the tree.

## Deliverables

| File | Responsibility |
|------|----------------|
| `TrafficSImulation/src/App.tsx` | Layout composition only |
| `TrafficSImulation/src/main.tsx` | React mount |
| `TrafficSImulation/src/components/AppHeader.tsx` | Brand, mode switch, request status |
| `TrafficSImulation/src/styles.css` | The presentation layer |
| `TrafficSImulation/src/App.test.tsx` | T-25, T-28, T-29, and the keyboard and live-region coverage that prompt 20 will deepen |

## Task

1. Implement `App.tsx` as pure composition:
   - Own `useRoutePlan` at the top and pass props down.
   - Render `AppHeader`, `RoutePlannerForm`, `RouteOptionList`, `MapConfigProvider` wrapping
     `RouteMap`, `AnalysisPanel`, `StatusBanner` / `Toast` as the loading-error document specifies.
   - Contain no `fetch` call and import no coefficient.
2. Implement `AppHeader` with the product name TrafficScope, the two mode options labeled `Simulated`
   and `Real-Time`, and a request-status indicator. A mode change calls `setMode`.
3. Implement `main.tsx` to mount `App` into the host document from prompt 01.
4. Write `styles.css` for a desktop browser layout that keeps the map, the route list, and the
   analysis panel simultaneously visible at a typical laptop width. Follow the accessibility contrast
   target of at least 4.5:1 for text. Do not add a CSS framework.
5. Wire Real-Time mode so scenario controls are absent and a successful plan renders exactly one
   route. Wire Simulated mode so up to three routes and the scenario controls appear.
6. Write T-25: initial load renders the default plan path, notice, and route list against a mocked
   client. Write T-28: switching to Real-Time hides scenario controls and renders one route. Write
   T-29: selection updates analysis and reconciles across a re-plan. Include keyboard traversal of the
   mode switch and route cards, and polite live-region announcements for loading and error, as a
   baseline that prompt 20 will harden.

## Boundaries

- `App.tsx` performs no fetching and imports no coefficient.
- No second map path, no CSS framework, no state-management library.
- Do not add a heatmap toolbar or any P3 affordance.
- Do not put domain arithmetic in a style or a layout helper.

## Tests To Write

| Test ID | Level | Target file | Assertion |
|---------|-------|-------------|-----------|
| T-25 | component | `src/App.test.tsx` | Initial load renders the default plan, notice, and route list |
| T-28 | component | `src/App.test.tsx` | Real-Time switch hides scenario controls and renders one route |
| T-29 | component | `src/App.test.tsx` | Selection updates analysis and reconciles across a re-plan |
| T-36 baseline | component | `src/App.test.tsx` | Keyboard traversal of the mode switch and route cards |
| T-37 baseline | component | `src/App.test.tsx` | Live-region announcements for loading and error |

## Definition Of Done

- [ ] `App.tsx` contains no `fetch` call and imports no coefficient.
- [ ] Mode switch labels are `Simulated` and `Real-Time`.
- [ ] Both modes render through the same map component.
- [ ] Scenario controls are present only when scenario applies.
- [ ] T-25, T-28, and T-29 pass.
- [ ] Keyboard traversal and live-region baselines exist.
- [ ] `npm test` and `npm run build` pass.
- [ ] A manual check against `npm run dev` with the API from prompt 11 shows the composed layout.

## Handoff

Report the component tree as rendered, any prop-drilling seams that felt wrong, and screenshots or a
short description of the desktop layout at a typical laptop width.
