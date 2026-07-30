# Shared Context — Read Before Any Prompt

Every agent executing a prompt in this folder reads this file first. It carries the rules that apply
to all packages so that individual prompts stay short.

---

## Your Standing Orders

You are building TrafficScope, a browser application for rideshare-style trip planning in Austin,
Texas, from the PROJECT2 specification. The specification is authoritative and complete; you are not
designing the product, you are implementing a design that already exists.

| Rule | Statement |
|------|-----------|
| Specification wins | [../README.md](../README.md) holds the locked contracts. If your prompt, a layer context, or your own judgment disagrees with it, the README wins and the disagreement is a defect to report |
| No invention | Do not add a field, endpoint, mode, scenario variable, coefficient, or dependency that the specification does not name. If something appears missing, stop and report it rather than filling the gap |
| No scope creep | Deliver your package. Do not improve a neighboring package because you noticed something; report it in your handoff |
| Phase discipline | Build only what your prompt's phase covers. P2 and P3 capabilities are not written early, and are never described as existing |
| Evidence over assertion | A behavior is done when a test asserts it. Do not report a package complete on the strength of reading the code |

---

## Where Everything Lives

All application code is under `TrafficSImulation/`. Run every command from that directory. The folder
name has a capital S and a lowercase i-m: `TrafficSImulation`, not "TrafficSimulation".

| Layer | Location | Technology |
|-------|----------|-----------|
| View | `TrafficSImulation/src/` | React 19, TypeScript, Vite, `@vis.gl/react-google-maps` |
| Controller | `TrafficSImulation/main.py`, `TrafficSImulation/app/api/` | FastAPI on Uvicorn, Python 3.13 |
| Model | `TrafficSImulation/app/map/`, `simulation/`, `pricing/`, `weather/`, `heatmap/`, `config/` | Python domain packages |
| Backend tests | `TrafficSImulation/tests/` | pytest |
| Frontend tests | Colocated beside the module under `TrafficSImulation/src/` | Vitest and Testing Library in jsdom |

The target module layout is fixed in [../README.md](../README.md) under "Target module layout". The
backend package set `api`, `map`, `simulation`, `pricing`, `weather`, `heatmap`, `config` is fixed by
repo-root `AGENTS.md` and by NFR-5.4. Flat module paths such as `app/routes.py`, `app/models.py`, or
`app/map_service.py` do not exist in the target design and must never appear in an import.

---

## The Dependency Rules

These come from
[../srs-context/architecture/architecture-overview.md](../srs-context/architecture/architecture-overview.md).
Breaking R1, R2, or R6 is a design defect, not a style preference. Each one is checkable by inspecting
the import graph.

| Rule | Statement |
|------|-----------|
| R1 | The Model never imports the Controller, FastAPI, `main`, or any HTTP type |
| R2 | The Controller never contains a coefficient or a formula |
| R3 | The View never contains a coefficient; it renders server-computed numbers |
| R4 | Only `app/api/mode_policy.py` compares the mode string |
| R5 | Only `app/config/__init__.py` reads environment variables |
| R6 | Only `app/map/places.py`, `app/map/routing.py`, and `app/map/health.py` make outbound Google HTTP calls |
| R7 | Only `src/components/MapConfigProvider.tsx` and the components beneath it touch the Maps JavaScript API |
| R8 | The Model raises domain exceptions; only `app/api/errors.py` converts them to HTTP |

---

## The Non-Negotiables

1. One map rendering path: the Google Maps JavaScript API, for both modes, always. No second map
   technology for any mode, state, or degraded condition. The map-unavailable state is a text banner.
2. The server credential never reaches the browser. The browser receives a separate,
   referrer-restricted credential through `GET /api/map/config`.
3. No substituted data. A missing credential or an unreachable upstream is an explicit error state
   with a documented code, never numbers that look real and are not.
4. Exactly three scenario variables: `hour`, `weather`, `congestion`.
5. Only `app/api/mode_policy.py` inspects the mode string.
6. Only `app/config/__init__.py` holds coefficients and reads the environment.
7. The Model never imports the Controller, FastAPI, or any HTTP type.
8. Heatmaps are phase P3.

---

## Contracts You May Not Change

| Contract | Source |
|----------|--------|
| `POST /api/plan` request and response field sets | [../README.md](../README.md) |
| `GET /api/map/config`, `GET /api/health` response shapes | [../README.md](../README.md) |
| The error envelope and the seven error codes with their statuses | [../README.md](../README.md) |
| Shared value objects: `LatLngPoint`, `RouteBounds`, `TrafficInterval`, `TrafficSpeed`, `Scenario`, `WeatherState`, `PriceFactors`, `RoadSegment`, `RouteOption` | [../README.md](../README.md) |
| Mode wire values `simulated` and `realtime`, and the UI labels `Simulated` and `Real-Time` | [../README.md](../README.md) |
| Every coefficient value | [../srs-context/model/configuration.md](../srs-context/model/configuration.md) |

Adding a response field means changing `app/api/models.py`, `src/types.ts`, the contract test, and
[../srs-context/controller/api-contracts.md](../srs-context/controller/api-contracts.md) in the same
change. If your prompt does not authorize that, you may not add the field.

---

## Style

From repo-root `AGENTS.md`.

| Concern | Convention |
|---------|-----------|
| Python indentation | Four spaces |
| TypeScript and TSX indentation | Two spaces |
| Python naming | `snake_case` modules and functions, `PascalCase` classes |
| TypeScript naming | `PascalCase` components and types, `camelCase` values and callbacks |
| Typing | Strict TypeScript. Request and response shapes are declared in the model or type module, never passed as untyped objects |
| Comments | Only where the code cannot state a constraint itself. Do not narrate what a line does |
| Magic numbers | None. Any coefficient, threshold, timeout, or fixed response string is a named constant in `app/config/__init__.py` |

---

## Commands

Run from `TrafficSImulation/`.

| Goal | Command |
|------|---------|
| Install frontend dependencies | `npm install` |
| Install backend dependencies | `pip install -r requirements.txt` |
| Backend and API tests | `python -m pytest` |
| Frontend tests | `npm test` |
| Type-check and bundle | `npm run build` |
| Development, two terminals | `python main.py` and `npm run dev`, then open `http://127.0.0.1:5173` |
| Production check | `npm run build`, then `python main.py`, then open `http://127.0.0.1:8000` |

Before reporting a package complete, run `python -m pytest`, and also `npm test` and `npm run build`
if the package touched `src/`.

---

## Testing Rules

| Rule | Detail |
|------|--------|
| Test IDs are stable | Reference the ID from [../srs-context/requirements/traceability.md](../srs-context/requirements/traceability.md) in the test's docstring or name so the mapping survives |
| Tests assert literals | A test that reads a coefficient constant still passes when the constant changes, which defeats its purpose. Write the expected value literally |
| No live Google calls | The default suite makes zero outbound Google requests. Gateways are exercised through mocked transports. Any live-credential test is opt-in and excluded from the default run |
| Behavior, not snapshots | React tests assert user-visible behavior with Testing Library. Do not add snapshot assertions |
| Boundary cases | Every domain formula gets a unit test with at least one boundary case |
| Naming | Python tests are `test_<behavior>` in `tests/test_*.py`. Frontend tests are `*.test.ts` or `*.test.tsx` beside the module |

---

## Handoff Report

End every package with a short report containing:

1. What you built, by file.
2. Which test IDs now pass, and the command output that proves it.
3. Any specification defect, ambiguity, or contradiction you found, quoted with its file and line.
4. Anything you deliberately left for a later prompt, with the prompt number.
5. Any dependency you added, and the requirement that justifies it.

Do not report a package complete with a failing test, a skipped test that is not marked opt-in, or an
unticked Definition of Done item.
