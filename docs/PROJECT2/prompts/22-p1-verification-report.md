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

Environment: no `.env` file present (only `.env.example`). Server started with `python main.py`.

| Scenario | Observation |
|----------|-------------|
| **Simulated plan** | Live call blocked without credentials (`503 maps_not_configured`). Behavior covered by mocked T-01 and component T-25. |
| **Real-Time plan** | Same credential gate. Covered by T-02 and T-28. |
| **Mode switch** | Component tests T-28 confirm Real-Time hides scenario controls and re-plans. |
| **Scenario debounce** | T-27 confirms coalescing and abort of superseded requests. |
| **Map render** | T-31 confirms `APIProvider` mounts with fetched credentials and polylines render in jsdom. |
| **Map config failure** | `GET /api/map/config` returned `503` with `{"code":"maps_not_configured","detail":"Google Maps is not configured on the server."}` — matches FR-7.5 / NFR-2.3 contract. |
| **Health** | `GET /api/health` returned `200` with `google_maps.ok: false` and probe message; startup was not blocked (NFR-2.4). |

Full browser smoke with live Google credentials requires copying `.env.example` to `.env` and setting both keys. That path is optional (T-57).

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
