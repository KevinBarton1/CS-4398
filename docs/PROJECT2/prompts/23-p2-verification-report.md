# P2 Verification Report — Prompt 23

**Date:** 2026-07-31  
**Verifier:** Prompt 23 depth and resilience pass  
**Repository:** `TrafficSImulation/` under `CS-4398`

---

## Commands Run And Results

| Command | Result | Notes |
|---------|--------|-------|
| `python -m pytest` | **PASS** — 182 passed, 1 deselected | T-57 remains opt-in via `@live` |
| `npm test` | **PASS** — 68 tests in 18 files | Includes T-48, T-55 harness |
| `npm run build` | **PASS** | `tsc -b` clean; bundle 268.51 kB (84.90 kB gzip) |
| `npm run check:bundle` | **PASS** | 82.91 kB gzip JS (budget 400 kB) |
| `npm run test:e2e` | **PASS** | T-44 in `e2e/plan.spec.ts` (~710 ms) |

---

## P2 Requirements Closed

All P2 Target rows in [traceability.md](../srs-context/requirements/traceability.md) are marked `Complete`:

| ID | Requirement | Test |
|----|-------------|------|
| FR-1.8 | Scenario-only re-plan issues no new Places request | T-47 |
| FR-2.11 | Segments cover the full step list | T-14 expansion |
| FR-3.8 | Origin and destination markers with labels | T-48 |
| FR-3.9 | Polyline click selects route | T-48 |
| FR-7.10 | One jittered retry on transient upstream failure | T-50 |
| NFR-1.6 | Cached place resolution avoids repeat Places calls | T-47 |
| NFR-1.7 | Bundle under 400 kB gzipped (excluding Maps script) | T-53 |
| NFR-2.6 | One jittered retry on transient failure | T-50 |
| NFR-3.8 | Credentials rotate without code change | T-54 extension |
| NFR-4.7 | Reduced-motion preference honored | T-55 |
| NFR-4.8 | Automated accessibility audit — no critical violations | T-55 |
| NFR-6.8 | End-to-end plan, select, mode switch | T-44 |

No P3 behavior (heatmap, demand, alternate map paths) was introduced.

---

## Cache Key Design (FR-1.8, NFR-1.6)

**Module:** `app/map/place_cache.py` — `PlaceResolutionCache`  
**Wiring:** `GooglePlacesGateway` in `app/map/places.py`; singleton on `app.state.place_cache` via `main.py`.

**Key:** Normalized query text — `" ".join(query.strip().lower().split())`.

**Behavior:**

- Cache hits return the stored `ResolvedPlace` without a network call.
- Cache misses call Places, then store under the normalized key.
- Scenario-only re-plans reuse cached origin/destination resolution (T-47).
- Real-Time plan responses are **not** cached at the plan level (orchestration constraint preserved).

---

## Retry Policy (FR-7.10, NFR-2.6)

**Module:** `app/map/retry.py` — `with_upstream_retry`  
**Used by:** `app/map/places.py`, `app/map/routing.py`

| Setting | Value | Source |
|---------|-------|--------|
| Max retries | 1 | `UPSTREAM_RETRY_MAX = 1` in `app/config/__init__.py` |
| Jitter range | 0.05–0.15 s | `UPSTREAM_RETRY_JITTER_MIN/MAX_SECONDS` |

**Retryable errors:** `httpx.TimeoutException`, `httpx.ConnectError`, HTTP status ≥ 500.  
**Non-retryable:** 4xx, validation errors, and other non-transient failures propagate immediately.  
Sanitization paths in error handling remain unchanged.

---

## Frontend Depth (FR-3.8, FR-3.9, NFR-4.7)

| Feature | Module |
|---------|--------|
| Origin/destination markers (A/B labels) | `src/components/RouteEndpointMarkers.tsx` |
| Polyline click-to-select | `src/components/RoutePolylineLayer.tsx` + `routePolylineSlices.ts` |
| Reduced motion | `@media (prefers-reduced-motion: reduce)` in `src/styles.css` |
| Accessibility harness | `src/accessibility.harness.test.ts` (contrast + reduced-motion + axe) |

T-56 allowlist updated to include `RouteEndpointMarkers.tsx` (five map components total).

---

## Credential Rotation (NFR-3.8)

T-54 extension in `tests/test_config.py` confirms `GOOGLE_MAPS_API_KEY`, `GOOGLE_MAPS_BROWSER_API_KEY`, and `GOOGLE_MAPS_MAP_ID` reload from environment without code changes.

---

## End-to-End Flow (NFR-6.8, T-44)

**Command:** `npm run test:e2e` (Playwright)

**Spec:** `e2e/plan.spec.ts`

**Flow covered:**

1. Initial simulated plan renders route cards (Fastest, Balanced).
2. User selects Balanced (`aria-pressed="true"`).
3. User switches to Real-Time — second route hidden, Real-Time mode active, scenario-unavailable copy visible.

**Note:** Map config is mocked as 503 in e2e so the test focuses on planning/analysis without loading the Google Maps script. Map markers and polyline selection are covered by T-48 component tests and manual smoke (map rendering confirmed by user in Prompt 22 follow-up).

---

## P1 Carry-Forward (Not P2 Scope)

These remain open from Prompt 22 and were **not** in Prompt 23 scope:

| Item | Status |
|------|--------|
| T-52 performance harness (NFR-1.1–1.3) | Deferred |
| Full manual T-55 accessibility audit (NFR-4.5, NFR-7.7) | Partial |
| NFR-3.5 deployment TLS manual review | Deferred |
| NFR-5.8 lint runner | Deferred |

---

## Manual Smoke Reminder

User confirmed map rendering with `GOOGLE_MAPS_BROWSER_API_KEY` after Prompt 22. P2 map features (markers, polyline click) should be verified locally with both server and browser keys configured.

**Local dev:** `python main.py` + `npm run dev` from `TrafficSImulation/`.
