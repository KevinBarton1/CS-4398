# Prompt 01 — Workspace Baseline And Toolchain

**Wave:** 0 — Foundation
**Depends on:** nothing
**Phase:** P1
**Read first:** [00-shared-context.md](00-shared-context.md)

## Read First

1. [00-shared-context.md](00-shared-context.md)
2. [../README.md](../README.md), sections "Target module layout" and "Endpoints"
3. [../agent-quickstart.md](../agent-quickstart.md), sections "Run And Test" and "Configuration And Environment"
4. [../srs-context/architecture/architecture-overview.md](../srs-context/architecture/architecture-overview.md), sections "Containers" and "Deployment Assumptions"
5. [../srs-context/model/configuration.md](../srs-context/model/configuration.md), section "`.env` Contract"
6. Repo-root `AGENTS.md`

## Objective

Put the target skeleton and the toolchain in place so that every later package has somewhere to write
and something to run. This package creates structure and configuration only. It implements no domain
behavior, no endpoint, and no component.

## Deliverables

| File | Responsibility |
|------|----------------|
| `TrafficSImulation/requirements.txt` | The backend dependency set, pinned by compatible range |
| `TrafficSImulation/package.json` | Frontend dependencies and the `dev`, `build`, `preview`, `test` scripts |
| `TrafficSImulation/pytest.ini` or the `[tool.pytest.ini_options]` table of `pyproject.toml` | Test discovery, async test mode, and the marker that excludes opt-in live-credential tests from the default run |
| `TrafficSImulation/vite.config.ts` | Dev server on `127.0.0.1:5173`, `/api` proxied to `http://127.0.0.1:8000`, React plugin, `dist/` build output |
| `TrafficSImulation/vitest.config.ts` | jsdom environment, global setup file, colocated test discovery under `src/` |
| `TrafficSImulation/tsconfig.json`, `tsconfig.app.json`, `tsconfig.node.json` | Strict TypeScript for the app and the tooling |
| `TrafficSImulation/src/test-setup.ts` | Testing Library and jest-dom registration |
| `TrafficSImulation/index.html` | The single-page application host document |
| `TrafficSImulation/.env.example` | The three environment variable names with empty values |
| `TrafficSImulation/.gitignore` coverage for `.env` | The real `.env` is never committed |
| `TrafficSImulation/app/**/__init__.py` | The fixed package set exists and is importable |
| `TrafficSImulation/tests/__init__.py` and `tests/conftest.py` | Shared fixture home for later packages |
| `TrafficSImulation/README.md` | How to install, run, test, and configure credentials |

## Task

1. Create the backend package tree exactly as listed under "Target module layout" in
   [../README.md](../README.md): `app/api/`, `app/map/`, `app/simulation/`, `app/pricing/`,
   `app/weather/`, `app/heatmap/`, `app/config/`, each with an `__init__.py`. Leave the module files
   for their owning prompts; do not stub them with placeholder classes.
2. Create `src/` subdirectories `api/`, `hooks/`, `constants/`, `utils/`, `components/`. Leave the
   modules for Wave 3.
3. Create `tests/` with `__init__.py` and an empty-but-valid `conftest.py`.
4. Write `requirements.txt`. The set must support what the specification requires and nothing more:
   FastAPI, Uvicorn, Pydantic v2, `pydantic-settings` because `Settings` extends `BaseSettings`,
   `python-dotenv` for loading `TrafficSImulation/.env` at import, `httpx` as the single outbound
   transport and the FastAPI test client transport, `pytest`, and the async plugin needed to run
   `async def` tests. Justify every entry in your handoff against a requirement.
5. Write `package.json`. Keep React 19, TypeScript, Vite, `@vis.gl/react-google-maps`,
   `@types/google.maps`, Vitest, jsdom, and Testing Library with jest-dom. Do not add a second map
   library, a state-management library, a component library, or a CSS framework. Scripts are `dev`,
   `build` as `tsc -b && vite build`, `preview`, and `test` as `vitest run`.
6. Configure Vite: the React plugin, `server.host` `127.0.0.1`, `server.port` `5173`, and a
   `server.proxy` entry sending `/api` to `http://127.0.0.1:8000`. Build output goes to `dist/`,
   because in production the application service serves the built single-page application from there.
7. Configure Vitest: `environment: "jsdom"`, `setupFiles` pointing at `src/test-setup.ts`, and globals
   enabled or explicitly imported, consistently across the suite.
8. Configure TypeScript in strict mode. `strict`, `noUnusedLocals`, `noUnusedParameters`, and
   `noFallthroughCasesInSwitch` are on. `npm run build` must type-check and must be able to gate a
   merge, per NFR-6.6.
9. Configure pytest: `testpaths` is `tests`, async tests run without per-test decoration boilerplate,
   and a marker such as `live` is registered and deselected by default so an opt-in live-credential
   test cannot run in the default suite (NFR-6.9).
10. Write `.env.example` with `GOOGLE_MAPS_API_KEY=`, `GOOGLE_MAPS_BROWSER_API_KEY=`, and
    `GOOGLE_MAPS_MAP_ID=`, and no values. Confirm `.env` is ignored by git.
11. Write `TrafficSImulation/README.md`: install, run both processes, run both test suites, build for
    production, and set the two credentials with their Google console restrictions. State that a
    working server credential is a hard dependency for planning and that there is no offline path.
12. Verify the skeleton: `pip install -r requirements.txt`, `npm install`, `python -m pytest`
    collecting zero tests without error, and `npm run build` succeeding on an empty entry point or
    failing only for the deliberately absent Wave 3 modules. Record exactly which of these you ran and
    what they reported.

## Boundaries

- Write no domain logic, no endpoint, no React component. A later prompt owns each of those.
- Do not create placeholder modules that a later prompt must delete. Empty packages, yes; stub classes,
  no.
- Do not add a dependency the specification does not require. Every entry needs a named justification.
- Do not read an environment variable anywhere in this package. `app/config/__init__.py` in prompt 02
  is the only reader (R5).
- Do not modify or delete the code that currently exists under `TrafficSImulation/` beyond the
  configuration files listed above. Prompt 21 owns removal.

## Tests To Write

None. This package is verified by the toolchain running, not by assertions.

## Definition Of Done

- [ ] Every directory in the target module layout exists and every backend package imports cleanly.
- [ ] `pip install -r requirements.txt` succeeds and every entry has a stated justification.
- [ ] `npm install` succeeds with no map library other than `@vis.gl/react-google-maps`.
- [ ] `python -m pytest` runs, collects cleanly, and deselects the opt-in live marker by default.
- [ ] `npm run build` type-checks with the strict settings in place.
- [ ] Vite serves on `127.0.0.1:5173` and proxies `/api` to `http://127.0.0.1:8000`.
- [ ] `.env.example` lists exactly the three documented variables with empty values, and `.env` is git-ignored.
- [ ] `TrafficSImulation/README.md` documents install, run, test, build, and both credentials.
- [ ] No environment variable is read outside `app/config/__init__.py`, which does not exist yet.

## Handoff

Report the final dependency sets with a justification per entry, the exact commands you ran with their
results, and anything in the target layout that the specification names but you could not place.
