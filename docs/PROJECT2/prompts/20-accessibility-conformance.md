# Prompt 20 — Accessibility Conformance

**Wave:** 3 — View
**Depends on:** prompt 19
**Phase:** P1
**Read first:** [00-shared-context.md](00-shared-context.md)

## Read First

1. [00-shared-context.md](00-shared-context.md)
2. [../srs-context/view/accessibility.md](../srs-context/view/accessibility.md) — read all of it
3. [../srs-context/requirements/non-functional-requirements.md](../srs-context/requirements/non-functional-requirements.md), NFR-4.*
4. [../srs-context/view/loading-error-states.md](../srs-context/view/loading-error-states.md)
5. [../srs-context/view/results-analysis.md](../srs-context/view/results-analysis.md)

## Objective

Harden the composed View so that every P1 accessibility requirement is met: keyboard operation,
semantics, live regions, contrast, and non-visual parity with the map. This package changes existing
components; it does not add a parallel interface.

## Deliverables

| File | Responsibility |
|------|----------------|
| Updates across View components and `styles.css` | Keyboard, semantics, focus, contrast, live regions, textual severity |
| Hardened tests | T-36, T-37, T-39 (textual severity if not already complete), and any contrast assertions that can be automated |

## Task

1. Confirm every interactive control is reachable and operable by keyboard alone, with a visible focus
   indicator that meets the contrast target (NFR-4.2).
2. Confirm programmatic labels on every input, and roles or headings that make the mode switch, route
   list, analysis panel, and map region structurally clear.
3. Confirm status and errors announce through a polite aria-live region without announcing routine
   keystrokes (NFR-4.4). Strengthen T-37 until it fails when the live region is removed.
4. Confirm map information is duplicated in text: route list, ETAs, segment table, and textual
   traffic severity so a user who cannot see the map still gets the same facts (NFR-4.3, NFR-4.6).
5. Confirm text contrast is at least 4.5:1 for body text and interactive labels (NFR-4.5). Fix any
   style that fails. Where an automated check is practical in jsdom or via a small script, add it;
   otherwise record a manual contrast review in the handoff and leave the P2 automated audit (T-55)
   for prompt 23.
6. Do not rely on color alone for traffic severity or recommendation. Pair color with text.
7. Leave reduced-motion handling and the full automated audit for P2 (NFR-4.7, NFR-4.8) unless a
   change is trivial and already required to pass a P1 criterion; note what you deferred.

## Boundaries

- Do not add a second interface, a high-contrast theme toggle, or a screen-reader-only mode that
  hides the visual UI.
- Do not weaken visual design below the contrast floor to avoid work; fix the color.
- Do not introduce an accessibility library that rewrites the DOM in ways the tests cannot see.

## Tests To Write

| Test ID | Level | Target file | Assertion |
|---------|-------|-------------|-----------|
| T-36 | component | `src/App.test.tsx` | Keyboard traversal of the mode switch and route cards |
| T-37 | component | `src/App.test.tsx` | Live-region announcements for loading and error |
| T-39 (completion) | component | `src/components/SegmentTable.test.tsx` | Textual severity alongside any color cue |

## Definition Of Done

- [ ] Every interactive control is keyboard operable with visible focus.
- [ ] Status and errors announce through a polite live region, proven by T-37.
- [ ] Map facts are duplicated in text.
- [ ] Traffic severity and recommendation are not color-only.
- [ ] Text contrast meets 4.5:1 for body text and interactive labels, with evidence in the handoff.
- [ ] T-36 and T-37 pass.
- [ ] `npm test` and `npm run build` pass.

## Handoff

Report the accessibility fixes by component, the contrast evidence (tool or manual method), and the
P2 items you deferred with their NFR IDs.
