# Prompt 14 — Plan And Map Config Hooks

**Wave:** 3 — View
**Depends on:** prompts 13
**Phase:** P1
**Read first:** [00-shared-context.md](00-shared-context.md)

## Read First

1. [00-shared-context.md](00-shared-context.md)
2. [../srs-context/view/app-composition.md](../srs-context/view/app-composition.md)
3. [../srs-context/architecture/state-diagrams.md](../srs-context/architecture/state-diagrams.md), the plan lifecycle and client request states
4. [../srs-context/architecture/class-diagram.md](../srs-context/architecture/class-diagram.md), `useRoutePlan` and `useMapConfig`
5. [../srs-context/view/loading-error-states.md](../srs-context/view/loading-error-states.md)

## Objective

Own the View's request lifecycle. `useRoutePlan` holds trip inputs, mode, scenario, the plan, the
selection, and the request state. `useMapConfig` fetches and caches map configuration independently,
so a map failure and a plan failure degrade separately.

## Deliverables

| File | Responsibility |
|------|----------------|
| `TrafficSImulation/src/hooks/useRoutePlan.ts` | Trip inputs, mode, scenario, request lifecycle, route selection |
| `TrafficSImulation/src/hooks/useMapConfig.ts` | Retrieve and cache `GET /api/map/config` |
| `TrafficSImulation/src/hooks/useRoutePlan.test.ts` | T-27 and selection reconciliation coverage |
| Colocated `useMapConfig` tests | Config success, failure, and caching |

## Task

1. Implement `useRoutePlan` with the public surface from the class diagram: `origin`, `destination`,
   `mode`, `scenario`, `plan`, `selectedRouteId`, `status`, `error`, `submit`, `setMode`,
   `setScenario`, `resetScenario`, `selectRoute`.
2. Request lifecycle:
   - Origin and destination changes require an explicit `submit`. They do not auto-plan.
   - Scenario changes are debounced at 180 ms and coalesce into one request (FR-5.5, NFR-1.5).
   - A mode change issues a new plan request.
   - Superseded in-flight requests are aborted through `AbortSignal` and their responses discarded.
   - `status` moves through `idle | loading | success | error` as the state diagrams specify.
3. Selection:
   - `selectRoute` updates `selectedRouteId`.
   - Across a re-plan, preserve the selection when the id remains in the new `routes`; otherwise fall
     back to `recommended_route_id` (FR-2.10).
4. Failure:
   - On error, preserve the previous successful `plan` and the user's inputs (FR-7.4).
   - Surface the parsed `ApiError` so presentation can branch on `code`.
5. Implement `useMapConfig`:
   - Fetch once, cache the result for the session.
   - Expose `config`, `status`, and `error`.
   - A failure is local to the map configuration flow and does not affect the plan hook.
6. Neither hook imports a coefficient, performs fare or ETA arithmetic, or touches the Maps JavaScript
   API. Both call `src/api/client.ts` only.
7. Write T-27: rapid scenario changes coalesce into one request; a superseded request is aborted and
   its late response is discarded. Write selection reconciliation coverage for the preserve-or-fallback
   rule. Write map-config tests for success, `maps_not_configured`, and cache reuse.

## Boundaries

- No `fetch` call outside the client.
- No coefficient and no domain arithmetic (R3).
- No Maps JavaScript API (R7).
- Do not decide mode policy. Read `plan.mode` and `plan.scenario_applied` from the response when a
  consumer needs to know what happened; do not re-derive policy from the request intent.
- Do not put presentation markup in a hook.

## Tests To Write

| Test ID | Level | Target file | Assertion |
|---------|-------|-------------|-----------|
| T-27 | component | `src/hooks/useRoutePlan.test.ts` | Debounce coalescing and abort of superseded requests |
| Selection coverage | component | `src/hooks/useRoutePlan.test.ts` | Selection preserved across re-plan when id remains; otherwise falls back to recommended |
| Map-config coverage | component | `src/hooks/useMapConfig.test.ts` | Success, failure contained, cache reuse |

## Definition Of Done

- [ ] Origin and destination require explicit submit; scenario changes debounce at 180 ms.
- [ ] Mode change issues a new plan request.
- [ ] Superseded requests are aborted and discarded.
- [ ] Selection reconciles across a re-plan as specified.
- [ ] A plan failure preserves inputs and the previous plan.
- [ ] Map configuration failure is independent of the plan hook.
- [ ] Neither hook imports a coefficient or the Maps JavaScript API.
- [ ] T-27 and the colocated coverage pass.
- [ ] `npm test` and `npm run build` pass.

## Handoff

Report the public hook surfaces, the debounce interval constant's location, and any state-diagram
transition that the documents left underspecified.
