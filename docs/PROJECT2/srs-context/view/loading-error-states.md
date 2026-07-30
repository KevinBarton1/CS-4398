# View Context — Loading, Empty, Error, and Degraded States

**Layer:** View
**Target modules:** `src/components/StatusBanner.tsx`, `src/components/Toast.tsx`, `src/components/AppHeader.tsx`, `src/api/client.ts`, `src/hooks/useRoutePlan.ts`, `src/hooks/useMapConfig.ts`
**Related:** [app-composition.md](app-composition.md), [route-scenario-forms.md](route-scenario-forms.md), [map-rendering.md](map-rendering.md), [results-analysis.md](results-analysis.md), [accessibility.md](accessibility.md), [../controller/validation-error-handling.md](../controller/validation-error-handling.md), [../architecture/state-diagrams.md](../architecture/state-diagrams.md)

## Purpose

Define every non-success state the interface can be in, what each one renders, which controls it disables, and how the error envelope's `code` selects presentation. The organizing principle is that a failure costs the user nothing they had already earned: their typed inputs, their scenario settings, their selected route, and the last plan they successfully received all survive.

The server owns error wording. `detail` is displayed as written. The `code` selects where the message appears, whether a retry is offered, and which single sentence of local guidance accompanies it.

## Requirements

| ID | Requirement | Status | Phase |
|----|-------------|--------|-------|
| FR-7.3 | The server's `detail` string is rendered verbatim for every non-2xx response, and a validation failure lists the offending fields from the `fields` array | Target | P1 |
| FR-7.2 | Each failure class maps to exactly one `code` and status, and presentation branches on the `code` rather than on the HTTP status alone | Target | P1 |
| FR-7.4 | A failed request preserves all form inputs, the scenario, the selection, and the last plan | Target | P1 |
| FR-7.8 | Every recoverable failure offers a retry affordance with explicit retry guidance | Target | P1 |
| FR-7.6 | A denied geolocation permission produces a toast and leaves manual entry working | Target | P1 |
| FR-7.5 | A map configuration failure is scoped to the map region | Target | P1 |
| NFR-1.2 | A loading state is visible within 100 ms of a request starting | Target | P1 |
| NFR-2.3 | No single failed dependency renders the application unusable | Target | P1 |
| NFR-2.5 | A failed or repeatedly failing re-plan keeps the previously rendered plan and marks it as an explicit degraded state rather than presenting stale values as current | Target | P1 |
| NFR-1.5 | Superseded requests are aborted, never write state, and a stale response never overwrites a newer one | Target | P1 |
| NFR-4.4 | Status changes and errors are announced to assistive technology | Target | P1 |

## State Model

`status` is a single string union in `src/types.ts`, owned by `useRoutePlan`. Exactly one value holds at a time.

```ts
export type RequestStatus = "idle" | "loading" | "success" | "empty" | "error";
```

The map region has its own independent status from `useMapConfig`, because the map and the plan fail separately and must be able to.

### State table

| State | Entered when | Planner column | Map region | Analysis column | Header status | Disabled controls |
|-------|--------------|----------------|------------|-----------------|---------------|-------------------|
| `idle` | Before the first request settles on a cold mount | Form with defaults, no route cards | Map placeholder while the configuration loads | Placeholder card | `Starting` | None |
| `loading`, no prior plan | First request in flight | Form plus a `StatusBanner` reading `Planning your route...` | Map placeholder | Placeholder card | `Planning` | Submit button |
| `loading`, prior plan present | Re-plan in flight | Previous route cards, dimmed but readable and still selectable | Previous strokes stay drawn | Previous values stay rendered | `Recalculating` | Submit button |
| `success` | 2xx response with a non-empty `routes` array | Route cards | Map with strokes | Full analysis | `Plan ready` | None |
| `empty` | 2xx response with an empty `routes` array | `StatusBanner` reading `No route alternatives came back for this trip.` with retry | Map at default camera, no strokes | Placeholder card | `Plan ready` | None |
| `error`, no prior plan | Non-2xx or transport failure with `plan === null` | `StatusBanner` with `detail`, guidance, and retry | Map at default camera, no strokes | Placeholder card | `Problem` | None |
| `error`, prior plan present | Non-2xx or transport failure with a prior plan | Previous route cards plus a stale marker; the failure appears as a toast | Previous strokes stay drawn | Previous values plus the stale marker | `Problem` | None |
| Map unavailable | `useMapConfig` errored, or the Maps JavaScript API failed to load | Unaffected | `StatusBanner` with `detail` and retry | Unaffected | Unaffected by this failure | None |

Text inputs and the mode switch are never disabled. Only the submit button is, and only while a request is in flight, and only to prevent a duplicate submission. A user who realizes mid-request that they typed the wrong destination should be able to fix it immediately.

The `empty` state is defensive. The contract specifies three routes in Simulated mode and one in Real-Time mode, so an empty array indicates an upstream anomaly rather than a normal outcome. It is modeled explicitly so that it cannot be mistaken for `loading` and leave the user watching an interface that will never change.

### Stale marker

When a re-plan fails while a previous plan is on screen, the previous plan stays rendered and carries one line of context:

```
Showing the last successful plan. The most recent update did not complete.
```

The alternative, clearing the screen, punishes the user for a transient network failure by destroying results they already had.

## Error Envelope Handling

`src/api/client.ts` is the only module that reads a `Response`. It normalizes every failure into one shape before anything renders.

```ts
export interface ApiError {
  detail: string;
  code: ApiErrorCode | null;
  fields?: ValidationField[];
  status?: number;
}
```

| Situation | `client.ts` behavior |
|-----------|----------------------|
| 2xx with a JSON body | Returns the parsed body, typed from `src/types.ts` |
| Non-2xx with a parseable envelope | Throws an `ApiError` carrying `detail`, `code`, `status`, and `fields` when present |
| Non-2xx whose body is not a parseable envelope | Throws an `ApiError` with `code: null` and a locally authored `detail` |
| `fetch` rejects, for example a dropped connection | Throws an `ApiError` with `code: null` and a locally authored `detail` |
| The request was aborted | Rethrows the `AbortError` unchanged; `useRoutePlan` recognizes and discards it |

`code: null` is a View-local sentinel for "no server code available." It is not a wire value and is never sent anywhere. It exists so that presentation has one exhaustive switch with a defined default rather than a chain of loose checks.

### Code to presentation mapping

| `code` | Status | Placement | Guidance sentence rendered under `detail` | Retry offered |
|--------|--------|-----------|-------------------------------------------|---------------|
| `validation_error` | 422 | Inline banner in the planner column, plus a list of `fields` entries | `Correct the highlighted fields and plan again.` | No; the user must change an input |
| `invalid_location` | 400 | Inline banner in the planner column | `Try a nearby landmark, a full street address, or one of the suggested Austin places.` | No |
| `same_origin_destination` | 400 | Inline banner in the planner column | `Choose a destination that differs from the starting point.` | No |
| `no_route_found` | 400 | Inline banner in the planner column | `No driving route connects these two places. Try a different destination.` | No |
| `maps_not_configured` | 503 | Inline banner in whichever region failed: the map region for `GET /api/map/config`, the planner column for `POST /api/plan` | `The server is missing its Google Maps credential. An administrator has to configure it before planning works.` | Yes |
| `upstream_unavailable` | 502 | Toast when a plan is already on screen, otherwise an inline banner in the planner column | `Google Maps did not answer successfully. Your inputs are unchanged; try again in a moment.` | Yes |
| `upstream_timeout` | 504 | Toast when a plan is already on screen, otherwise an inline banner in the planner column | `Google Maps took too long to answer. Try again, and move the scenario sliders in fewer, larger steps if this repeats.` | Yes |
| `null` | none | Toast when a plan is already on screen, otherwise an inline banner in the planner column | `Could not reach TrafficScope. Check your connection and try again.` | Yes |

Two rules generate this table and should be applied to any code added later:

1. **Who can fix it decides the placement.** A failure the user fixes by editing an input belongs next to the inputs, as a persistent banner. A failure the user fixes by waiting belongs in a toast that does not occupy the form.
2. **Whether retrying the identical request could succeed decides the retry affordance.** Retrying `invalid_location` with unchanged text will fail identically, so offering retry would waste the user's time; retrying `upstream_timeout` may well succeed.

`maps_not_configured` is the one code that can arrive from either endpoint, and it is placed in the region that produced it. From `GET /api/map/config` it means the browser key is missing and only the map is affected. From `POST /api/plan` it means the server key is missing and planning itself is unavailable.

### Validation field list

When `code` is `validation_error`, the envelope adds a `fields` array. The banner renders `detail` as the heading, then one list item per entry. Entries are display-only: the View shows each entry's field name and message and draws no inference from the field name beyond moving focus to a matching input when one exists.

```ts
export interface ValidationField {
  field: string;
  message: string;
}
```

A `validation_error` naming `hour`, `weather`, or `congestion` indicates a client defect rather than user error, since the sliders make out-of-range values unreachable. It is still displayed rather than swallowed, because a silently discarded contract violation is a bug that hides itself.

## Toast Versus Inline Banner

| Property | `StatusBanner` | `Toast` |
|----------|----------------|---------|
| Lifetime | Persists until the state changes | Auto-dismisses after 6 seconds, or on user dismiss |
| Placement | Inside the region it describes | Fixed layer, a sibling of `main` |
| Occupies layout | Yes | No |
| Dismissible | No; it describes current state | Yes, via a labeled close button |
| Carries retry | Yes, when the code permits | Yes, when the code permits |
| Used for | Persistent conditions: loading with no prior plan, empty, input-correctable errors, configuration failures | Transient conditions: retryable upstream failures over an existing plan, geolocation denial |
| Announcement | `role="status"` for progress and empty, `role="alert"` for errors | `role="status"` for informational, `role="alert"` for failures |

A toast never carries the only copy of information the user needs to act on. Retryable failures also leave the stale marker in the panels, so a toast the user missed does not leave them believing stale values are current.

Only one toast is shown at a time. A new toast replaces the current one rather than stacking, and its dismissal timer restarts. Hovering or focusing a toast pauses the timer so a keyboard user reading it is not interrupted mid-sentence.

### Geolocation denial

Geolocation failures are browser-side and produce no error envelope. They are always toasts, never banners, and their messages are authored in the View. The three cases and their exact strings are specified in [route-scenario-forms.md](route-scenario-forms.md). In every case the origin field keeps its previous contents and the form stays submittable.

## Input And State Preservation

On any failed plan request, `useRoutePlan` writes `error` and `status` and nothing else.

| Value | On failure |
|-------|-----------|
| `origin`, `destination` | Unchanged |
| `mode` | Unchanged; the switch continues to show what the user chose |
| `scenario` | Unchanged, including a value the failed request was carrying |
| `plan` | Unchanged; a prior successful plan stays rendered |
| `selectedRouteId` | Unchanged |
| `viewAll` | Unchanged |
| `scenarioApplied` | Unchanged, because it is derived from the surviving `plan` |
| Map camera | Unchanged; no refit occurs, since the plan payload did not change |

A failure is therefore a purely additive state change. Clearing it requires a successful response or a state change that supersedes it: a fresh submit, a mode change, a scenario change, or a retry.

## Abort Handling

| Rule | Detail |
|------|--------|
| One controller at a time | `useRoutePlan` keeps the current `AbortController` in a ref |
| Abort before issuing | Every new request aborts the previous one before creating its own controller |
| Signal plumbing | The controller's `signal` is passed through `client.ts` to `fetch` |
| Identity check | After awaiting, a response whose controller is no longer the ref's current value is discarded even if it resolved successfully |
| `AbortError` handling | Caught and swallowed: no `error`, no `status` transition, no toast, no log entry the user can see |
| Loading state | `status` stays `loading` across an abort-and-reissue, so a slider drag shows one continuous loading state rather than a flicker per request |
| Unmount | The effect cleanup aborts any in-flight request, so no state is written after unmount |

An abort is a normal event during a slider drag or a rapid mode change. Treating it as a failure would fill the screen with toasts during ordinary use, which is why it is explicitly not an error path.

The identity check exists because aborting is advisory: a response can already be in flight in the microtask queue when `abort()` is called. Comparing controller identity after the await is what actually guarantees that only the newest request writes state.

## Retry

| Affordance | Location | Action |
|-----------|----------|--------|
| `Retry` button in `StatusBanner` | Planner column, for plan failures | Reissues `POST /api/plan` with the current inputs, preserving selection |
| `Retry` button in `StatusBanner` | Map region, for configuration failures | Reissues `GET /api/map/config` and clears the cached failure |
| `Retry` button in `Toast` | Toast layer | Reissues `POST /api/plan` with the current inputs, preserving selection |
| Resubmitting the form | Planner column | Reissues with `preserveSelection: false`, since the trip may have changed |

Retry sends the same request the failure came from; it does not alter inputs, fall back to a different mode, or silently substitute defaults. No automatic retry, backoff loop, or polling is performed. Retrying is the user's decision, which keeps a failing upstream from being hammered by an interface the user has walked away from.

## Acceptance Criteria

- [ ] A loading indication is visible within 100 ms of a request starting.
- [ ] While a re-plan is in flight, the previous route cards, strokes, and analysis values stay on screen and readable.
- [ ] The submit button is the only control disabled during a request; text inputs, sliders, and the mode switch stay enabled.
- [ ] A 2xx response with an empty `routes` array produces the `empty` state, not a stuck `loading` state.
- [ ] Every non-2xx response renders its `detail` string verbatim.
- [ ] Each of the seven documented codes maps to the placement, guidance sentence, and retry availability in the mapping table.
- [ ] A `validation_error` response lists one entry per element of `fields`.
- [ ] A response body that is not a parseable envelope produces a `code: null` error with a locally authored message, not an unhandled exception.
- [ ] A `fetch` rejection produces a `code: null` error, not an unhandled rejection.
- [ ] A failed re-plan leaves `origin`, `destination`, `mode`, `scenario`, `selectedRouteId`, and `plan` untouched and adds the stale marker.
- [ ] A failed re-plan over an existing plan surfaces as a toast; a failure with no prior plan surfaces as an inline banner.
- [ ] An aborted request produces no error state, no toast, and no `status` transition.
- [ ] A rapid sequence of scenario changes produces one continuous loading state, not one flicker per aborted request.
- [ ] A response that resolves after its request was superseded does not overwrite the newer plan.
- [ ] Unmounting during a request writes no state afterward.
- [ ] `Retry` reissues the same request with unchanged inputs and clears the error on success.
- [ ] No automatic retry or polling occurs after any failure.
- [ ] A `GET /api/map/config` failure leaves the planner form, route cards, price summary, and segment table fully interactive.
- [ ] Only one toast is present at a time, and it auto-dismisses after 6 seconds unless hovered or focused.

## Planned Tests

| Test ID | Level | Target file | Assertion |
|---------|-------|-------------|-----------|
| T-30 | component | `src/components/StatusBanner.test.tsx` | For each of the seven codes, the banner renders the server `detail`, the documented guidance sentence, and a retry button only where the mapping table permits one; a 422 envelope lists its `fields` entries and a body that is not a parseable envelope renders a `code: null` message; a 2xx response with an empty `routes` array renders the empty-state banner with a retry button and no route cards; and a failed re-plan preserves `origin`, `destination`, `mode`, `scenario`, `selectedRouteId`, and the prior `plan` |
| T-27 | component | `src/hooks/useRoutePlan.test.ts` | A superseded request that resolves late does not overwrite the newer plan, and its `AbortError` sets no error and produces no toast |
| T-37 | component | `src/App.test.tsx` | A second toast replaces the first rather than stacking, auto-dismisses after its timer, and uses `role="alert"` for failures and `role="status"` for informational messages; with a successful plan followed by an `upstream_timeout` re-plan, the previous route cards and analysis values remain on screen, the stale marker appears, and the timeout guidance appears in a toast |

## Agent Implementation Notes

- Model status as the string union, never as `{ loading: boolean; error: unknown }`. The boolean pair permits `loading` and `error` simultaneously, and `empty` cannot be expressed in it at all.
- Normalize every failure inside `src/api/client.ts`. If a component or hook ever inspects `response.status`, the normalization boundary has leaked and the code-to-presentation switch is no longer exhaustive.
- Write the code switch with an explicit `default` branch that handles `null` and any future code. A `code` the View does not recognize must still display its `detail`.
- Compare `AbortController` identity after the await, not just before the fetch. Checking only `signal.aborted` misses a response that resolved in the same tick as the abort.
- Catch `AbortError` by name at the top of the catch block and return immediately, before any state is written. Everything else in that block assumes a real failure.
- Keep the map's status separate from the plan's status. One shared status makes a missing browser key look like a planning outage and disables controls that work perfectly well.
- Author the guidance sentences as a lookup keyed by `code` in `StatusBanner.tsx`, and keep them one sentence each. They are local guidance, not error text; the server's `detail` remains the message of record and is never replaced.
- Do not add retry backoff, request queueing, or offline detection. Retry stays a user action at P1; automatic retry with jittered backoff is FR-7.10 and arrives at P2. Marking a preserved stale plan as an explicit degraded state is not deferred: NFR-2.5 requires it at P1.
