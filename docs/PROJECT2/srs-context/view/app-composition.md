# View Context — Application Composition

**Layer:** View
**Target modules:** `src/main.tsx`, `src/App.tsx`, `src/types.ts`, `src/styles.css`, `src/api/client.ts`, `src/hooks/useRoutePlan.ts`, `src/hooks/useMapConfig.ts`, `src/constants/scenario.ts`, `src/components/AppHeader.tsx`, `src/components/Toast.tsx`
**Related:** [route-scenario-forms.md](route-scenario-forms.md), [map-rendering.md](map-rendering.md), [results-analysis.md](results-analysis.md), [loading-error-states.md](loading-error-states.md), [accessibility.md](accessibility.md), [../architecture/architecture-overview.md](../architecture/architecture-overview.md), [../architecture/state-diagrams.md](../architecture/state-diagrams.md), [../controller/api-contracts.md](../controller/api-contracts.md), [../../README.md](../../README.md)

## Purpose

Define the target layout regions, component tree, state ownership, props contracts, and data flow for the TrafficScope browser client. This document is the entry point for the View layer: it fixes who owns each piece of state and which module performs each network call, so that no other View document has to re-decide those questions.

The governing rule is that `src/App.tsx` composes and never fetches. Every request the browser makes originates in `src/api/client.ts`, is sequenced by `src/hooks/useRoutePlan.ts` or `src/hooks/useMapConfig.ts`, and reaches presentational components only as props.

## Requirements

| ID | Requirement | Status | Phase |
|----|-------------|--------|-------|
| FR-2.10 | Route selection is preserved across re-plans when the selected `id` still exists in the new `routes` | Target | P1 |
| FR-4.1 | A mode switch in the application header offers exactly two options, labeled `Simulated` and `Real-Time` | Target | P1 |
| FR-4.2 | A mode change triggers a re-plan without requiring form submission | Target | P1 |
| FR-4.4 | Real-Time mode removes the scenario controls from the rendered tree | Target | P1 |
| FR-5.5 | Mode and scenario changes re-plan after a 180 ms debounce | Target | P1 |
| FR-7.4 | A failed plan preserves all form inputs and the previously rendered plan | Target | P1 |
| NFR-1.5 | Superseded in-flight plan requests are aborted and never write state | Target | P1 |
| NFR-1.2 | A control change is reflected in the interface within 2 seconds | Target | P1 |
| NFR-3.2 | The browser map credential reaches the View only through `GET /api/map/config` | Target | P1 |
| NFR-5.2 | `src/App.tsx` contains layout composition only: no `fetch`, no derivation of API values, no business rules | Target | P1 |
| NFR-6.4 | Every API shape lives in `src/types.ts` and mirrors `app/api/models.py` field for field | Target | P1 |
| NFR-5.3 | Scenario defaults and labels live in `src/constants/scenario.ts` and are never re-declared inline | Target | P1 |
| NFR-6.5 | Component and hook behavior is covered by Vitest with Testing Library in jsdom | Target | P1 |
| NFR-7.1 | The response `notice` string is displayed verbatim, without View-side rewriting | Target | P1 |

## Layout Regions

Four regions, one transient layer. Widths below describe the desktop arrangement; the planner and analysis columns stack above and below the map on narrow viewports.

```
+--------------------------------------------------------------------------+
| REGION 1  header (banner)                                                |
|   AppHeader: TrafficScope brand | [ Simulated | Real-Time ] | status     |
+----------------------+---------------------------+-----------------------+
| REGION 2  aside      | REGION 3  map column      | REGION 4  aside       |
| "planner"            | (primary content)         | "analysis"            |
|                      |                           |                       |
| RoutePlannerForm     | MapConfigProvider         | AnalysisPanel         |
|  - origin            |   RouteMap                |  - selected summary   |
|  - destination       |     RoutePolylineLayer    |  PriceSummary         |
|  - geolocation       |     MapBoundsController   |  ScenarioControls     |
|  - submit            |   "View all" toggle       |    (Simulated only)   |
|                      |                           |  SegmentTable         |
| RouteOptionList      | StatusBanner              |                       |
|  - up to 3 cards     |   (map unavailable)       | StatusBanner          |
|                      |                           |   (no plan yet)       |
| StatusBanner         |                           |                       |
|   (plan error)       |                           |                       |
+----------------------+---------------------------+-----------------------+
| TRANSIENT  Toast: retryable failures and geolocation denial              |
+--------------------------------------------------------------------------+
```

| Region | Element | Contents |
|--------|---------|----------|
| 1 | `header` | `AppHeader`: brand, mode switch, request status indicator |
| 2 | `aside.planner` | `RoutePlannerForm`, `RouteOptionList`, planner-scoped `StatusBanner` |
| 3 | `section.map` inside `main` | `MapConfigProvider` wrapping `RouteMap`, or a map-scoped `StatusBanner` |
| 4 | `aside.analysis` | `AnalysisPanel`, `PriceSummary`, `ScenarioControls`, `SegmentTable` |
| — | `Toast` | Rendered as a sibling of `main`, outside all three columns |

## Component Tree

```
main.tsx
  App
    AppHeader
    main
      aside.planner
        RoutePlannerForm
        RouteOptionList
        StatusBanner
      section.map
        MapConfigProvider
          RouteMap
            RoutePolylineLayer
            MapBoundsController
      aside.analysis
        AnalysisPanel
          PriceSummary
          ScenarioControls
          SegmentTable
    Toast
```

`src/main.tsx` creates the React root, mounts `App`, and imports `src/styles.css`. It holds no state and reads no API values.

## State Ownership

Each row names exactly one owner. No other module holds a second copy of the value.

| State | Type | Owner | Notes |
|-------|------|-------|-------|
| `origin` | `string` | `useRoutePlan` | Raw user text; the resolved name arrives back as `plan.origin` |
| `destination` | `string` | `useRoutePlan` | Raw user text |
| `mode` | `Mode` | `useRoutePlan` | `simulated` or `realtime` |
| `scenario` | `Scenario` | `useRoutePlan` | `hour`, `weather`, `congestion`; initialized from `defaultScenario` |
| `plan` | `PlanResult \| null` | `useRoutePlan` | Last successful `POST /api/plan` response |
| `selectedRouteId` | `string \| undefined` | `useRoutePlan` | Falls back to `plan.recommended_route_id` |
| `status` | `RequestStatus` | `useRoutePlan` | `idle`, `loading`, `success`, `empty`, `error` |
| `error` | `ApiError \| null` | `useRoutePlan` | Parsed error envelope from `src/api/client.ts` |
| `toast` | `ToastMessage \| null` | `useRoutePlan` | Transient notifications, including geolocation denial |
| `viewAll` | `boolean` | `useRoutePlan` | Drives the `fitBounds` target in `MapBoundsController` |
| `mapConfig` | `MapConfig \| null` | `useMapConfig` | Result of `GET /api/map/config`, fetched once and cached for the session |
| `mapConfigError` | `ApiError \| null` | `useMapConfig` | Rendered by the map-scoped `StatusBanner` |
| Polyline instances | `google.maps.Polyline[]` | `RoutePolylineLayer` | Imperative Maps objects, never React state; see [map-rendering.md](map-rendering.md) |

Derived values are memoized inside `useRoutePlan` and exposed read-only. They are never stored:

| Derived value | Definition |
|---------------|------------|
| `routes` | `plan?.routes ?? []` |
| `selectedRoute` | `routes.find((route) => route.id === selectedRouteId) ?? routes[0]` |
| `scenarioApplied` | `plan?.scenario_applied ?? mode === "simulated"` |
| `effectiveScenario` | `plan?.scenario ?? scenario` |
| `recommendedRouteId` | `plan?.recommended_route_id` |

`scenarioApplied` is read from the response, not inferred from local `mode`. That is what keeps the interface from claiming scenario influence during the window between a mode change and the arrival of the corresponding response.

## Hook Surface

`src/hooks/useRoutePlan.ts` exposes one object. `App.tsx` destructures it and forwards slices downward.

```ts
export interface RoutePlanController {
  origin: string;
  destination: string;
  mode: Mode;
  scenario: Scenario;
  plan: PlanResult | null;
  routes: RouteOption[];
  selectedRouteId?: string;
  selectedRoute?: RouteOption;
  scenarioApplied: boolean;
  effectiveScenario: Scenario;
  status: RequestStatus;
  error: ApiError | null;
  toast: ToastMessage | null;
  viewAll: boolean;
  setOrigin: (value: string) => void;
  setDestination: (value: string) => void;
  setMode: (mode: Mode) => void;
  setScenario: (scenario: Scenario) => void;
  resetScenario: () => void;
  selectRoute: (id: string) => void;
  toggleViewAll: () => void;
  submit: (event: FormEvent<HTMLFormElement>) => void;
  retry: () => void;
  useCurrentLocation: () => void;
  dismissToast: () => void;
}
```

`src/hooks/useMapConfig.ts` exposes `{ config, error, status }` and nothing else. It performs a single `GET /api/map/config` on first mount and returns the cached value on every later call within the session.

## Props Contracts

`App.tsx` passes only what each child renders or invokes. No child receives the whole controller object.

```ts
<AppHeader
  mode={mode}
  status={status}
  onModeChange={setMode}
/>

<RoutePlannerForm
  origin={origin}
  destination={destination}
  status={status}
  onOriginChange={setOrigin}
  onDestinationChange={setDestination}
  onSubmit={submit}
  onUseCurrentLocation={useCurrentLocation}
/>

<RouteOptionList
  routes={routes}
  selectedRouteId={selectedRouteId}
  recommendedRouteId={plan?.recommended_route_id}
  comparisonEnabled={scenarioApplied}
  onSelect={selectRoute}
/>

<MapConfigProvider>
  <RouteMap
    routes={routes}
    selectedRouteId={selectedRouteId}
    planBounds={plan?.map_bounds}
    congestion={scenarioApplied ? effectiveScenario.congestion : 0}
    weatherSeverity={scenarioApplied ? plan?.weather.severity ?? 0 : 0}
    viewAll={viewAll}
    onToggleViewAll={toggleViewAll}
  />
</MapConfigProvider>

<AnalysisPanel
  route={selectedRoute}
  weather={plan?.weather}
  notice={plan?.notice}
  recommendedRouteId={plan?.recommended_route_id}
  mode={mode}
  scenarioApplied={scenarioApplied}
  scenario={scenario}
  onScenarioChange={setScenario}
  onScenarioReset={resetScenario}
/>

<Toast message={toast} onDismiss={dismissToast} />
```

| Child | Receives | Never receives |
|-------|----------|----------------|
| `AppHeader` | `mode`, `status`, `onModeChange` | routes, scenario, plan payload |
| `RoutePlannerForm` | trip text, `status`, submit and geolocation callbacks | plan payload, scenario |
| `RouteOptionList` | `routes`, selection ids, `comparisonEnabled`, `onSelect` | scenario, weather |
| `MapConfigProvider` | children only; it reads `useMapConfig` itself | plan payload |
| `RouteMap` | `routes`, selection, bounds, color inputs, view-all state | form text, request status |
| `AnalysisPanel` | selected route, weather, notice, scenario and its callbacks | full `routes` array |
| `StatusBanner` | `status`, `error`, `onRetry`, region label | hooks or callbacks other than retry |
| `Toast` | `message`, `onDismiss` | plan payload |

`congestion` and `weatherSeverity` are zeroed by `App.tsx` when `scenarioApplied` is false. That single expression is why the map needs no mode-specific branch: in Real-Time mode the color function receives zeros and returns pure Google coloring.

## Data Flow

### Initial load

1. `main.tsx` mounts `App`.
2. `useMapConfig` issues `GET /api/map/config`. `useRoutePlan` issues `POST /api/plan` with the default trip, `mode: "simulated"`, and `defaultScenario`. The two requests are independent and neither blocks the other.
3. `status` moves `idle` to `loading`; `AppHeader` announces the in-flight state and `StatusBanner` occupies the planner column.
4. On success, `plan` is set, `selectedRouteId` becomes `plan.recommended_route_id`, and `status` becomes `success`.
5. On failure, `status` becomes `error`, `plan` stays `null`, and the planner column renders `StatusBanner` with `error.detail`.

### Form submit

1. `RoutePlannerForm` calls `onSubmit`, which calls `event.preventDefault()`.
2. `useRoutePlan` aborts any in-flight request, then posts the current `origin`, `destination`, `mode`, and scenario values.
3. Selection is not preserved across an explicit submit: the new `plan.recommended_route_id` becomes the selection, because origin and destination changes make the previous route identity meaningless.

### Mode change

1. `AppHeader` calls `onModeChange`.
2. `useRoutePlan` sets `mode`, then schedules a re-plan 180 ms later. A second mode change inside that window replaces the pending timer.
3. Until the response lands, `scenarioApplied` still reflects the previous response. `ScenarioControls` therefore leaves the tree only when the response with `scenario_applied: false` arrives, so no visual state claims an effect the server has not confirmed.
4. Selection is preserved by id when possible. Switching to Real-Time mode returns exactly one route, so selection normally falls back to `recommended_route_id`.

### Scenario change

1. `ScenarioControls` calls `onScenarioChange` with the complete next `Scenario` object.
2. Local state updates immediately, so the slider and its `output` track the pointer without waiting for the network.
3. A re-plan is scheduled 180 ms after the last change. Dragging a slider produces one request, not one per pointer move.
4. Scenario changes are ignored for re-planning while `scenarioApplied` is false; the controls are absent in that state, so no such change can originate from the interface.

### Selection change

1. `RouteOptionList` calls `onSelect` with a route `id`.
2. `selectedRouteId` updates. No network request occurs.
3. `RoutePolylineLayer` restyles strokes, `MapBoundsController` refits to the newly selected route's `bounds`, and `AnalysisPanel`, `PriceSummary`, and `SegmentTable` re-render from the new `selectedRoute`.

### Re-plan settlement

| Condition | Result |
|-----------|--------|
| Response `routes` contains `selectedRouteId` and the request preserved selection | Selection unchanged |
| Response `routes` does not contain `selectedRouteId` | Selection becomes `recommended_route_id` |
| Request was superseded and aborted | No state is written at all |
| Request failed | `plan`, `selectedRouteId`, and every form input are left untouched; `error` is set |

## Composition Rules

| Rule | Rationale |
|------|-----------|
| `App.tsx` imports no module from `src/api/` | Keeps the fetch boundary inside hooks and the typed client |
| `App.tsx` performs no formatting | Formatting belongs to `src/utils/format.ts` and the component that renders the value |
| Presentational components receive plain data and callbacks | Makes each component testable without a network stub |
| `useMapConfig` is consumed only by `MapConfigProvider` | The browser credential never travels through `App.tsx` props |
| API types are imported from `src/types.ts` only | One place changes when `app/api/models.py` changes |
| Scenario defaults and weather labels are imported from `src/constants/scenario.ts` | Prevents a drifting second copy of `defaultScenario` |

## Acceptance Criteria

- [ ] The application renders a plan for the default trip on first load with no user action.
- [ ] `src/App.tsx` contains no `fetch` call, no `await`, and no import from `src/api/`.
- [ ] The mode switch renders exactly two options, labeled `Simulated` and `Real-Time`.
- [ ] Changing mode issues exactly one plan request after 180 ms of quiet, not one per click within that window.
- [ ] Dragging a scenario slider across many values issues exactly one plan request.
- [ ] `ScenarioControls` is absent from the DOM once a response with `scenario_applied: false` is rendered.
- [ ] Selecting a route updates the map and all analysis panels without a network request.
- [ ] A re-plan that returns the previously selected `id` keeps that selection; otherwise the selection becomes `recommended_route_id`.
- [ ] A failed plan leaves `origin`, `destination`, `mode`, `scenario`, and the previously rendered plan intact.
- [ ] A superseded request writes no state, sets no error, and produces no toast.
- [ ] A failing `GET /api/map/config` leaves the planner column, the route list, and the analysis column fully usable.
- [ ] `plan.notice` is rendered verbatim, character for character.

## Planned Tests

| Test ID | Level | Target file | Assertion |
|---------|-------|-------------|-----------|
| T-25 | component | `src/App.test.tsx` | On mount, one `POST /api/plan` is issued and the resulting route cards, map region, and analysis panels are all present |
| T-27 | component | `src/hooks/useRoutePlan.test.ts` | Two mode changes 50 ms apart produce exactly one plan request, issued after the 180 ms debounce, and a superseded request that rejects with `AbortError` sets no error and leaves `plan` unchanged |
| T-29 | component | `src/App.test.tsx` | A re-plan whose `routes` still contain the selected `id` preserves the selection; a re-plan without it selects `recommended_route_id` |
| T-30 | component | `src/components/StatusBanner.test.tsx` | A rejected request preserves `origin`, `destination`, `mode`, `scenario`, and the prior `plan`, and sets `error.detail` |
| T-28 | component | `src/App.test.tsx` | Switching to `Real-Time` with a stubbed `scenario_applied: false` response removes the scenario controls from the DOM and keeps the map region mounted |

Level `component` denotes rendered React behavior in jsdom with Testing Library, including a full-`App` flow against a stubbed network layer, since the whole frontend suite runs under Vitest.

## Agent Implementation Notes

- Build `useRoutePlan` around a single `plan(options)` function that takes `{ preserveSelection: boolean }`. Submit passes `false`; mode, scenario, and retry pass `true`.
- Keep one `AbortController` in a ref. Abort it at the top of `plan()` before creating the next one, and discard any response whose controller is no longer the current one.
- Keep one debounce timer in a ref shared by the mode and scenario effects, so a mode change followed by a slider drag collapses into one request rather than racing two.
- Zero `congestion` and `weatherSeverity` in `App.tsx` when `scenarioApplied` is false. Do not push that conditional into `RouteMap` or `trafficSegmentColor`; the color function stays a pure function of its three arguments.
- Type `RequestStatus` as a string union in `src/types.ts` and derive every rendered state from it rather than from a boolean pair, so `empty` and `error` cannot both look like `loading`.
- `src/types.ts` mirrors `app/api/models.py` exactly, including `price_factors`. Do not shorten the field name and do not mark any `PriceFactors` member optional; all five are always present.
- When `app/api/models.py` gains a field, add it to `src/types.ts` in the same change so the contract test in [../requirements/traceability.md](../requirements/traceability.md) stays meaningful.
