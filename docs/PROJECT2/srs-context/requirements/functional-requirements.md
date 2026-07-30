# Functional Requirements — PROJECT2

**Scope:** TrafficScope rewrite. Future-state behavior only.
**Authority:** All names, fields, modes, and labels come from [../../README.md](../../README.md).
**Related:** [non-functional-requirements.md](non-functional-requirements.md), [traceability.md](traceability.md), [../architecture/architecture-overview.md](../architecture/architecture-overview.md)

## How To Read This Catalog

Every requirement carries a status and a phase.

| Column | Values |
|--------|--------|
| Status | `Target` — must be delivered in the stated phase. `Out of scope` — deliberately excluded from PROJECT2. |
| Phase | `P1` Core planning, `P2` Depth and resilience, `P3` Congestion heatmap, `—` for out-of-scope items. |
| Owner | The MVC context that owns the behavior. |

A requirement marked `P2` or `P3` describes work that does not exist yet. No PROJECT2 document may
describe it in the present tense.

---

## FR-1 Location Entry And Resolution

| ID | Requirement | Status | Phase | Owner |
|----|-------------|--------|-------|-------|
| FR-1.1 | The View shall provide a labeled text input for the trip origin, defaulting to `Downtown Austin`. | Target | P1 | View |
| FR-1.2 | The View shall provide a labeled text input for the trip destination, defaulting to `Austin Airport`. | Target | P1 | View |
| FR-1.3 | The View shall offer a browser geolocation assist that, when permission is granted, fills the origin input with the device position formatted as decimal `lat, lng` text. | Target | P1 | View |
| FR-1.4 | The Controller shall resolve `origin` and `destination` to coordinates server-side through the Google Places API (New) text search. | Target | P1 | Controller |
| FR-1.5 | When Places returns no usable result for a location, the Controller shall respond `400` with code `invalid_location` and a message naming the unresolved input. | Target | P1 | Controller |
| FR-1.6 | When `origin` and `destination` resolve to the same place, the Controller shall respond `400` with code `same_origin_destination`. | Target | P1 | Controller |
| FR-1.7 | The response shall report the resolved Places display names in `origin` and `destination`, not the raw user text. | Target | P1 | Controller |
| FR-1.8 | Place resolution results shall be cached by normalized query so that scenario-only re-plans issue no additional Places requests. | Target | P2 | Model |
| FR-1.9 | Typeahead place autocomplete in the origin and destination inputs. | Out of scope | — | — |
| FR-1.10 | Saved or favorite locations. | Out of scope | — | — |

**Acceptance criteria**

- [ ] Submitting `Downtown Austin` to `Austin Airport` returns `200` with resolved display names that differ from the submitted strings.
- [ ] Submitting an unresolvable destination returns `400` with `code` equal to `invalid_location`.
- [ ] Submitting the same text for both fields returns `400` with `code` equal to `same_origin_destination`.
- [ ] Denying the geolocation prompt leaves the origin input editable and shows a dismissible notice.

---

## FR-2 Route Planning, ETA, And Comparison

| ID | Requirement | Status | Phase | Owner |
|----|-------------|--------|-------|-------|
| FR-2.1 | The Controller shall compute driving route alternatives server-side through the Google Routes API `computeRoutes` method. | Target | P1 | Controller |
| FR-2.2 | Simulated mode shall return up to three alternatives with `name` values `Fastest`, `Balanced`, and `Low traffic` and a distinct `objective` per alternative. | Target | P1 | Controller |
| FR-2.3 | Real-Time mode shall return exactly one alternative. | Target | P1 | Controller |
| FR-2.4 | Each route shall report `distance_miles` to one decimal place. | Target | P1 | Model |
| FR-2.5 | Each route shall report `base_eta_minutes` derived from the Google static duration. | Target | P1 | Model |
| FR-2.6 | Each route shall report `adjusted_eta_minutes` computed by the active mode policy. | Target | P1 | Controller |
| FR-2.7 | Each route shall include at least one `RoadSegment` carrying name, length, lanes, speed limit, average speed, volume, capacity, free-flow minutes, adjusted minutes, traffic ratio, and polyline. | Target | P1 | Model |
| FR-2.8 | The system shall rank routes by a weighted normalization of adjusted ETA, distance, and congestion score, and shall expose the best route as `recommended_route_id`. | Target | P1 | Model |
| FR-2.9 | Each route shall declare its provenance in `data_source`. | Target | P1 | Controller |
| FR-2.10 | The View shall allow selection of any returned route and shall preserve the selection across a re-plan whenever the selected `id` is still present, otherwise falling back to `recommended_route_id`. | Target | P1 | View |
| FR-2.11 | Segment detail shall expand from the leading Routes steps to the full step list of the selected route. | Target | P2 | Model |
| FR-2.12 | Turn-by-turn navigation guidance or live re-routing during a trip. | Out of scope | — | — |
| FR-2.13 | Multimodal, transit, cycling, or walking routing. | Out of scope | — | — |

**Acceptance criteria**

- [ ] A successful Simulated plan returns three routes, each with a non-empty `segments` array and a distinct `objective`.
- [ ] A successful Real-Time plan returns exactly one route.
- [ ] `recommended_route_id` always equals the `id` of a route present in `routes`.
- [ ] The recommended route has the lowest `normalized_score` of the returned set.
- [ ] Re-planning after a scenario change keeps the user's selected route when that route is still returned.

---

## FR-3 Map Rendering And Traffic Visualization

| ID | Requirement | Status | Phase | Owner |
|----|-------------|--------|-------|-------|
| FR-3.1 | All map output shall be rendered by the Google Maps JavaScript API, loaded in the browser through `@vis.gl/react-google-maps`. | Target | P1 | View |
| FR-3.2 | A single map component shall serve both Simulated and Real-Time mode. There shall be exactly one map rendering path in the product. | Target | P1 | View |
| FR-3.3 | Each route shall be drawn with native `google.maps.Polyline` instances created from `route.polyline`. | Target | P1 | View |
| FR-3.4 | Polylines shall be sliced by `traffic_intervals` and colored by the Google speed category of each interval. | Target | P1 | View |
| FR-3.5 | In Simulated mode, non-`NORMAL` slices shall be tinted according to `scenario.congestion` and `scenario.weather`; in Real-Time mode no tint shall be applied. | Target | P1 | View |
| FR-3.6 | The selected route shall be emphasized with greater stroke weight and full opacity relative to unselected routes. | Target | P1 | View |
| FR-3.7 | The map shall fit the selected route's `bounds`, and a "View all" affordance shall fit `map_bounds`. | Target | P1 | View |
| FR-3.8 | The map shall display origin and destination markers with accessible labels. | Target | P2 | View |
| FR-3.9 | Clicking a route polyline shall select that route. | Target | P2 | View |
| FR-3.10 | Server-computed map camera state such as a center point and zoom level. | Out of scope | — | — |
| FR-3.11 | Tilt, rotation, satellite, street-level, or 3D map presentations. | Out of scope | — | — |

**Acceptance criteria**

- [ ] With three routes returned, three sets of polylines are present on one map instance.
- [ ] A route whose `traffic_intervals` array is empty renders as a single `NORMAL`-colored polyline.
- [ ] Changing the selection changes stroke emphasis and refits the camera to the newly selected route.
- [ ] Polyline instances are removed from the map when the plan changes or the component unmounts.
- [ ] A failure to obtain map configuration leaves the route list, analysis panel, and form fully usable.

---

## FR-4 Planning Mode Selection

| ID | Requirement | Status | Phase | Owner |
|----|-------------|--------|-------|-------|
| FR-4.1 | The View shall present a mode switch offering exactly two options labeled `Simulated` and `Real-Time`. | Target | P1 | View |
| FR-4.2 | Changing the mode shall trigger a re-plan without requiring form resubmission. | Target | P1 | View |
| FR-4.3 | The response shall declare whether scenario inputs were applied through `scenario_applied`. | Target | P1 | Controller |
| FR-4.4 | In Real-Time mode the View shall hide the scenario controls rather than render them inert, and shall explain that route comparison is a Simulated-mode capability. | Target | P1 | View |
| FR-4.5 | The response shall carry a mode-specific `notice` string describing where the numbers come from. | Target | P1 | Controller |
| FR-4.6 | Persisting the selected mode across page reloads, or deep-linking a mode and trip. | Out of scope | — | — |

**Acceptance criteria**

- [ ] The mode switch renders exactly two options with the labels `Simulated` and `Real-Time`.
- [ ] Switching mode issues a new `POST /api/plan` with the new `mode` value.
- [ ] A Real-Time response has `scenario_applied` equal to `false`; a Simulated response has `true`.
- [ ] Scenario controls are absent from the accessibility tree in Real-Time mode.
- [ ] `notice` is non-empty for both modes and differs between them.

---

## FR-5 Scenario Controls

| ID | Requirement | Status | Phase | Owner |
|----|-------------|--------|-------|-------|
| FR-5.1 | The View shall provide a departure-hour control over the integer range 0–23 with a 12-hour clock readout. | Target | P1 | View |
| FR-5.2 | The View shall provide a weather-severity control over the integer range 0–3 with the readouts `Clear`, `Light rain`, `Heavy rain`, `Severe`. | Target | P1 | View |
| FR-5.3 | The View shall provide a congestion control over the integer range 0–100 with a percentage readout. | Target | P1 | View |
| FR-5.4 | The View shall provide a reset action restoring `hour` 17, `weather` 1, and `congestion` 56. | Target | P1 | View |
| FR-5.5 | Scenario changes shall be debounced by 180 ms and then trigger one re-plan. | Target | P1 | View |
| FR-5.6 | The Controller shall reject out-of-range scenario values with `422` and code `validation_error`. | Target | P1 | Controller |
| FR-5.7 | The response shall echo the effective scenario actually used in `scenario`. | Target | P1 | Controller |
| FR-5.8 | Named or saved scenario presets. | Out of scope | — | — |
| FR-5.9 | A customer-demand scenario variable. | Out of scope | — | — |
| FR-5.10 | Vehicle, driver, or incentive profile variables. | Out of scope | — | — |

**Acceptance criteria**

- [ ] The scenario control set contains exactly three controls.
- [ ] Dragging a slider across several values issues exactly one `POST /api/plan` after the debounce settles.
- [ ] `weather` equal to 99 returns `422` with `code` equal to `validation_error` and a `fields` array naming `weather`.
- [ ] Reset restores the documented defaults and triggers one re-plan.
- [ ] A Simulated response echoes back the submitted `hour`, `weather`, and `congestion`.

---

## FR-6 Price Estimation

| ID | Requirement | Status | Phase | Owner |
|----|-------------|--------|-------|-------|
| FR-6.1 | Each route shall carry an `estimated_price` in US dollars rounded to two decimal places. | Target | P1 | Model |
| FR-6.2 | Each route shall carry a `price_factors` breakdown containing `route_subtotal`, `traffic_multiplier`, `weather_multiplier`, `time_multiplier`, and `unrounded_total`, all always present. | Target | P1 | Model |
| FR-6.3 | The estimate shall never fall below the configured minimum fare. | Target | P1 | Model |
| FR-6.4 | Applying `price_factors` to `route_subtotal` shall reproduce `unrounded_total`, and `estimated_price` shall equal `unrounded_total` rounded to two decimals. | Target | P1 | Model |
| FR-6.5 | The View shall display a persistent statement that the estimate is illustrative and is not an official Uber or Lyft fare. | Target | P1 | View |
| FR-6.6 | Real rideshare fare quotation, surge pricing feeds, or payment processing. | Out of scope | — | — |
| FR-6.7 | Driver earnings, expense, or profitability projections. | Out of scope | — | — |

**Acceptance criteria**

- [ ] Every route in every successful response has all five `price_factors` fields present and numeric.
- [ ] Recomputing `route_subtotal * traffic_multiplier * weather_multiplier * time_multiplier` reproduces `unrounded_total` within floating-point tolerance.
- [ ] A very short trip returns the configured minimum fare rather than a lower computed total.
- [ ] The disclaimer text is present in the rendered price panel in both modes.

---

## FR-7 Error Handling And Degraded Operation

| ID | Requirement | Status | Phase | Owner |
|----|-------------|--------|-------|-------|
| FR-7.1 | Every non-2xx response from every endpoint shall use the body shape `{ "detail": string, "code": string }`. | Target | P1 | Controller |
| FR-7.2 | The Controller shall map each failure class to exactly one code and status: `validation_error` 422, `invalid_location` 400, `same_origin_destination` 400, `no_route_found` 400, `maps_not_configured` 503, `upstream_unavailable` 502, `upstream_timeout` 504. | Target | P1 | Controller |
| FR-7.3 | The View shall display `detail` to the user and shall choose its presentation and guidance text from `code`. | Target | P1 | View |
| FR-7.4 | A failed plan shall preserve the form inputs, the scenario, and the previously rendered plan. | Target | P1 | View |
| FR-7.5 | A failure to load map configuration shall be contained to the map region; every other panel shall remain usable. | Target | P1 | View |
| FR-7.6 | A denied or unavailable geolocation permission shall produce an actionable message and shall leave manual origin entry working. | Target | P1 | View |
| FR-7.7 | A transport-level fetch failure shall produce a distinct connectivity message rather than a generic failure. | Target | P1 | View |
| FR-7.8 | Upstream timeouts shall be surfaced as retryable with explicit retry guidance. | Target | P1 | View |
| FR-7.9 | Error responses shall never contain stack traces, credentials, or unsanitized upstream response bodies. | Target | P1 | Controller |
| FR-7.10 | Automatic retry with jittered backoff for `upstream_timeout` and `upstream_unavailable`. | Target | P2 | View |
| FR-7.11 | Offline operation or replaying a cached plan without network access. | Out of scope | — | — |
| FR-7.12 | A local geocoding or routing fallback that answers when Google is unavailable. | Out of scope | — | — |

**Acceptance criteria**

- [ ] Each of the seven documented codes is produced by at least one deterministic test.
- [ ] A `422` body contains `detail`, `code`, and `fields`, and `detail` is a string rather than a list.
- [ ] After a failed plan, the origin, destination, mode, scenario, and previous route list are unchanged.
- [ ] No error body contains the substring `Traceback` or any credential value.
- [ ] With map configuration unavailable, route selection and the segment table still respond to input.

---

## FR-8 Congestion Heatmap

Roadmap only. Nothing in FR-8 exists in P1 or P2. The `app/heatmap/` package in the reference
implementation is not wired to any endpoint or view and is not a P1 deliverable.

| ID | Requirement | Status | Phase | Owner |
|----|-------------|--------|-------|-------|
| FR-8.1 | `POST /api/heatmap` shall return congestion intensity cells for a submitted scenario. | Target | P3 | Controller |
| FR-8.2 | The View shall render heatmap cells as a geographic overlay layer on the existing Google Maps JavaScript API map instance. | Target | P3 | View |
| FR-8.3 | The View shall render a legend describing the intensity scale. | Target | P3 | View |
| FR-8.4 | The user shall be able to turn the overlay on and off without losing the current plan. | Target | P3 | View |
| FR-8.5 | A customer-demand heatmap metric. | Out of scope | — | — |
| FR-8.6 | A profitability or earnings heatmap metric. | Out of scope | — | — |

**Acceptance criteria (P3)**

- [ ] `POST /api/heatmap` returns cells whose values respond to `congestion` and `hour`.
- [ ] The overlay renders on the same map instance as the route polylines, not a second map.
- [ ] Toggling the overlay off leaves the plan, selection, and camera unchanged.

---

## Requirement Group Mapping From The Legacy SRS

The source SRS (Rev. 1.0) numbered its groups differently. This table exists so legacy notes can be
traced forward; it is not a statement of current behavior.

| Legacy group | Legacy subject | PROJECT2 group | Change |
|--------------|----------------|----------------|--------|
| FR-1.x | Enter starting point and destination | FR-1 | Google Places replaces dictionary geocoding; no "current location" alias on the server |
| FR-2.x | Route ETA and road segment statistics | FR-2 | Google Routes supplies geometry and durations |
| FR-3.x | Traffic, demand, and profitability heatmaps | FR-8 | Deferred to P3 and narrowed to a congestion metric |
| FR-4.x | Toggle real-time and simulated scenario | FR-4 | The second mode is named Real-Time, never Reference |
| FR-5.x | Adjust scenario variables | FR-5 | Four variables reduced to three |
| FR-6.x | Estimate upfront price | FR-6 | `factors` renamed `price_factors`; `time_multiplier` always present |
| FR-7.x | Handle missing or invalid data | FR-7 | Single error envelope with a code taxonomy |
| — | — | FR-3 | New group: the Maps JavaScript API rendering contract |
