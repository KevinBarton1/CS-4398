# Prompt 16 — Forms And Scenario Controls

**Wave:** 3 — View
**Depends on:** prompts 13, 14
**Phase:** P1
**Read first:** [00-shared-context.md](00-shared-context.md)

## Read First

1. [00-shared-context.md](00-shared-context.md)
2. [../srs-context/view/route-scenario-forms.md](../srs-context/view/route-scenario-forms.md)
3. [../README.md](../README.md), sections "Planning modes" and "Scenario variables"
4. [../srs-context/view/accessibility.md](../srs-context/view/accessibility.md), the form-related criteria

## Objective

Build the trip form and the three scenario controls. The form captures origin, destination, and an
optional geolocation assist. The scenario controls expose exactly `hour`, `weather`, and
`congestion`, and are absent in Real-Time mode.

## Deliverables

| File | Responsibility |
|------|----------------|
| `TrafficSImulation/src/components/RoutePlannerForm.tsx` | Origin, destination, geolocation assist, submit |
| `TrafficSImulation/src/components/ScenarioControls.tsx` | The three scenario controls and reset |
| Colocated tests | T-26, T-35 |

## Task

1. Implement `RoutePlannerForm`:
   - Labeled origin and destination inputs, each accepting 1–120 characters of free text.
   - Defaults suitable for an Austin demo trip, matching whatever the app-composition document
     specifies; if it specifies none, use empty strings and let the user type.
   - A submit control that calls `useRoutePlan`'s `submit`.
   - A geolocation assist that, on granted permission, fills the origin with `lat, lng` text
     (FR-1.3). On denial, show a notice and leave manual entry working (FR-7.6). The browser sends
     resolved coordinates as text; there is no server-side "current location" alias.
2. Implement `ScenarioControls`:
   - Hour control spanning 0–23 with a 12-hour readout.
   - Weather control spanning 0–3 with the locked labels Clear, Light rain, Heavy rain, Severe.
   - Congestion control spanning 0–100 with a percentage readout.
   - Reset restores `DEFAULT_HOUR`, `DEFAULT_WEATHER`, and `DEFAULT_CONGESTION`.
   - Changes flow through `setScenario` so the hook's debounce coalesces them.
3. Render `ScenarioControls` only when the active plan reports `scenario_applied` true, or when the
   current mode is Simulated before the first response. In Real-Time mode the controls are absent, not
   disabled-and-visible, and an explanation of why is available per NFR-7.5.
4. Do not introduce a fourth scenario variable under any name. `demand` is out of scope.
5. Every control is keyboard operable with a visible focus state. Labels are programmatic, not
   placeholder-only.
6. Write T-26 for slider ranges, readouts, and reset. Write T-35 for geolocation grant and denial.

## Boundaries

- No coefficient and no domain arithmetic.
- No Maps JavaScript API.
- No mode-policy logic beyond reading `mode` / `scenario_applied` to decide whether to render the
  controls.
- Do not call the API client directly; go through the hooks.
- Do not add autocomplete against Places from the browser. Place resolution is server-side only.

## Tests To Write

| Test ID | Level | Target file | Assertion |
|---------|-------|-------------|-----------|
| T-26 | component | `src/components/ScenarioControls.test.tsx` | Slider ranges, readouts, reset, and defaults 17 / 1 / 56 |
| T-35 | component | `src/components/RoutePlannerForm.test.tsx` | Geolocation grant fills `lat, lng` text; denial shows a notice and leaves entry working |

## Definition Of Done

- [ ] Origin and destination are labeled and submittable.
- [ ] Geolocation grant and denial paths both work.
- [ ] Scenario controls expose exactly hour, weather, and congestion with the documented ranges and labels.
- [ ] Reset restores the three defaults.
- [ ] Scenario controls are absent in Real-Time mode.
- [ ] No fourth scenario variable exists.
- [ ] Controls are keyboard operable with visible focus.
- [ ] T-26 and T-35 pass.
- [ ] `npm test` and `npm run build` pass.

## Handoff

Report the component props, the default origin and destination strings you chose if any, and any
form-document sentence that disagreed with the locked scenario table.
