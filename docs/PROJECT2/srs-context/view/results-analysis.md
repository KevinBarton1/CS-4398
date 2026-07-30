# View Context — Results and Analysis

**Layer:** View
**Target modules:** `src/components/RouteOptionList.tsx`, `src/components/AnalysisPanel.tsx`, `src/components/PriceSummary.tsx`, `src/components/SegmentTable.tsx`, `src/utils/format.ts`
**Related:** [app-composition.md](app-composition.md), [route-scenario-forms.md](route-scenario-forms.md), [map-rendering.md](map-rendering.md), [loading-error-states.md](loading-error-states.md), [accessibility.md](accessibility.md), [../model/pricing.md](../model/pricing.md), [../model/traffic-simulation.md](../model/traffic-simulation.md), [../model/domain-contracts.md](../model/domain-contracts.md)

## Purpose

Specify how a plan response becomes readable output: the route comparison cards, the selected-route summary, the fare breakdown, and the per-segment statistics table. Together these four components are the complete textual equivalent of everything the map draws, which is what allows the map to fail without the product failing.

Every value rendered here comes from the response. The View formats numbers and never recomputes them. A fare shown on screen is `route.estimated_price`, not a product the browser multiplied out; the multipliers in `price_factors` are displayed so the user can see the derivation, not so the client can perform it.

## Requirements

| ID | Requirement | Status | Phase |
|----|-------------|--------|-------|
| FR-1.7 | The resolved origin and destination names are displayed with the results | Target | P1 |
| FR-2.4 | Total route distance is shown per route | Target | P1 |
| FR-2.5 | Base travel time is shown for the selected route | Target | P1 |
| FR-2.6 | Adjusted travel time is shown per route and emphasized for the selected route | Target | P1 |
| FR-2.2 | Up to three alternatives are comparable side by side, with the recommended route marked | Target | P1 |
| FR-2.7 | Per-segment road statistics are shown for the selected route | Target | P1 |
| FR-2.10 | Selecting a card updates the map and every analysis panel | Target | P1 |
| FR-4.4 | Real-Time mode presents its single route without comparison affordances and explains why | Target | P1 |
| NFR-7.3 | Each route's `data_source` is displayed so simulated and live values are distinguishable | Target | P1 |
| FR-6.1 | Each route card shows its estimated price | Target | P1 |
| NFR-7.7 | The selected route's fare is shown as a headline figure | Target | P1 |
| FR-6.2 | All five `price_factors` members are displayed | Target | P1 |
| FR-6.5 | An illustrative-estimate disclaimer accompanies every fare | Target | P1 |
| FR-2.11 | Richer segment detail, including capacity and free-flow comparison, is presented in the segment table | Target | P2 |
| NFR-7.1 | The response `notice` is displayed verbatim | Target | P1 |
| NFR-7.2 | Simulated planning estimates are never presented as official fares or observed weather | Target | P1 |
| NFR-7.6 | Every displayed quantity carries its unit, at a numeric precision consistent across every panel | Target | P1 |

## Formatting Rules

All formatting helpers live in `src/utils/format.ts`. No component calls `toFixed` inline, so precision cannot drift between two panels showing the same field.

| Quantity | Rule | Helper | Example input | Rendered |
|----------|------|--------|---------------|----------|
| Distance in miles | One decimal, suffix `mi` | `formatMiles` | `12.34` | `12.3 mi` |
| Duration in minutes | One decimal, suffix `min` | `formatMinutes` | `27.86` | `27.9 min` |
| Currency | Two decimals, leading `$` | `formatCurrency` | `24.5` | `$24.50` |
| Vehicle flow | Integer with thousands separators, suffix `veh/hr` | `formatFlow` | `18400` | `18,400 veh/hr` |
| Multiplier | Two decimals, leading multiplication sign | `formatMultiplier` | `1.08` | `x1.08` |
| Congestion score | Integer out of 100 | `formatScore` | `56` | `56 / 100` |
| Segment congestion | Integer percentage of a 0.0 to 1.0 value | `formatRatioPercent` | `0.734` | `73%` |
| Comparison score | Four decimals | `formatNormalizedScore` | `0.8123` | `0.8123` |
| Departure hour | 12-hour clock | `hourLabel` | `17` | `5:00 PM` |

Thousands separators come from `toLocaleString("en-US")`. Rounding is presentational only: a distance of `12.34` is displayed as `12.3 mi` while the underlying value stays available for any comparison the server already performed.

## `RouteOptionList`

The comparison panel in the planner column. It renders one card per entry in `routes`, in response order, which is the server's ranked order.

### Panel chrome

| Element | Content |
|---------|---------|
| Eyebrow | `Route options` |
| Heading | `Compare your drive` |
| Count | `routes.length`, rendered as a numeric badge |
| Explanation line | Present only when comparison is unavailable; see below |

### Card contents

Each card is a native `button` element, which is what makes selection keyboard operable.

| Card element | Source field | Formatting |
|--------------|--------------|------------|
| Route name | `route.name` | Verbatim: `Fastest`, `Balanced`, or `Low traffic` |
| Recommended badge | Rendered when `route.id === plan.recommended_route_id` | Text `Recommended` |
| Objective line | `route.objective` | Verbatim |
| Adjusted ETA | `route.adjusted_eta_minutes` | `formatMinutes` |
| Distance | `route.distance_miles` | `formatMiles` |
| Price | `route.estimated_price` | `formatCurrency` |
| Identity accent | `route.color` | Applied as the CSS custom property `--route` on the card, matching the route's identity color |

The three metrics sit in one row so the alternatives can be scanned column-wise down the list. The badge is text, not a colored dot, so the recommendation survives grayscale rendering and screen readers.

### Selection interaction

| Aspect | Behavior |
|--------|----------|
| Trigger | Click, `Enter`, or `Space` on the card button |
| Effect | Calls `onSelect(route.id)`; no network request occurs |
| Selected state | `aria-pressed={true}` plus an `active` class carrying a visible border and background change |
| Downstream effects | `RoutePolylineLayer` restyles strokes, `MapBoundsController` refits the camera, and `AnalysisPanel`, `PriceSummary`, and `SegmentTable` re-render |
| Persistence | Selection survives a re-plan when the `id` still exists; otherwise it falls back to `recommended_route_id` |

The recommended route is the initial selection after every explicit submit. It is a starting point, not a lock: selecting any other card is a first-class action and nothing reverts it.

### Real-Time mode presentation

In Real-Time mode `routes` contains exactly one entry, so there is nothing to compare.

| Aspect | Behavior |
|--------|----------|
| Condition | `plan.scenario_applied === false` |
| Cards rendered | One |
| Count badge | `1` |
| Recommended badge | Not rendered; the sole route is trivially the recommendation |
| Card interactivity | The card renders as a static summary rather than a selection control, because there is no alternative to switch to |
| Explanation line | `Real-Time mode returns the single route Google recommends for the current departure time. Switch to Simulated mode to compare up to three alternatives.` |

The panel is present and populated, not hidden and not greyed out. The user still sees the route's name, objective, ETA, distance, and price; only the act of choosing between alternatives is meaningless and therefore absent.

## `AnalysisPanel`

The container for the selected-route analysis in the third column. It renders the selected-route summary itself and composes `PriceSummary`, `ScenarioControls`, and `SegmentTable` beneath it.

### Trip context

Rendered once at the top of the panel:

| Element | Source | Notes |
|---------|--------|-------|
| Resolved trip line | `plan.origin` and `plan.destination` | The names Google Places resolved, which may differ from what the user typed; rendered as `{origin} to {destination}` |
| Provenance notice | `plan.notice` | Displayed verbatim, with no truncation, rewriting, or substitution |

The notice is the product's honest statement about where its numbers come from. In Simulated mode it reads `Simulated mode: Google Maps supplies route geometry and departure-hour traffic; scenario controls adjust planning estimates.` In Real-Time mode it reads `Real-Time mode: route, distance, and travel time come from Google Maps traffic-aware routing for the current departure time.` The View never composes either sentence locally.

### Selected-route summary

| Element | Source | Formatting |
|---------|--------|------------|
| Eyebrow | Static `Selected route` | |
| Title | `selectedRoute.name` | Verbatim |
| Mode badge | `Simulated` or `Real-Time` derived from `plan.mode` | Exact UI labels |
| Data source line | `selectedRoute.data_source` | Verbatim |
| Recommended line | Rendered when the selected id equals `plan.recommended_route_id` | Text `Recommended route` |
| Hero figure | `selectedRoute.adjusted_eta_minutes` | One decimal, with the caption `min adjusted ETA` |
| Metric: Distance | `selectedRoute.distance_miles` | `formatMiles` |
| Metric: Base ETA | `selectedRoute.base_eta_minutes` | `formatMinutes` |
| Metric: Congestion | `selectedRoute.congestion_score` | `formatScore` |
| Metric: Comparison score | `selectedRoute.normalized_score` | `formatNormalizedScore`, captioned `lower is better` |
| Metric: Objective | `selectedRoute.objective` | Verbatim |
| Weather line | `plan.weather.label` with `plan.weather.source` | For example `Light rain, Simulated fallback` |

Base ETA and adjusted ETA appear together deliberately. The pair is what makes the adjustment visible: a user who sees `24.0 min` base and `27.9 min` adjusted can see the weather and traffic effect rather than being asked to trust one number.

`plan.weather.source` is always displayed with the label so a simulated weather state is never mistaken for an observation.

When no route is selected, because no plan has been received or the response contained no routes, the panel renders the placeholder specified in [loading-error-states.md](loading-error-states.md) rather than an empty shell.

## `PriceSummary`

### Fare display

| Element | Source | Formatting |
|---------|--------|------------|
| Eyebrow | Static `Planning estimate` | |
| Heading | Static `Expected fare` | |
| Headline amount | `selectedRoute.estimated_price` | `formatCurrency`, rendered as the panel's largest figure |
| Breakdown | `selectedRoute.price_factors` | See table below |
| Disclaimer | Static | See below |

### `price_factors` breakdown

All five members are always present in the response, and all five are always rendered. `time_multiplier` is `1.0` when no time-of-day factor applies; it is never absent and never null, so no conditional rendering is needed and none is written.

| Row label | Field | Formatting | Meaning |
|-----------|-------|------------|---------|
| Route subtotal | `route_subtotal` | `formatCurrency` | Distance and duration charge before any multiplier |
| Traffic | `traffic_multiplier` | `formatMultiplier` | Congestion effect on the fare |
| Weather | `weather_multiplier` | `formatMultiplier` | Equal to `plan.weather.price_multiplier` |
| Time of day | `time_multiplier` | `formatMultiplier` | Departure-hour effect; `x1.00` when no factor applies |
| Before rounding | `unrounded_total` | `formatCurrency` | Product of the subtotal and the three multipliers |

The rows are ordered so they read as a derivation: subtotal, then each multiplier, then the pre-rounding product, with the rounded headline figure above. `estimated_price` is `unrounded_total` rounded by the pricing model in `app/pricing/model.py`; the two figures differ by at most a cent and the breakdown makes that visible rather than confusing.

The field is named `price_factors`. It is not named `factors`.

### Disclaimer

Rendered inside the panel, always, with no dismiss control:

```
Illustrative estimate only. Not an official Uber or Lyft fare.
```

The disclaimer is part of the panel's permanent structure. It does not depend on mode, and it is never collapsed behind a disclosure control, because a fare figure without it overstates what the product knows.

## `SegmentTable`

Per-segment statistics for the selected route, rendered from `selectedRoute.segments`. The array always has at least one element.

### Columns

| Column | Primary cell content | Secondary cell content |
|--------|----------------------|------------------------|
| Road | `segment.name` | `{lanes} lanes` and `formatRatioPercent(segment.congestion)` |
| Length | `formatMiles(segment.length_miles)` | |
| Speed | `{average_speed_mph} mph` | `limit {speed_limit_mph}` |
| Flow | `formatFlow(segment.volume_vehicles_hour)` | `of {formatFlow(segment.capacity_vehicles_hour)} capacity` |
| Time | `formatMinutes(segment.adjusted_minutes)` | `free flow {formatMinutes(segment.free_flow_minutes)}` |
| Delay | `formatMultiplier(segment.traffic_ratio)` | `of free-flow time` |

Every `RoadSegment` field except `polyline` appears in the table. `polyline` is geometry consumed by the map and has no textual presentation.

The Flow, Time, and Delay columns each pair an observed value with its reference value, so a row is interpretable on its own: `18,400 veh/hr of 22,000 veh/hr capacity` says more than `18,400 veh/hr`, and `4.6 min, free flow 3.2 min` shows the delay that `traffic_ratio` summarizes.

### Table structure

| Aspect | Behavior |
|--------|----------|
| Element | A real `table` with `thead`, `tbody`, and `th` cells carrying `scope="col"` |
| Row key | `segment.name` combined with the row index, since two stretches of the same road can appear |
| Row count | One per segment, with no truncation and no pagination |
| Overflow | The table sits inside a horizontally scrollable wrapper so narrow viewports do not clip the right-hand columns |
| Caption | `Segment statistics for {selectedRoute.name}` |

Sorting and column hiding are not provided. The server's segment order follows the route from origin to destination, and that order is itself information a sort would destroy.

### Missing values

The contract guarantees every field on every segment, so the table renders no conditional fallbacks. If a field were absent, the cell would render an em dash rather than `undefined` or `NaN`, and the row would still render its remaining values. This is a defensive rendering rule, not an expected state.

## Panel Behavior By Mode

| Panel | Simulated | Real-Time |
|-------|-----------|-----------|
| `RouteOptionList` | Up to 3 selectable cards, recommended badge | 1 static card, explanation line |
| Selected-route summary | Full metric grid, mode badge `Simulated` | Full metric grid, mode badge `Real-Time` |
| `PriceSummary` | Full breakdown with the disclaimer | Full breakdown with the disclaimer |
| `ScenarioControls` | Rendered | Absent, with the explanation from [route-scenario-forms.md](route-scenario-forms.md) |
| `SegmentTable` | All segments of the selected route | All segments of the single route |

Only two things change with mode: how many cards exist, and whether the scenario panel is present. Every other panel renders the same fields from the same contract.

## Acceptance Criteria

- [ ] Three route cards render after a Simulated plan, each showing name, objective, adjusted ETA, distance, and price.
- [ ] Exactly one card carries the `Recommended` badge, and its id equals `plan.recommended_route_id`.
- [ ] Each card is a native `button` and is reachable and activatable by keyboard.
- [ ] Activating a card changes the selection, updates the analysis panels, and issues no network request.
- [ ] The selected-route summary shows both `base_eta_minutes` and `adjusted_eta_minutes`.
- [ ] `data_source` is rendered verbatim for the selected route.
- [ ] `plan.notice` is rendered verbatim, byte for byte, in both modes.
- [ ] `plan.origin` and `plan.destination` are shown as the resolved trip, not the raw user text.
- [ ] The weather line shows both `plan.weather.label` and `plan.weather.source`.
- [ ] All five `price_factors` rows are present, including `time_multiplier` when its value is `1.0`.
- [ ] The illustrative-estimate disclaimer is present whenever a fare figure is present, in both modes.
- [ ] Distances and durations show one decimal, currency shows two decimals, and vehicle flow shows thousands separators.
- [ ] `normalized_score` shows four decimals and is captioned `lower is better`.
- [ ] The segment table renders one row per element of `selectedRoute.segments`, with no truncation.
- [ ] Every `RoadSegment` field except `polyline` appears in the table.
- [ ] In Real-Time mode the route list shows one card, no `Recommended` badge, and the explanation line.
- [ ] No panel displays a value the browser computed from other response fields.

## Planned Tests

| Test ID | Level | Target file | Assertion |
|---------|-------|-------------|-----------|
| T-25 | component | `src/App.test.tsx` | Three route fixtures render three buttons; the card matching `recommended_route_id` carries the `Recommended` badge and no other card does |
| T-36 | component | `src/App.test.tsx` | Activating a card by keyboard calls `onSelect` with that route's `id`, and the card exposes `aria-pressed` reflecting selection |
| T-28 | component | `src/App.test.tsx` | With `comparisonEnabled` false and one route, one card renders, no `Recommended` badge is present, and the Real-Time explanation line is shown |
| T-38 | component | `src/components/PriceSummary.test.tsx` | All five `price_factors` rows render, `time_multiplier` of `1.0` renders as `x1.00` rather than being omitted, currency and multiplier formatting read `$24.50` and `x1.08`, and the disclaimer text is present |
| T-39 | component | `src/components/SegmentTable.test.tsx` | A three-segment fixture renders three `tbody` rows, each exposing name, lanes, congestion percentage, length, average speed, speed limit, volume, capacity, free-flow minutes, adjusted minutes, and traffic ratio, with every quantity carrying its unit |
| T-29 | component | `src/App.test.tsx` | Selecting the second route card updates the selected-route summary, fare headline, and segment table to that route's values with no additional plan request |

## Agent Implementation Notes

- Put every formatting helper in `src/utils/format.ts` and unit-test it there. A component that calls `toFixed` inline is how two panels end up disagreeing about the same number.
- Read the fare breakdown from `route.price_factors`. The current implementation names this field `factors`; the target contract does not, and the rename is deliberate.
- Do not multiply `route_subtotal` by the three multipliers to produce a displayed total. Render `unrounded_total` and `estimated_price` as the server sent them; a client-side product will disagree at the cent boundary and will silently diverge if the pricing model changes.
- Do not mark any `PriceFactors` member optional in `src/types.ts`, and do not write a conditional around the `time_multiplier` row.
- Render the recommendation as text, not as a color or an icon alone, so it survives grayscale, high-contrast modes, and screen readers.
- Render the Real-Time card as a non-interactive summary rather than a disabled button. A disabled control implies a state in which it would work; there is no such state for a single route.
- Key segment rows on name plus index. Routes legitimately traverse the same named road more than once, and a name-only key collapses those rows.
- Keep the disclaimer inside `PriceSummary` rather than in a shared footer, so a fare figure can never be rendered anywhere without it.
