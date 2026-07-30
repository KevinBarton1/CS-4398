# View Context — Trip Form and Scenario Controls

**Layer:** View
**Target modules:** `src/components/RoutePlannerForm.tsx`, `src/components/ScenarioControls.tsx`, `src/constants/scenario.ts`, `src/utils/format.ts`, `src/hooks/useRoutePlan.ts`
**Related:** [app-composition.md](app-composition.md), [results-analysis.md](results-analysis.md), [loading-error-states.md](loading-error-states.md), [accessibility.md](accessibility.md), [../controller/validation-error-handling.md](../controller/validation-error-handling.md), [../controller/mode-policies.md](../controller/mode-policies.md), [../model/weather-scenarios.md](../model/weather-scenarios.md)

## Purpose

Specify every input surface the user manipulates: the origin and destination text fields, the submit action, the browser geolocation assist, and the three scenario sliders. This document fixes label text, defaults, ranges, live value formatting, and the exact relationship between browser-side constraints and server-side validation.

Two inputs behave differently from the rest. Origin and destination require an explicit submit, because resolving a place is expensive and a keystroke is not an intent. Mode and scenario changes re-plan automatically after a 180 ms debounce, because those are exploratory controls whose value is immediate feedback.

## Requirements

| ID | Requirement | Status | Phase |
|----|-------------|--------|-------|
| FR-1.1 | An origin text field accepts a free-text Austin-area place | Target | P1 |
| FR-1.2 | A destination text field accepts a free-text Austin-area place | Target | P1 |
| FR-1.3 | A geolocation assist fills the origin field with the resolved browser coordinates | Target | P1 |
| FR-1.4 | Origin and destination submitted as free text are resolved server-side through the Google Places API | Target | P1 |
| FR-1.7 | The resolved place names returned by the server are shown alongside results | Target | P1 |
| FR-5.1 | A departure-hour slider covers 0 to 23 with default 17 | Target | P1 |
| FR-5.2 | A weather-severity slider covers 0 to 3 with default 1 | Target | P1 |
| FR-5.3 | A congestion slider covers 0 to 100 with default 56 | Target | P1 |
| NFR-7.6 | Each slider renders a live formatted value, carrying its unit or label, in an `output` element | Target | P1 |
| FR-5.4 | A reset action restores `defaultScenario` and re-plans | Target | P1 |
| FR-5.5 | Scenario changes re-plan after a 180 ms debounce | Target | P1 |
| FR-4.4 | Scenario controls are absent from the tree in Real-Time mode | Target | P1 |
| FR-7.6 | A denied geolocation permission produces a toast and leaves manual entry working | Target | P1 |
| NFR-1.2 | A slider change is reflected in results within 2 seconds | Target | P1 |
| NFR-4.1 | Every input has a programmatically associated label and, for sliders, an associated `output` | Target | P1 |
| NFR-5.3 | Defaults and weather labels are imported from `src/constants/scenario.ts` | Target | P1 |
| NFR-7.5 | The interface explains why scenario controls are unavailable in Real-Time mode | Target | P1 |

## `RoutePlannerForm`

### Fields

| Field | Element | Label | Default | Constraints |
|-------|---------|-------|---------|-------------|
| Origin | `input#origin` `type="text"` | `Starting point` | `Downtown Austin` | `required`, `maxLength={120}`, `autoComplete="off"` |
| Destination | `input#destination` `type="text"` | `Destination` | `Austin Airport` | `required`, `maxLength={120}`, `autoComplete="off"` |

Both defaults are seeded in `useRoutePlan` so the application can plan a route on first load without user input. The fields are controlled inputs; the value shown is always the raw user text, never the server's resolved name. The resolved names arrive as `plan.origin` and `plan.destination` and are displayed in the results area, described in [results-analysis.md](results-analysis.md).

### Supporting text

A single hint line sits below the destination field:

```
Try: The Domain, UT Austin, Zilker Park, Mueller, South Congress
```

These are suggestions rendered as static text, not an autocomplete menu. Place resolution happens server-side through Google Places; the View sends free text and never queries Google directly.

### Actions

| Action | Element | Behavior |
|--------|---------|----------|
| Submit | `button.primary` `type="submit"` | Calls `event.preventDefault()`, then plans with `preserveSelection: false` |
| Geolocation assist | `button` `type="button"` labeled `Use my current location` | Requests one position fix and writes it into the origin field |

### Submit and loading behavior

| `status` | Submit label | Submit disabled | Notes |
|----------|--------------|-----------------|-------|
| `idle` | `Plan routes` | no | Only before the first request settles |
| `loading` | `Planning...` | yes | Prevents a duplicate request from a double click |
| `success` | `Plan routes` | no | |
| `empty` | `Plan routes` | no | |
| `error` | `Plan routes` | no | Inputs stay editable so the user can correct and resubmit |

Text fields are never disabled, including while a request is in flight. A user who mistyped a destination can fix it during the request and submit again; the earlier request is aborted.

### Browser constraints and server validation

The browser constraints are a fast first filter, not the authority. The server re-validates every field and owns the error text.

| Concern | Browser side | Server side | Interaction |
|---------|--------------|-------------|-------------|
| Empty field | `required` blocks submit; the browser shows its native validation bubble and no request is sent | Rejects with `validation_error` (422) if a request somehow arrives empty | The View never has to author an "empty field" message |
| Over-long value | `maxLength={120}` prevents typing past 120 characters | Rejects values outside 1 to 120 characters after trimming with `validation_error` (422) | The browser limit matches the server limit exactly, so paste-truncation is silent rather than surprising |
| Leading and trailing spaces | Not trimmed in the field, so the user's text is preserved as typed | Trims before length checking and before resolution | The View sends the raw string and lets the server trim |
| Unresolvable place | No check possible | `invalid_location` (400) with a `detail` naming the offending text | Rendered as an inline banner in the planner column |
| Origin equals destination | No check | `same_origin_destination` (400) | Rendered as an inline banner in the planner column |
| Scenario out of range | Slider `min` and `max` make out-of-range values unreachable | `validation_error` (422) on `hour`, `weather`, or `congestion` | A 422 on a scenario field indicates a client defect, not user error |

Presentation for each `code` is specified in [loading-error-states.md](loading-error-states.md).

## Geolocation Assist

The assist is a convenience for filling the origin field. It is not a separate planning path and it introduces no new request field.

| Step | Behavior |
|------|----------|
| 1 | The user activates `Use my current location` |
| 2 | The View calls `navigator.geolocation.getCurrentPosition` with `{ enableHighAccuracy: false, timeout: 8000 }` |
| 3 | On success, the origin field is set to the coordinates formatted as `"lat, lng"` with five decimal places, for example `30.26720, -97.74310` |
| 4 | The user submits the form as usual; the coordinate text travels in the ordinary `origin` field of `POST /api/plan` |
| 5 | On denial or failure, a toast appears and the origin field keeps whatever it already contained |

The server has no `current location` alias and no special handling for a coordinate origin. It resolves the coordinate text through the same place-resolution path as any other origin string, and returns the resolved display name in `plan.origin`. If resolution fails, the response is an ordinary `invalid_location` error.

| Geolocation outcome | Toast text |
|---------------------|------------|
| Permission denied | `Location permission was denied. Enter a starting point manually.` |
| Position unavailable or timed out | `Could not read your location. Enter a starting point manually.` |
| API absent from the browser | `This browser does not provide location access. Enter a starting point manually.` |

In all three cases the origin field stays editable and the form stays submittable. Geolocation is never a precondition for planning.

## `ScenarioControls`

`ScenarioControls` renders the complete, closed set of three scenario variables. There is no fourth control, and no control is added for any value the server derives.

### Sliders

| Control | Field | Element | Range | Step | Default | `output` format | Example |
|---------|-------|---------|-------|------|---------|-----------------|---------|
| Time of day | `hour` | `input#scenario-hour` `type="range"` | 0 to 23 | 1 | 17 | 12-hour clock from `hourLabel` | `5:00 PM` |
| Weather | `weather` | `input#scenario-weather` `type="range"` | 0 to 3 | 1 | 1 | Label from `weatherLabels` | `Light rain` |
| Congestion | `congestion` | `input#scenario-congestion` `type="range"` | 0 to 100 | 1 | 56 | Integer percentage | `56%` |

`weatherLabels` is the ordered array `["Clear", "Light rain", "Heavy rain", "Severe"]` in `src/constants/scenario.ts`, indexed by severity. `hourLabel` lives in `src/utils/format.ts`:

```ts
export function hourLabel(hour: number): string {
  return `${hour % 12 || 12}:00 ${hour >= 12 ? "PM" : "AM"}`;
}
```

`hourLabel(0)` is `12:00 AM`, `hourLabel(12)` is `12:00 PM`, and `hourLabel(23)` is `11:00 PM`.

Each control is a `label` containing the control name, an `output` bound to the input's `id`, and the range input. The `output` updates on every pointer move, independent of the debounce, so the displayed value always matches the thumb position.

### Change handling

Each slider's `onChange` builds a complete next `Scenario` and hands it up:

```ts
onChange={(event) =>
  onScenarioChange({ ...scenario, [key]: Number(event.target.value) })
}
```

`Number(...)` is mandatory. Range inputs report strings, and sending `"56"` where the contract specifies an integer produces a `validation_error` response.

### Reset

A `Reset` button in the panel heading calls `onScenarioReset`, which sets state back to `defaultScenario` from `src/constants/scenario.ts`:

```ts
export const defaultScenario: Scenario = {
  hour: 17,
  weather: 1,
  congestion: 56,
};
```

Reset restores all three values in one state update, so it schedules one debounced re-plan rather than three. Reset is a no-op visually when the scenario already equals the defaults, but it still re-plans, which gives the user a way to force a fresh response.

### Debounce

| Property | Value |
|----------|-------|
| Delay | 180 ms after the last change |
| Scope | Shared by mode changes and scenario changes |
| Effect of a change inside the window | The pending timer is replaced; no request is sent for the superseded value |
| Effect on the in-flight request | Aborted when the new request is issued |

180 ms is short enough that a deliberate single click feels immediate and long enough that a slider drag collapses into one request. Local slider state is never debounced; only the network call is.

### Absence in Real-Time mode

`ScenarioControls` is removed from the tree, not disabled, whenever the current response reports `scenario_applied: false`. A disabled slider still shows a value and still implies that the value matters; in Real-Time mode the server ignores all three values entirely, so showing them would misstate what the interface controls.

| Aspect | Behavior |
|--------|----------|
| Condition | `scenarioApplied === false`, read from `plan.scenario_applied` |
| Rendering | `ScenarioControls` is not mounted; the analysis column closes the gap |
| Replacement text | `Real-Time mode plans for the current departure time using live Google Maps traffic. Scenario controls apply in Simulated mode.` |
| Local state | `scenario` values are retained in `useRoutePlan`, so switching back to Simulated mode restores the user's last settings rather than the defaults |
| Requests | The request body still carries `hour`, `weather`, and `congestion`; the server accepts and ignores them |

The replacement text is rendered where the panel would have been, so the absence is explained rather than merely observed.

## Acceptance Criteria

- [ ] The origin field defaults to `Downtown Austin` and the destination field to `Austin Airport`.
- [ ] Both text fields carry `required` and `maxLength={120}`.
- [ ] Clearing a text field and submitting sends no request; the browser blocks the submit.
- [ ] Typing in a text field alone never issues a plan request.
- [ ] Submitting issues one plan request and resets the selection to the recommended route.
- [ ] The submit button is disabled and labeled `Planning...` while a request is in flight; the text fields stay editable.
- [ ] The hint line lists The Domain, UT Austin, Zilker Park, Mueller, and South Congress.
- [ ] A successful geolocation fix writes `"lat, lng"` with five decimal places into the origin field and issues no request by itself.
- [ ] A denied geolocation permission shows the denial toast, leaves the origin field unchanged, and leaves the form submittable.
- [ ] The three sliders expose ranges 0 to 23, 0 to 3, and 0 to 100 with step 1.
- [ ] Each slider's `output` shows the 12-hour clock label, the weather label, or the percentage respectively, and updates on every change.
- [ ] Dragging one slider across ten values issues exactly one plan request.
- [ ] `Reset` restores `hour: 17`, `weather: 1`, `congestion: 56` and issues exactly one plan request.
- [ ] Scenario values are sent as numbers, never strings.
- [ ] With `scenario_applied: false`, no `type="range"` input exists in the document and the explanatory sentence is shown.
- [ ] Switching back to Simulated mode restores the user's previous scenario values, not the defaults.

## Planned Tests

| Test ID | Level | Target file | Assertion |
|---------|-------|-------------|-----------|
| T-25 | component | `src/App.test.tsx` | Both fields render with their default values, `required`, and `maxLength` of 120, and submitting calls the submit handler once without reloading the document |
| T-35 | component | `src/components/RoutePlannerForm.test.tsx` | A stubbed `getCurrentPosition` success sets the origin field to the five-decimal `"lat, lng"` string; a stubbed denial triggers the denial toast and leaves the origin field unchanged |
| T-26 | component | `src/components/ScenarioControls.test.tsx` | The three sliders expose the documented ranges, their `output` elements read `5:00 PM`, `Light rain`, and `56%` for the default scenario, and `Reset` emits `defaultScenario` in a single change event |
| T-27 | component | `src/hooks/useRoutePlan.test.ts` | Ten successive scenario changes inside 180 ms produce exactly one plan request, whose body carries numeric `hour`, `weather`, and `congestion` |

## Agent Implementation Notes

- Render the three sliders from a small local array of descriptors keyed by `keyof Scenario`, so adding a label or changing a range touches one line. The set of three keys is closed; the descriptor array is a rendering convenience, not an extension point.
- Format the geolocation coordinates with `toFixed(5)` on both components and join with `", "`. Five decimals is roughly one meter, which is more than enough for place resolution and short enough to remain readable in the field.
- Do not attempt browser-side place validation or coordinate range checks. Place resolution is a server responsibility, and duplicating it in the View creates two sources of truth for what counts as an Austin-area location.
- Keep the `output` value derived directly from `scenario`, not from the input's DOM value, so the rendered label cannot drift from the state that will be sent.
- Gate the scenario re-plan effect on `scenarioApplied`, not on `mode`. Gating on local `mode` re-plans once on the way into Real-Time mode for no reason.
- Retain scenario state when the controls unmount. Storing it in `useRoutePlan` rather than inside `ScenarioControls` is what makes this work without extra code.
- Author no client-side copy for validation failures. Render the server's `detail` string; the guidance sentence per `code` is defined in [loading-error-states.md](loading-error-states.md).
