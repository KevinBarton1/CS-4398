# View Context — Accessibility

**Layer:** View
**Target modules:** `src/App.tsx`, `src/styles.css`, `src/components/AppHeader.tsx`, `src/components/RoutePlannerForm.tsx`, `src/components/ScenarioControls.tsx`, `src/components/RouteOptionList.tsx`, `src/components/RouteMap.tsx`, `src/components/SegmentTable.tsx`, `src/components/StatusBanner.tsx`, `src/components/Toast.tsx`
**Related:** [app-composition.md](app-composition.md), [route-scenario-forms.md](route-scenario-forms.md), [map-rendering.md](map-rendering.md), [results-analysis.md](results-analysis.md), [loading-error-states.md](loading-error-states.md), [../requirements/non-functional-requirements.md](../requirements/non-functional-requirements.md)

## Purpose

Define the accessibility contract for the TrafficScope browser client, targeting WCAG 2.1 level AA. The load-bearing commitment is textual parity: every fact the map conveys is also available as text, so a user who cannot see or cannot use the map still receives the complete result. That commitment is what makes the map an enhanced presentation rather than the product itself, and it is the same property that lets the map fail without the application failing, as described in [loading-error-states.md](loading-error-states.md).

The second commitment is that interactive elements are native elements. The mode switch, the route cards, the sliders, and the retry actions are `button`, `input`, and `output` elements. Nothing here is a `div` with a click handler and a bolted-on `role`.

## Requirements

| ID | Requirement | Status | Phase |
|----|-------------|--------|-------|
| NFR-4.1 | The document exposes `banner`, `main`, and `complementary` landmarks with distinct accessible names, and every form control has a programmatically associated label, with an associated `output` on every slider | Target | P1 |
| NFR-4.2 | The mode switch and route cards are keyboard operable with a visible focus indicator and no keyboard trap | Target | P1 |
| NFR-4.3 | The map region has an accessible name and a text description of the selected route, and every fact conveyed by the map is available in the route list or the segment table | Target | P1 |
| NFR-4.4 | Request status and error messages are announced through `aria-live` regions | Target | P1 |
| NFR-4.5 | Text meets 4.5:1 contrast, large text and control boundaries meet 3:1 | Target | P1 |
| NFR-4.6 | Traffic color is never the only carrier of meaning | Target | P1 |
| NFR-4.7 | `prefers-reduced-motion` suppresses non-essential motion | Target | P2 |
| NFR-4.8 | An automated accessibility check runs against the rendered application in the test suite | Target | P2 |
| FR-2.7 | Every route carries the per-segment road statistics that make route geometry and traffic conditions readable without the map | Target | P1 |

## Semantic Landmarks

| Region | Element | Accessible name | Landmark role |
|--------|---------|-----------------|---------------|
| Application header | `header` | Implicit | `banner` |
| Mode switch | `div` with `role="group"` inside the header | `Planning mode` | — |
| Request status | `p` inside the header | `Request status` | — |
| Primary content | `main` | Implicit | `main` |
| Trip planning column | `aside` | `Trip planning` | `complementary` |
| Map column | `section` | `Route map` | `region` |
| Analysis column | `aside` | `Route analysis` | `complementary` |
| Toast layer | `div`, sibling of `main` | `Notifications` | — |

Each panel inside a column is a `section` with a heading, and each heading level descends by exactly one from its container. The document has one `h1`, in the trip planning column, and every `section` heading is an `h2` with `h3` used only inside a panel. No heading level is chosen for its visual size; sizing is a `styles.css` concern.

A skip link is the first focusable element in the document. It targets the `main` element and is visible on focus, so a keyboard user does not traverse the header on every page load.

## Form Controls

### Text inputs

| Control | Association | Additional attributes |
|---------|-------------|-----------------------|
| Origin | `label` with `htmlFor="origin"` | `required`, `maxLength={120}`, `autoComplete="off"` |
| Destination | `label` with `htmlFor="destination"` | `required`, `maxLength={120}`, `autoComplete="off"` |

The suggestion hint line is associated with the destination field through `aria-describedby`, so a screen reader announces the example places as part of the field rather than as orphaned text after it.

When a `validation_error` response names a field that matches an input, that input receives `aria-invalid="true"` and `aria-describedby` pointing at the corresponding entry in the banner's field list, and focus moves to it. Focus moves only in response to a submit the user initiated; it never moves as a side effect of a debounced re-plan.

### Sliders

Each scenario control is a `label` containing the control name, an `output`, and a range input.

```tsx
<label className="control" htmlFor="scenario-hour">
  <span>Time of day</span>
  <output htmlFor="scenario-hour">{hourLabel(scenario.hour)}</output>
  <input
    id="scenario-hour"
    type="range"
    min={0}
    max={23}
    step={1}
    value={scenario.hour}
    aria-valuetext={hourLabel(scenario.hour)}
    onChange={handleHourChange}
  />
</label>
```

| Requirement | Reason |
|-------------|--------|
| `output` carries `htmlFor` naming the input | Binds the displayed value to the control it describes |
| `aria-valuetext` carries the formatted label | Without it, the hour slider announces `17` and the weather slider announces `1`, neither of which is meaningful |
| `step={1}` on all three | Arrow keys move by exactly one unit, matching the integer contract |
| Native `input type="range"` | Supplies arrow, `Home`, `End`, and `Page` key handling with no custom key code |

`aria-valuetext` values are the same strings the `output` displays: `5:00 PM`, `Light rain`, `56%`. Formatting lives in `src/utils/format.ts` and `src/constants/scenario.ts`, so the visible label and the announced label cannot diverge.

Because the sliders are removed from the tree in Real-Time mode rather than disabled, a screen reader user encounters the explanatory sentence instead of three controls that report values the server ignores. That is the accessible behavior as well as the honest one.

## Keyboard Operability

### Mode switch

| Aspect | Behavior |
|--------|----------|
| Elements | Two native `button` elements inside a `div role="group"` named `Planning mode` |
| State | `aria-pressed={mode === value}` on each button |
| Labels | The visible text `Simulated` and `Real-Time`, which are also the accessible names |
| Keyboard | `Tab` reaches each button; `Enter` and `Space` activate |
| Focus after activation | Stays on the activated button, so a user can switch back without re-navigating |

Both buttons are in the tab order. A roving-tabindex tab pattern is not used, because two toggle buttons do not benefit from it and it would remove the second option from sequential navigation.

### Route cards

| Aspect | Behavior |
|--------|----------|
| Element | Native `button` with `type="button"` |
| State | `aria-pressed` reflecting selection |
| Accessible name | Composed from the route name, the recommended badge when present, the adjusted ETA, the distance, and the price, so the card is fully described without a visual scan |
| Keyboard | `Tab` between cards; `Enter` or `Space` selects |
| Focus after selection | Stays on the activated card; the map and analysis panels update around it |

In Real-Time mode the single card renders as a non-interactive summary and is therefore not in the tab order. There is nothing to activate, and a focusable element that does nothing is a worse experience than one that is absent.

### Focus visibility and traps

| Rule | Detail |
|------|--------|
| Focus indicator | A `:focus-visible` outline of at least 2 px with at least 3:1 contrast against its background, on every interactive element |
| No suppression | `outline: none` appears nowhere in `src/styles.css` without an equally visible replacement |
| Map region | The Google map is reachable by `Tab` and escapable by `Tab`; a keyboard user is never held inside it |
| Toast | Never steals focus. It is announced through its live region, and its dismiss and retry buttons sit in the natural tab order |
| Banner | `StatusBanner` does not move focus on appearance, except for the submit-initiated validation case described above |
| No modals | The interface contains no dialog, so no focus trapping is required anywhere |

Tab order follows document order: skip link, header, trip planning column, map region, analysis column, toast layer. No positive `tabIndex` value is used anywhere, since a positive value reorders the whole document and is unmaintainable.

## Live Regions

| Region | Element | Attributes | Announces |
|--------|---------|------------|-----------|
| Request status | Header status line | `aria-live="polite"`, `aria-atomic="true"` | `Starting`, `Planning`, `Recalculating`, `Plan ready`, `Problem` |
| Plan result summary | Visually hidden paragraph in the analysis column | `aria-live="polite"` | The selected route's name, adjusted ETA, distance, and price after each successful plan |
| Error banner | `StatusBanner` in an error state | `role="alert"` | The server `detail` and its guidance sentence |
| Progress and empty banner | `StatusBanner` in a loading or empty state | `role="status"` | `Planning your route...` or the empty-state sentence |
| Toast, failure | `Toast` | `role="alert"` | The failure `detail` and guidance |
| Toast, informational | `Toast` | `role="status"` | Geolocation denial and similar notices |

Progress announcements are `polite` so a slider drag does not interrupt whatever the user is reading. Errors are assertive because they change what the user should do next.

Live region containers are present in the DOM from first render and have their text swapped, rather than being mounted when a message appears. A region mounted at the same moment as its content is frequently not announced at all.

The status line announces at most one message per settled request. The 180 ms debounce that collapses a slider drag into one request also collapses it into one announcement, which is why the debounce is an accessibility measure and not only a performance measure.

## Non-Visual Parity With The Map

Every fact the map draws has a text location. This table is the parity contract; a map feature added without a row here is incomplete.

| Map-conveyed fact | Text equivalent | Location |
|-------------------|-----------------|----------|
| A route exists as an alternative | Route card with name and objective | `RouteOptionList` |
| Route length | `distance_miles` | Route card and selected-route summary |
| Route travel time | `adjusted_eta_minutes`, with `base_eta_minutes` alongside | Route card and selected-route summary |
| Which route is selected | `aria-pressed` on the card, plus the selected-route summary heading | `RouteOptionList`, `AnalysisPanel` |
| Which route is recommended | `Recommended` text badge | `RouteOptionList` |
| Overall route congestion | `congestion_score` as `56 / 100` | Selected-route summary |
| Per-stretch slowness that stroke color shows | Per-segment congestion percentage, average speed against speed limit, and adjusted against free-flow minutes | `SegmentTable` |
| Which roads the route uses | `segment.name` per row | `SegmentTable` |
| Traffic volume relative to capacity | `volume_vehicles_hour` against `capacity_vehicles_hour` | `SegmentTable` |
| Weather conditions affecting the drive | `weather.label` with `weather.source` | Selected-route summary |
| Where the numbers come from | `plan.notice` and `route.data_source`, verbatim | `AnalysisPanel` |

A user who never perceives the map receives the route set, the recommendation, both ETAs, the distance, the fare with its full breakdown, and per-segment conditions for every stretch of the selected route. What the map adds is spatial context, not data.

## Map Region Semantics

| Aspect | Behavior |
|--------|----------|
| Container | `section` with `role="region"` and `aria-label="Route map"` |
| Description | `aria-describedby` pointing at a visually hidden paragraph inside the region |
| Description content | The selected route's name, adjusted ETA, distance, and the count of intervals in each non-normal traffic category, for example `Balanced route, 27.9 min, 12.3 mi, 4 slow stretches and 1 heavy stretch` |
| Description updates | Rewritten whenever `selectedRoute` or the plan changes; it is not a live region, so it is read on entry rather than announced continuously |
| Polylines | Not exposed to assistive technology; they are `clickable: false` and carry no accessible name |
| Google controls | Left enabled, since they carry their own accessible names from the Maps JavaScript API |
| Pointer requirement | No information requires hovering, dragging, or a pinch gesture to obtain |
| `View all` toggle | A native `button` with `aria-pressed`, inside the map region and in the tab order |
| Map unavailable | The region renders `StatusBanner` with the server `detail`, so entering the region explains the situation rather than presenting silence |

The map is announced as a described region rather than as an image, because it is an interactive surface, and rather than as an application, because doing so would suppress the screen reader's normal navigation keys inside a region a user has no reason to explore key by key.

## Color And Contrast

| Surface | Requirement |
|---------|-------------|
| Body text on panel backgrounds | At least 4.5:1 |
| Large text, 18.66 px bold or 24 px and above, including the hero ETA and fare figures | At least 3:1 |
| Control boundaries: input borders, slider tracks, card borders, button outlines | At least 3:1 against the adjacent background |
| Focus indicator | At least 3:1 against the background it sits on |
| Traffic strokes against the dark map | At least 3:1, which the Google palette satisfies on the `DARK` color scheme |
| Disabled submit button | Exempt from contrast minimums, but distinguished by more than color: the label changes to `Planning...` |

### Color is never the only carrier

| Meaning | Color channel | Additional channel |
|---------|---------------|--------------------|
| Traffic category on a stroke | `#4285F4`, `#FBBC04`, `#EA4335` | Per-segment percentages, speeds, and time comparisons in `SegmentTable` |
| Selected route | Increased stroke opacity | Stroke weight 6 against 4, `aria-pressed` on the card, and the selected-route summary heading |
| Route identity | `route.color` accent on the card | The route's name, `Fastest`, `Balanced`, or `Low traffic` |
| Recommendation | Badge styling | The literal word `Recommended` |
| Error state | Banner accent color | `role="alert"`, the heading text, and the guidance sentence |
| Request in flight | Status dot color | The status words `Planning` and `Recalculating` |

Scenario color correction is bounded so a `SLOW` stroke stays recognizably amber and a `TRAFFIC_JAM` stroke stays recognizably red at every slider position, as specified in [map-rendering.md](map-rendering.md). No slider setting can push one category into another category's hue, so a user relying on color still reads the categories consistently.

## Reduced Motion

`src/styles.css` carries a `prefers-reduced-motion: reduce` block:

| Effect | Default | Reduced motion |
|--------|---------|----------------|
| Toast entry and exit | Slide and fade | Appears and disappears with no transition |
| Route card hover and selection | Transform and color transition | Color change only, no transform |
| Panel and banner appearance | Fade | No transition |
| Loading indicator | Continuous spin | A static indicator paired with the status text |
| Map camera fitting | The Maps default `fitBounds` behavior | Unchanged; no easing or animated pan is added by the View, so there is nothing extra to suppress |

No animation conveys information on its own. Every state an animation accompanies is also stated in text, so suppressing motion removes decoration and never removes meaning. No content flashes, and no animation loops more than five seconds outside the loading indicator, which is bounded by the request it represents.

## Acceptance Criteria

- [ ] The document exposes exactly one `banner`, one `main`, and two named `complementary` landmarks.
- [ ] A skip link is the first focusable element, targets `main`, and is visible on focus.
- [ ] Heading levels descend without skipping, and the document has exactly one `h1`.
- [ ] Every `input` has a programmatically associated `label`; no control relies on placeholder text as its label.
- [ ] Each slider has an `output` bound by `htmlFor` and an `aria-valuetext` matching the displayed label.
- [ ] Arrow keys move each slider by exactly one unit.
- [ ] The mode switch is two native buttons in a named group, each exposing `aria-pressed`.
- [ ] Every route card is a native button exposing `aria-pressed`, activatable by `Enter` and `Space`.
- [ ] Each route card's accessible name includes its name, ETA, distance, and price.
- [ ] Focus remains on the activated control after a mode change or route selection.
- [ ] A visible focus indicator of at least 2 px and 3:1 contrast appears on every interactive element.
- [ ] `Tab` enters and leaves the map region without trapping focus.
- [ ] The toast never receives focus automatically.
- [ ] Live regions exist in the DOM from first render and have their content swapped rather than being mounted when a message arrives.
- [ ] Request status changes are announced politely; errors are announced assertively.
- [ ] A slider drag produces exactly one status announcement.
- [ ] The map region has `aria-label="Route map"` and an `aria-describedby` target naming the selected route, its ETA, its distance, and its slow and heavy stretch counts.
- [ ] Every row of the parity table has a rendered text equivalent.
- [ ] Body text meets 4.5:1 and control boundaries meet 3:1 against their adjacent backgrounds.
- [ ] Every meaning listed in the color table is carried by at least one non-color channel.
- [ ] With `prefers-reduced-motion: reduce`, no transform or fade transition runs and the loading indicator does not spin.
- [ ] No information requires hover, drag, or a pinch gesture to obtain.

## Planned Tests

| Test ID | Level | Target file | Assertion |
|---------|-------|-------------|-----------|
| T-36 | component | `src/App.test.tsx` | The rendered application exposes one `banner`, one `main`, and two `complementary` landmarks with the documented accessible names, and the skip link is the first focusable element; both mode buttons are in a group named `Planning mode`, expose `aria-pressed` matching the active mode, and activate by keyboard with focus retained; each route card's accessible name contains the route name, adjusted ETA, distance, and price, keyboard activation selects the card, and the Real-Time single card is not in the tab order |
| T-26 | component | `src/components/ScenarioControls.test.tsx` | Each slider is retrievable by its label text, exposes an `output` bound by `htmlFor`, and reports `aria-valuetext` of `5:00 PM`, `Light rain`, and `56%` for the default scenario |
| T-37 | component | `src/App.test.tsx` | The status live region moves from `Planning` to `Plan ready` across one request, an error response renders a `role="alert"` node containing the server `detail`, and ten scenario changes inside the debounce window produce one status announcement |
| T-31 | component | `src/components/RouteMap.test.tsx` | The map region exposes `aria-label="Route map"` and an `aria-describedby` target containing the selected route's name, adjusted ETA, distance, and non-normal interval counts, updated on selection change |
| T-39 | component | `src/components/SegmentTable.test.tsx` | Every fact in the parity table is present as text: the segment table exposes per-segment congestion, speed against limit, and adjusted against free-flow minutes for the selected route, with the map region stubbed out |

Level `component` denotes rendered React behavior in jsdom with Testing Library, including a full-`App` flow against a stubbed network layer. The automated rule-based accessibility check named by NFR-4.8 is P2 work; the tests above are explicit assertions that do not depend on it.

## Agent Implementation Notes

- Query by role and accessible name in tests. A test that reaches an element by CSS class will keep passing after the element stops being a button, which is exactly the regression these tests exist to catch.
- Compose route card accessible names from the same formatted strings the card displays, using the helpers in `src/utils/format.ts`. A separately authored `aria-label` drifts from the visible text within a release or two.
- Set `aria-valuetext` on every slider without exception. Two of the three sliders announce a meaningless bare integer without it, and the third announces a number with no unit.
- Render live region containers unconditionally and swap their text content. Conditional mounting is the most common reason an announcement never reaches a screen reader.
- Prefer removing a control to disabling it when it has no effect, which is why `ScenarioControls` unmounts in Real-Time mode and why the single Real-Time route card is a static summary rather than a disabled button.
- Keep the map description text in `RouteMap`, derived from the selected route, and count non-normal traffic intervals from the same slice list that produces the strokes, so the description cannot describe geometry the map is not drawing.
- Verify contrast against the actual `DARK` color scheme surfaces rather than against pure black. The rendered panel backgrounds are lighter than the token values suggest, and a ratio computed against black overstates compliance.
- Do not add camera easing, animated marker drops, or transition effects to the map. There is no reduced-motion escape hatch for motion the Maps API is instructed to perform, so the simplest compliance strategy is to never request it.
