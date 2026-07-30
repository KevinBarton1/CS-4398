# Build Prompts — TrafficScope PROJECT2

**Purpose:** An ordered, executable set of agent prompts that build the application described by
[../srs-context/architecture/architecture-overview.md](../srs-context/architecture/architecture-overview.md).
Each numbered file is one self-contained work package: hand it to an agent, and it produces the files,
tests, and verification for one slice of the architecture.

**Status:** These prompts describe work to be done. They add no requirement and no contract. Where a
prompt appears to disagree with [../README.md](../README.md), the README wins and the prompt is a
defect.

---

## How To Use This Folder

1. Read [00-shared-context.md](00-shared-context.md). Every agent reads it before its own prompt; it
   carries the layer rules, style conventions, and commands that apply to every package.
2. Execute prompts in ascending order. A prompt may only start when everything in its
   **Depends on** line is done.
3. Give an agent exactly one prompt at a time. The prompts are sized so that one agent, one branch,
   and one review can carry a whole package.
4. Finish a package before starting the next: its own tests pass, `python -m pytest` passes,
   `npm test` and `npm run build` pass if it touched the View, and its Definition of Done checklist is
   fully ticked.
5. Update the `Progress` column of
   [../srs-context/requirements/traceability.md](../srs-context/requirements/traceability.md) for the
   rows a package completes. A row is only complete when its planned tests pass.

Prompts inside one wave that list the same dependencies can run in parallel on separate branches;
prompts across waves cannot.

---

## Waves And Order

### Wave 0 — Foundation

| # | Prompt | Produces |
|---|--------|----------|
| 01 | [01-workspace-baseline-and-toolchain.md](01-workspace-baseline-and-toolchain.md) | Package skeleton, dependency manifests, test harness, environment contract |
| 02 | [02-configuration-and-coefficients.md](02-configuration-and-coefficients.md) | `app/config/__init__.py`, the whole coefficient catalog, `tests/test_config.py` |

### Wave 1 — Model

| # | Prompt | Produces |
|---|--------|----------|
| 03 | [03-geospatial-types-and-geometry.md](03-geospatial-types-and-geometry.md) | `app/map/types.py`, `polyline.py`, `bounds.py` |
| 04 | [04-google-gateways-and-probe.md](04-google-gateways-and-probe.md) | `app/map/places.py`, `routing.py`, `health.py` |
| 05 | [05-traffic-physics-and-segments.md](05-traffic-physics-and-segments.md) | `app/simulation/traffic.py`, `segments.py` |
| 06 | [06-weather-and-pricing.md](06-weather-and-pricing.md) | `app/weather/service.py`, `app/pricing/model.py` |
| 07 | [07-route-scoring.md](07-route-scoring.md) | `app/simulation/scoring.py` |

Prompts 03 through 07 depend only on Wave 0. 04 additionally depends on 03.

### Wave 2 — Controller

| # | Prompt | Produces |
|---|--------|----------|
| 08 | [08-api-schemas-and-error-envelope.md](08-api-schemas-and-error-envelope.md) | `app/api/models.py`, `app/api/errors.py` |
| 09 | [09-mode-policies.md](09-mode-policies.md) | `app/api/mode_policy.py` |
| 10 | [10-planning-orchestration.md](10-planning-orchestration.md) | `app/api/planning.py`, `app/api/dependencies.py` |
| 11 | [11-http-surface-and-app-assembly.md](11-http-surface-and-app-assembly.md) | `app/api/routes.py`, `main.py`, the API test suite |
| 12 | [12-contract-and-architecture-tests.md](12-contract-and-architecture-tests.md) | `tests/test_contracts.py`, `tests/test_architecture.py` |

### Wave 3 — View

| # | Prompt | Produces |
|---|--------|----------|
| 13 | [13-frontend-types-client-and-constants.md](13-frontend-types-client-and-constants.md) | `src/types.ts`, `src/api/client.ts`, `src/constants/scenario.ts`, `src/utils/format.ts` |
| 14 | [14-plan-and-map-config-hooks.md](14-plan-and-map-config-hooks.md) | `src/hooks/useRoutePlan.ts`, `src/hooks/useMapConfig.ts` |
| 15 | [15-map-rendering-path.md](15-map-rendering-path.md) | The four map components and `src/utils/trafficSegmentColor.ts` |
| 16 | [16-forms-and-scenario-controls.md](16-forms-and-scenario-controls.md) | `src/components/RoutePlannerForm.tsx`, `ScenarioControls.tsx` |
| 17 | [17-results-and-analysis-panels.md](17-results-and-analysis-panels.md) | `RouteOptionList.tsx`, `AnalysisPanel.tsx`, `PriceSummary.tsx`, `SegmentTable.tsx` |
| 18 | [18-status-and-notice-presentation.md](18-status-and-notice-presentation.md) | `StatusBanner.tsx`, `Toast.tsx` |
| 19 | [19-app-composition-and-styles.md](19-app-composition-and-styles.md) | `src/App.tsx`, `src/main.tsx`, `AppHeader.tsx`, `src/styles.css` |
| 20 | [20-accessibility-conformance.md](20-accessibility-conformance.md) | Accessibility hardening across the View |

Prompts 15 through 18 depend on 13 and 14 and can run in parallel. 19 depends on all of them. 20
depends on 19.

### Wave 4 — Convergence

| # | Prompt | Produces |
|---|--------|----------|
| 21 | [21-superseded-code-decommission.md](21-superseded-code-decommission.md) | Removal of everything the rewrite replaced |
| 22 | [22-p1-acceptance-verification.md](22-p1-acceptance-verification.md) | A verified P1, with traceability updated |

### Wave 5 — Later phases

| # | Prompt | Produces |
|---|--------|----------|
| 23 | [23-p2-depth-and-resilience.md](23-p2-depth-and-resilience.md) | P2 scope: caching, retry, richer segments, expanded tests |
| 24 | [24-p3-congestion-heatmap.md](24-p3-congestion-heatmap.md) | P3 scope: `POST /api/heatmap` and the overlay layer |

Do not start Wave 5 until [22-p1-acceptance-verification.md](22-p1-acceptance-verification.md)
reports a clean P1.

---

## Coverage Of The Architecture

Every component named in
[../srs-context/architecture/architecture-overview.md](../srs-context/architecture/architecture-overview.md)
is owned by exactly one prompt.

| Architecture section | Owning prompts |
|----------------------|----------------|
| Containers and toolchain | 01 |
| Model components | 02, 03, 04, 05, 06, 07 |
| Controller components | 08, 09, 10, 11 |
| View components | 13, 14, 15, 16, 17, 18, 19 |
| Dependency rules R1 through R8 | 12 enforces; every prompt obeys |
| Request and data flow | 10, 11, 14 |
| Trust boundaries and credentials | 02, 04, 11, 15 |
| Deployment assumptions | 01, 11 |
| Acceptance criteria and planned tests | 12, 22 |

---

## Prompt File Shape

Each prompt carries the same sections, so an agent always knows where to look.

| Section | Contents |
|---------|----------|
| Header | Wave, dependencies, phase |
| Read First | The documents that govern the package, in reading order |
| Deliverables | Every file the package creates or changes, with its responsibility |
| Task | Ordered, concrete instructions |
| Boundaries | What the package must not do, expressed as the dependency rules it can break |
| Tests To Write | Test IDs from the catalog, with target file and assertion |
| Definition Of Done | A checklist that must be fully ticked before handoff |
| Handoff | What to report to the next agent |

---

## Global Definition Of Done

No package is done until all of these hold.

- [ ] Every file in the Deliverables table exists at its stated path with its stated responsibility.
- [ ] Every test in the Tests To Write table exists, is named for the behavior it checks, and passes.
- [ ] `python -m pytest` passes from `TrafficSImulation/`.
- [ ] `npm test` and `npm run build` pass from `TrafficSImulation/` if the package touched `src/`.
- [ ] The package introduced no coefficient, credential, or mode comparison outside its permitted home.
- [ ] No contract field was added, renamed, or removed without the matching change in
      `app/api/models.py`, `src/types.ts`, the contract test, and
      [../srs-context/controller/api-contracts.md](../srs-context/controller/api-contracts.md).
- [ ] The `Progress` column in
      [../srs-context/requirements/traceability.md](../srs-context/requirements/traceability.md) reflects
      what actually passes.
