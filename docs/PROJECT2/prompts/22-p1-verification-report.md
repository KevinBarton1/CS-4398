# P1 Verification Report — Prompt 22

**Date:** 2026-07-31  
**Verifier:** Prompt 22 acceptance pass  
**Repository:** `TrafficSImulation/` under `CS-4398`

---

## Commands Run And Results

| Command | Result | Notes |
|---------|--------|-------|
| `python -m pytest` | **PASS** — 176 passed, 1 deselected | Default run excludes `@live` (T-57) via `pytest.ini` |
| `npm test` | **PASS** — 64 tests in 17 files | Vitest component and hook suite |
| `npm run build` | **PASS** | `tsc -b` clean; bundle 267.53 kB (84.63 kB gzip) |
| `python main.py` | **PASS** | Uvicorn on `http://127.0.0.1:8000`; startup probe logs warning when credentials absent |
| Manual API smoke | **PASS** (partial) | See Manual Smoke section |

No production code changes were required. The suite was already green.

---

## Architecture Acceptance Criteria

| Criterion | Status | Evidence |
|-----------|--------|----------|
| No Model-to-Controller import edge | ✅ | `test_t45_model_packages_do_not_import_controller` |
| `app/api/planning.py` contains no numeric coefficient | ✅ | `test_t45_planning_has_no_numeric_coefficient_literals` |
| `GOOGLE_MAPS_API_KEY` in no response body | ✅ | T-11 map-config tests; T-49 sanitization |
| `GET /api/map/config` returns `maps_browser_api_key`, never `maps_api_key` | ✅ | `test_t11_map_config_returns_browser_key_and_map_constants` |
| `google.maps` only in four map components | ✅ | `test_t56_google_maps_usage_confined_to_map_components` |
| Mode literals only in mode policy (+ schema allowlist) | ✅ | `test_t46_mode_literals_are_confined_to_allowlist` (`mode_policy.py`, `models.py`) |

Checkboxes updated in [architecture-overview.md](../srs-context/architecture/architecture-overview.md).

---

## Test Catalog — P1 IDs

| ID | Present | Green | Notes |
|----|---------|-------|-------|
| T-01 … T-39 | Yes | Yes | Named in test files under `tests/` and `src/` |
| T-42 | Yes | Yes | `tests/test_static.py` |
| T-43 | Yes | Yes | Verified by `npm run build` (tsc + vite) |
| T-45 | Yes | Yes | `tests/test_architecture.py` |
| T-46 | Yes | Yes | `tests/test_architecture.py` |
| T-49 | Yes | Yes | `tests/test_errors.py` |
| T-54 | Yes | Yes | `tests/test_config.py` |
| T-56 | Yes | Yes | `tests/test_architecture.py` |
| T-57 | Yes | Opt-in | 1 test collected, deselected by `-m "not live"` |

**Not in P1 default scope (deferred, not defects):**

| ID | Reason |
|----|--------|
| T-52 | Performance harness not implemented — NFR-1.1, NFR-1.2, NFR-1.3 deferred |
| T-55 | Full accessibility harness not implemented — NFR-4.5, NFR-7.7 partial (contrast unit tests only) |

---

## Traceability Updates

Updated [traceability.md](../srs-context/requirements/traceability.md):

- **57 P1 functional rows:** `Complete`
- **48 P1 non-functional rows:** `Complete` except the deferred/partial rows below
- **P2 and P3 rows:** unchanged (`Not started`)

| ID | Progress | Reason |
|----|----------|--------|
| NFR-1.1 | Deferred — T-52 performance harness | No latency harness in repo |
| NFR-1.2 | Deferred — T-52 performance harness | Same |
| NFR-1.3 | Deferred — T-52 performance harness | Same |
| NFR-3.5 | Deferred — manual deployment review | TLS/HTTPS is deployment concern |
| NFR-4.5 | Partial — contrast subset | `src/utils/contrast.test.ts` passes; full T-55 audit absent |
| NFR-5.8 | Deferred — no lint runner configured | No ESLint/Ruff script; style follows AGENTS.md |
| NFR-7.7 | Partial — contrast subset | Same as NFR-4.5 for legibility metrics |

---

## Locked Decisions Confirmation

| Decision | Holds |
|----------|-------|
| Two modes (`simulated`, `realtime`) | ✅ T-22, T-28 |
| Three scenario variables (`hour`, `weather`, `congestion`) | ✅ T-26, T-03 |
| Four endpoints, three active in P1 | ✅ `/api/plan`, `/api/health`, `/api/map/config` tested; heatmap P3 only |
| One map path (Maps JavaScript API) | ✅ T-31, T-56 |
| Two credentials (server + browser) | ✅ T-11, T-54 |
| No `demand` | ✅ Absent from models, types, and tests |

---

## Defects Fixed

None. Verification found no failing P1 criterion.

---

## Defects Deferred (Explicit Follow-Up)

| Item | ID | Action for Prompt 23+ |
|------|----|-----------------------|
| Plan latency p95 | T-52 | Add performance harness; close NFR-1.1–1.3 |
| FCP / debounce-to-render timing | T-52 | Same harness |
| Full WCAG audit and reduced-motion | T-55 | Add accessibility harness; close NFR-4.5, NFR-7.7 |
| TLS-only deployment | NFR-3.5 | Manual ops review at deploy time |
| Lint gate | NFR-5.8 | Add ESLint/Ruff to CI or document manual review |

These are **not P2 feature scope** unless Prompt 23 chooses to implement the harnesses.

---

## Manual Smoke Observations

**Environment (2026-07-31, credentials present):** `.env` loaded after server restart. `python main.py` + `npm run dev` at `http://127.0.0.1:5173`.

| Scenario | Observation |
|----------|-------------|
| **Health / server key** | `GET /api/health` → `200`, `google_maps.ok: true`, Places and Routes reachable |
| **Simulated plan (API)** | `POST /api/plan` → 3 routes, `scenario_applied: true`, recommended route present (~8 s) |
| **Real-Time plan (API)** | `POST /api/plan` → 1 route, `scenario_applied: false`, `data_source: Google Routes with live traffic` (~7 s) |
| **Simulated plan (browser)** | Initial load planned Downtown Austin → Austin Airport; three route cards (Fastest, Balanced, Low traffic); analysis panel populated |
| **Real-Time switch** | Mode toggle re-planned; scenario sliders hidden; single Fastest route; Real-Time notice displayed |
| **Scenario debounce** | Covered by passing T-27; live slider interaction not re-verified in browser (keyboard/drag on range input inconclusive in automation) |
| **Map render** | **Blocked** — see map-config note below |
| **Map config failure (deliberate)** | `GET /api/map/config` → `503 maps_not_configured`. Map region shows contained error; route cards and analysis remain usable (NFR-2.3, FR-7.5) |

### Map-config note

Only `GOOGLE_MAPS_API_KEY` (server key) was present. Planning and health checks work. **`GOOGLE_MAPS_BROWSER_API_KEY` is still required** for `GET /api/map/config` and the interactive map. Add it to `.env` as a separate referrer-restricted Maps JavaScript API key, restart the server, then reload the app to verify polyline rendering.

Without the browser key, the deliberate map-config failure path is still valid P1 evidence: planning degrades separately from the map surface.

---

## Definition Of Done

- [x] `python -m pytest`, `npm test`, and `npm run build` all pass
- [x] Every architecture overview acceptance criterion is ticked with evidence
- [x] Every P1 Target row in traceability has Progress reflecting passing tests (or explicit Deferred/Partial)
- [x] T-01 through T-39, T-42, T-43, T-45, T-46, T-49, T-54, T-56 green; T-57 opt-in only
- [x] Manual smoke recorded (API + test-backed UI behaviors)
- [x] This verification report exists
- [x] No P2 or P3 behavior was introduced

---

## Handoff To Prompt 23

P1 is **complete** for all behavior covered by the automated catalog. Prompt 23 should treat **T-52**, **T-55**, **NFR-3.5**, and **NFR-5.8** as open measurement/deployment items, not as missing P2 features, unless the team explicitly scopes harness work into P2.
