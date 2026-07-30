# Prompt 18 — Status And Notice Presentation

**Wave:** 3 — View
**Depends on:** prompts 13, 14
**Phase:** P1
**Read first:** [00-shared-context.md](00-shared-context.md)

## Read First

1. [00-shared-context.md](00-shared-context.md)
2. [../srs-context/view/loading-error-states.md](../srs-context/view/loading-error-states.md)
3. [../README.md](../README.md), the error envelope and the seven error codes
4. [../srs-context/view/accessibility.md](../srs-context/view/accessibility.md), live-region requirements

## Objective

Build the loading, empty, error, and degraded presentation so that every failure class the API can
produce has a clear, code-branched UI treatment, and so that transient notices can be dismissed
without erasing the plan.

## Deliverables

| File | Responsibility |
|------|----------------|
| `TrafficSImulation/src/components/StatusBanner.tsx` | Loading, empty, error, and map-unavailable states |
| `TrafficSImulation/src/components/Toast.tsx` | Transient dismissible notices |
| Colocated tests | T-30 and toast coverage |

## Task

1. Implement `StatusBanner` to present:
   - loading while a plan request is in flight;
   - empty when there is no plan yet;
   - error states branched on `ApiError.code`, showing `detail` and any code-specific guidance
     (for example, retry guidance for `upstream_timeout`);
   - the map-unavailable state when map configuration failed, scoped to the map region.
2. Branch on `code`, never on message text (FR-7.3). Cover every code in the README table with a
   distinct presentation or a shared presentation that still surfaces the `detail`.
3. On a plan failure, keep the previous plan visible and leave the user's inputs editable (FR-7.4).
   The banner reports the failure; it does not clear the page.
4. A transport failure with no error envelope shows a connectivity message (FR-7.7).
5. Implement `Toast` for transient dismissible notices such as geolocation denial. Toasts do not
   replace the banner for plan failures.
6. Announce status and errors through a polite aria-live region (NFR-4.4). Do not use an assertive
   live region for routine loading.
7. Write T-30 covering error presentation by `code`, input and plan preservation, and the
   connectivity fallback. Write toast coverage for dismiss behavior.

## Boundaries

- No domain arithmetic.
- No Maps JavaScript API.
- Do not invent an error code. If the API returns an unknown code, show `detail` with a generic
  fallback rather than inventing a new contract.
- Do not auto-retry from the View. Retry is a user action or a P2 server concern.

## Tests To Write

| Test ID | Level | Target file | Assertion |
|---------|-------|-------------|-----------|
| T-30 | component | `src/components/StatusBanner.test.tsx` | Error presentation by `code`, input and plan preservation, connectivity fallback |
| Toast coverage | component | `src/components/Toast.test.tsx` | Renders, announces, and dismisses |

## Definition Of Done

- [ ] Every documented error code has a presentation path that surfaces `detail`.
- [ ] Presentation branches on `code`, never on message text.
- [ ] A plan failure preserves inputs and the previous plan.
- [ ] Map-unavailable is contained to the map region.
- [ ] Status and errors announce through a polite live region.
- [ ] T-30 and toast coverage pass.
- [ ] `npm test` and `npm run build` pass.

## Handoff

Report the code-to-presentation table you implemented, the connectivity copy, and any
loading-error-states sentence that left a code's guidance underspecified.
