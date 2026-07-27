# Controller Context — API Endpoints

**Layer:** Controller  
**Codebase:** `TrafficSImulation/main.py`, `TrafficSImulation/app/models.py`  
**Related:** [orchestration.md](orchestration.md), [validation-error-handling.md](validation-error-handling.md), [model/data-models.md](../model/data-models.md)

## Purpose

Expose HTTP endpoints for health checks and route planning; validate inbound requests; serve production frontend (SRS Part 4.3 — Python backend).

## Endpoints

### `GET /api/health`

**Response 200:**

```json
{
  "status": "ok",
  "service": "TrafficScope",
  "version": "1.1"
}
```

Used for service availability checks.

### `POST /api/plan`

**Request body:** `PlanRequest` (JSON)

```json
{
  "origin": "Downtown Austin",
  "destination": "Austin Airport",
  "mode": "simulated",
  "heatmap": "congestion",
  "hour": 17,
  "weather": 1,
  "congestion": 56,
  "demand": 68
}
```

**Response 200:** `PlanResult` shape — see [data-models.md](../model/data-models.md).

**Response 400:** `{ "detail": "<error message>" }` — business logic errors (invalid location, same origin/dest).

**Response 422:** Pydantic validation errors — out-of-range or missing required fields.

### Static / SPA (production)

When `dist/` exists:

- `GET /assets/*` — static files
- `GET /{path}` — SPA fallback to `index.html`

Dev mode: Vite on port 5173 proxies `/api` to port 8000.

## OpenAPI

FastAPI auto-generates docs at `/docs` when server running.

## SRS Functional Mapping

| FR | Endpoint responsibility |
|----|-------------------------|
| FR-1.6 | `/api/plan` triggers route calculation |
| FR-5.6 | Same endpoint recalculates on scenario change |
| FR-6.1–6.4 | Response includes pricing per route |
| FR-7.7 | 400 when route cannot be calculated |

## Request / Response Contract

### Required client fields

`origin`, `destination` (strings, 1–120 chars).

### Optional with defaults

`mode`, `heatmap`, `hour`, `weather`, `congestion`, `demand`.

### Response guarantees (success)

- `routes.length === 3`
- Each route has `segments`, `factors`, `points`
- `recommended_route_id` matches one route id
- `heatmap.cells` populated unless mode was `off`
- `notice` string present

## Acceptance Criteria

- [ ] Health returns 200 with version (test_health_endpoint).
- [ ] Valid plan returns 200 with 3 routes (test_typed_plan_endpoint).
- [ ] weather=99 returns 422 (test_out_of_range_scenario_is_rejected).
- [ ] Invalid location returns 400 with descriptive detail.
- [ ] CORS/proxy works in Vite dev setup.

## Non-Functional

| ID | Requirement |
|----|-------------|
| NFR-3.1 | Respond within 5 seconds under normal conditions |
| NFR-5.4 | HTTPS when deployed with TLS termination |
| NFR-5.5 | API keys not in client — backend holds secrets |

## Agent Implementation Notes

- Add new endpoints in `main.py`; keep business logic in `app/routes.py` or domain modules.
- Version string in health should bump with breaking API changes.
- If adding WebSocket or streaming traffic updates, document separately.
- Frontend fetch: `POST /api/plan` with `Content-Type: application/json`.
