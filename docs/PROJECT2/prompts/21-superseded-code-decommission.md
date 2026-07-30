# Prompt 21 — Superseded Code Decommission

**Wave:** 4 — Convergence
**Depends on:** prompts 01 through 20
**Phase:** P1
**Read first:** [00-shared-context.md](00-shared-context.md)

## Read First

1. [00-shared-context.md](00-shared-context.md)
2. [../migration-from-current-implementation.md](../migration-from-current-implementation.md) — read all of it; it is the deletion inventory
3. [../README.md](../README.md), "Target module layout"
4. [../srs-context/architecture/architecture-overview.md](../srs-context/architecture/architecture-overview.md), Acceptance Criteria
5. The architecture tests from prompt 12 (T-45, T-46, T-56)

## Objective

Remove everything the rewrite replaced so the repository contains only the target design. This
package deletes; it does not redesign. After it lands, a grep for the migration document's forbidden
strings under production code returns nothing, and the architecture tests pass without legacy
allowlist exceptions.

## Deliverables

| Change | Responsibility |
|--------|----------------|
| Deletion of every legacy artifact listed in the migration document | Sections 1 through 10 |
| Cleanup of imports, re-exports, and dead tests that referenced those artifacts | Keep the suite green |
| Confirmation that T-45, T-46, and T-56 pass without legacy exceptions | Enforcement |

## Task

1. Delete the second map rendering path and its contract fields:
   - Embed API iframe branch and any component that still renders it.
   - `directions_embed_url`, `map_embed_url`, `build_directions_embed_url`, `build_map_embed_url`,
     `POST /api/map/embed`, and `app/map/google_embed.py` or its successor name if still present.
2. Delete server-computed camera state: `map_view`, `MapView`, `compute_map_view_for_polyline`,
   `MapEmbedRequest`, `app/map/projection.py`.
3. Delete the SVG map path: `RouteOverlay`, `mapProjection` helpers and their tests, any `Point` type
   with `x`/`y` screen coordinates, and stylized SVG road markup.
4. Delete local geocoding and local routing fallback: `app/map/local.py`, synthetic geometry
   generation, the `"current location"` server-side alias, and any `ResolvedPlace.source` value other
   than the Google source.
5. Delete or rename response fields that the migration renames: `factors` becomes `price_factors`,
   `maps_api_key` becomes `maps_browser_api_key`, flat hour/congestion echoes become the `scenario`
   object. Confirm no old name remains in production code or in `src/types.ts`.
6. Delete flat legacy module paths if any still exist on disk.
7. Confirm `demand` appears nowhere under production code or PROJECT2 docs outside the migration
   document.
8. Update or delete tests that asserted legacy behavior. Do not keep a skipped test as a memorial.
9. Run the full suite. T-45, T-46, and T-56 must pass. Run the migration document's validation sweep:
   the listed forbidden strings appear nowhere under `docs/PROJECT2/` except in the migration
   document itself, and nowhere under `TrafficSImulation/` production code.
10. Do not delete heatmap modules; they are deferred to P3, not removed. Leave them unimported and
    unexposed, as the migration document specifies.

## Boundaries

- Delete only what the migration document names, plus the dead imports and tests that referenced it.
- Do not rewrite a working target module "while you are here."
- Do not remove `.env.example`, configuration constants, or the heatmap package.
- Do not soften an architecture test to allow a leftover legacy path.

## Tests To Write

None new. Existing T-45, T-46, T-56, and the full suite are the verification.

## Definition Of Done

- [ ] Every artifact in migration sections 1 through 10 is gone from production code.
- [ ] No production file still exposes `directions_embed_url`, `map_embed_url`, `map_view`, `factors` (as a fare breakdown), `maps_api_key`, or `demand`.
- [ ] No flat legacy module path exists on disk.
- [ ] Heatmap modules remain on disk but are unimported by any P1 endpoint or component.
- [ ] The migration validation sweep is clean under `TrafficSImulation/` production code.
- [ ] T-45, T-46, and T-56 pass without legacy exceptions.
- [ ] `python -m pytest`, `npm test`, and `npm run build` all pass.

## Handoff

Report every path deleted, every test deleted or rewritten, any migration-listed artifact you could
not find (so it is already gone), and the validation-sweep command with its result.
