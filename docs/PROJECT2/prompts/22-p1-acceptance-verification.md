# Prompt 22 — P1 Acceptance Verification

**Wave:** 4 — Convergence
**Depends on:** prompts 01 through 21
**Phase:** P1
**Read first:** [00-shared-context.md](00-shared-context.md)

## Read First

1. [00-shared-context.md](00-shared-context.md)
2. [../srs-context/architecture/architecture-overview.md](../srs-context/architecture/architecture-overview.md), Acceptance Criteria and Planned Tests
3. [../srs-context/requirements/traceability.md](../srs-context/requirements/traceability.md)
4. [../srs-context/requirements/functional-requirements.md](../srs-context/requirements/functional-requirements.md)
5. [../srs-context/requirements/non-functional-requirements.md](../srs-context/requirements/non-functional-requirements.md)
6. [../README.md](../README.md), Locked Decisions

## Objective

Prove that P1 is done. This package writes production code only to fix defects that verification
exposes. Its primary output is evidence: a green suite, a completed acceptance checklist, and an
updated traceability table.

## Deliverables

| Change | Responsibility |
|--------|----------------|
| Fixes for any P1 defect verification finds | Smallest change that restores a requirement |
| Updated Progress column in `docs/PROJECT2/srs-context/requirements/traceability.md` | Reflect what actually passes |
| A verification report committed beside this prompt or pasted into the PR | Evidence |

## Task

1. Run from `TrafficSImulation/`:
   - `python -m pytest`
   - `npm test`
   - `npm run build`
   - `python main.py` and `npm run dev` for a manual smoke of Simulated plan, Real-Time plan, mode
     switch, scenario debounce, map render, and a deliberate map-config failure.
2. Walk the architecture overview's Acceptance Criteria and tick each item only when a test or a
   recorded manual check supports it:
   - No Model-to-Controller import edge.
   - `app/api/planning.py` contains no numeric coefficient.
   - `GOOGLE_MAPS_API_KEY` appears in no response body produced by the suite.
   - `GET /api/map/config` returns `maps_browser_api_key` and never `maps_api_key`.
   - `google.maps` appears only in the four map components.
   - Only `app/api/mode_policy.py` compares the mode literals (plus the documented schema allowlist).
3. Walk every P1 row in the traceability table. For each Target requirement in phase P1, confirm its
   planned tests exist and pass, then set Progress to the appropriate completed state. Leave P2 and
   P3 rows untouched.
4. Confirm the test catalog's P1 entries T-01 through T-39, T-42, T-43, T-45, T-46, T-49, T-54, T-56
   are present and green. T-57 remains opt-in and deselected. Note any missing ID as a defect and
   either implement the smallest test that closes it or open an explicit follow-up named by ID.
5. Confirm the locked decisions still hold: two modes, three scenario variables, four endpoints with
   only three active in P1, one map path, two credentials, no `demand`.
6. Fix any defect you find with the smallest change that restores the requirement. If a fix expands
   beyond a few files, stop and report it rather than absorbing a new package into verification.
7. Produce a verification report listing: commands run and results, acceptance criteria ticks,
   traceability rows updated, defects fixed, defects deferred with IDs, and the manual smoke
   observations.

## Boundaries

- Do not start P2 or P3 work.
- Do not mark a traceability row complete without a passing planned test.
- Do not weaken a test to obtain a green suite.
- Do not add a feature that is not required to close a failing P1 criterion.

## Tests To Write

Only the missing P1 catalog entries that verification proves absent. Prefer writing the missing test
over rewriting production code. Name each by its catalog ID.

## Definition Of Done

- [ ] `python -m pytest`, `npm test`, and `npm run build` all pass.
- [ ] Every architecture overview acceptance criterion is ticked with evidence.
- [ ] Every P1 Target row in the traceability table has Progress reflecting a passing planned test.
- [ ] T-01 through T-39, T-42, T-43, T-45, T-46, T-49, T-54, and T-56 are green; T-57 is opt-in only.
- [ ] Manual smoke of Simulated, Real-Time, mode switch, scenario debounce, map render, and map failure is recorded.
- [ ] The verification report exists and is attached to the handoff.
- [ ] No P2 or P3 behavior was introduced.

## Handoff

Attach the verification report. Call out any P1 requirement that cannot be closed and the reason, so
prompt 23 does not mistake it for P2 scope.
