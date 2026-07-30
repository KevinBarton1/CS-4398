# Model Context — Configuration

**Layer:** Model  
**Target modules:** `app/config/__init__.py`  
**Related:** [README.md](../../README.md), [domain-contracts.md](domain-contracts.md), [route-planning.md](route-planning.md), [traffic-simulation.md](traffic-simulation.md), [pricing.md](pricing.md), [weather-scenarios.md](weather-scenarios.md), [heatmaps.md](heatmaps.md), [google-integrations.md](google-integrations.md)

## Purpose

`app/config/__init__.py` is the single source of truth for every tunable number, every fixed string that
appears in a response, and every environment-derived setting. Two kinds of value live here and the difference
matters: `Settings` holds what the deployment supplies, and module-level constants hold what the domain
model asserts.

## Requirements

| ID | Requirement | Status | Phase |
|----|-------------|--------|-------|
| FR-7.2 | An absent server credential is reported as `maps_not_configured` before any upstream call | Target | P1 |
| NFR-3.1 | The server credential is never serialized to a client, a log line, or the browser bundle | Target | P1 |
| NFR-3.2 | The browser credential is a separate value from the server credential | Target | P1 |
| NFR-3.3 | Both credentials are supplied only through environment variables and never committed | Target | P1 |
| NFR-5.2 | The View imports no coefficient from the Model; every coefficient-bearing calculation stays in a Model module | Target | P1 |
| NFR-5.3 | Weather penalties, fare multipliers, and every other coefficient are defined once in `app/config/__init__.py` and duplicated nowhere else | Target | P1 |
| NFR-6.2 | Changing a coefficient changes behavior predictably and breaks only the tests that assert on it | Target | P1 |
| — | A runtime admin interface for tuning coefficients | Out of scope | — |
| — | Per-request coefficient overrides from the client | Out of scope | — |

## `Settings`

`Settings` carries what the deployment supplies. Values differ between a developer machine and a deployed
instance, and none of them is a domain coefficient.

```python
class Settings(BaseSettings):
    google_maps_api_key: str = ""
    google_maps_browser_api_key: str = ""
    google_maps_map_id: str | None = None

    @property
    def google_maps_configured(self) -> bool:
        return bool(self.google_maps_api_key.strip())
```

| Attribute | Environment variable | Type | Default | Purpose |
|-----------|---------------------|------|---------|---------|
| `google_maps_api_key` | `GOOGLE_MAPS_API_KEY` | string | `""` | Server key for Places and Routes. Never leaves the process |
| `google_maps_browser_api_key` | `GOOGLE_MAPS_BROWSER_API_KEY` | string | `""` | Referrer-restricted browser key, served by `GET /api/map/config` |
| `google_maps_map_id` | `GOOGLE_MAPS_MAP_ID` | string or null | `None` | Optional Google cloud-styled map identifier, serialized as `map_id` |
| `google_maps_configured` | — | bool | derived | Whether the server key is present; backs the health response field |

| Rule | Detail |
|------|--------|
| Loaded once | `Settings` is instantiated once at import and provided to the Controller through `app/api/dependencies.py`. Modules do not read `os.environ` directly |
| `.env` is loaded from the app root | `TrafficSImulation/.env`, loaded at import so `python main.py` and `python -m pytest` behave identically |
| Empty is absent | An empty or whitespace-only key counts as not configured, which is what raises `maps_not_configured` |
| Never logged | No code path logs, echoes, or serializes `google_maps_api_key`, including in an error `detail` |
| Only the browser key is served | `GET /api/map/config` returns `google_maps_browser_api_key` and `google_maps_map_id`. It never returns the server key |

## `.env` Contract

```
GOOGLE_MAPS_API_KEY=AIza...server
GOOGLE_MAPS_BROWSER_API_KEY=AIza...browser
GOOGLE_MAPS_MAP_ID=
```

| Variable | Required | Restriction to apply in the Google console | Absent behavior |
|----------|----------|--------------------------------------------|------------------|
| `GOOGLE_MAPS_API_KEY` | Yes | API-restricted to Places API (New) and Routes API; IP-restricted where the deployment allows | Every `POST /api/plan` returns `maps_not_configured` with HTTP 503, and `GET /api/health` reports `google_maps_configured` `false` |
| `GOOGLE_MAPS_BROWSER_API_KEY` | Yes | HTTP referrer restricted to the application origins; API-restricted to Maps JavaScript API | `GET /api/map/config` returns 503 with `maps_not_configured`, and the View shows a stated map-unavailable state in the map region only. It never serves an empty key, because an empty key produces a silently broken map instead of a reported failure |
| `GOOGLE_MAPS_MAP_ID` | No | None | `map_id` is `null` and the map uses the default styling |

Two keys, not one, because they have incompatible restrictions. A referrer-restricted key cannot be used from
a server, and a key usable from a server cannot be safely published to a browser. Reusing one key for both
would mean publishing a key that can call Places and Routes on someone else's behalf.

`.env` is never committed. The repository carries a `.env.example` with the variable names and empty values.

## Coefficient Catalog

Module-level constants. These are domain assertions, not deployment settings, so they are not environment
variables and cannot be overridden per request.

### Pricing

| Constant | Value | Unit | Consumer |
|----------|-------|------|----------|
| `BASE_FARE` | 2.20 | US dollars | `PricingModel` |
| `PER_MILE_RATE` | 1.28 | dollars per mile | `PricingModel` |
| `PER_MINUTE_RATE` | 0.31 | dollars per minute | `PricingModel` |
| `MINIMUM_FARE` | 7.50 | US dollars | `PricingModel` |
| `PRICE_CONGESTION_DIVISOR` | 500 | dimensionless | `PricingModel`, as `1 + congestion_score / divisor` |

### Traffic and segments

| Constant | Value | Unit | Consumer |
|----------|-------|------|----------|
| `BPR_ALPHA` | 0.15 | dimensionless | `bpr_adjusted_time` |
| `BPR_BETA` | 4 | dimensionless exponent | `bpr_adjusted_time` |
| `BASE_LANE_CAPACITY` | 520 | vehicles per hour per lane | `SegmentBuilder` |
| `MINIMUM_CRAWL_SPEED_MPH` | 6.0 | mph | `SegmentBuilder` |
| `SEGMENT_COUNT_MAX` | 2 | segments per route | `SegmentBuilder` |
| `SEGMENT_SPEED_LIMITS_MPH` | (45, 55) | mph by segment index | `SegmentBuilder` |
| `SEGMENT_LANE_COUNTS` | (3, 4) | lanes by segment index | `SegmentBuilder` |
| `SEGMENT_CONGESTION_INDEX_STEP` | 11 | percentage points per segment index | `SegmentBuilder` |
| `SEGMENT_CONGESTION_MIN` | 5 | percent | `SegmentBuilder` clamp floor |
| `SEGMENT_CONGESTION_MAX` | 98 | percent | `SegmentBuilder` clamp ceiling |
| `PEAK_TIME_FACTOR` | 1.22 | dimensionless | `time_of_day_factor` |
| `OFFPEAK_TIME_FACTOR` | 0.92 | dimensionless | `time_of_day_factor` |
| `PEAK_HOURS_MORNING` | (7, 9) | inclusive hour range | `time_of_day_factor` |
| `PEAK_HOURS_EVENING` | (16, 18) | inclusive hour range | `time_of_day_factor` |
| `OFFPEAK_HOUR_START` | 22 | hour of day | `time_of_day_factor` |
| `OFFPEAK_HOUR_END` | 6 | hour of day, exclusive | `time_of_day_factor` |

### Weather

| Constant | Value | Unit | Consumer |
|----------|-------|------|----------|
| `WEATHER_TIME_MULTIPLIERS` | (1.0, 1.08, 1.18, 1.32) | dimensionless, indexed by severity | `WeatherService`, Simulated ETA |
| `WEATHER_PRICE_MULTIPLIERS` | (1.0, 1.03, 1.07, 1.12) | dimensionless, indexed by severity | `WeatherService`, `PricingModel` |
| `WEATHER_LABELS` | ("Clear", "Light rain", "Heavy rain", "Severe") | display strings | `WeatherService` |
| `WEATHER_SOURCE_SIMULATED` | "Simulated fallback" | display string | `WeatherState.source` |

All three indexed tuples have exactly four entries, matching the severity range 0–3.

### Route identity and scoring

| Constant | Value | Unit | Consumer |
|----------|-------|------|----------|
| `ROUTE_SCORE_WEIGHTS` | `{"time": 0.47, "distance": 0.23, "congestion": 0.30}` | dimensionless weights summing to 1.0 | `RouteScorer` |
| `ROUTE_COLORS` | ["#55d6be", "#ffb35c", "#4d72e8"] | hex RGB by index | route identity assignment |
| `ROUTE_NAMES` | ("Fastest", "Balanced", "Low traffic") | display strings by index | route identity assignment |
| `ROUTE_OBJECTIVES` | ("Minimum adjusted travel time", "Weighted time, distance, and congestion", "Minimum congestion exposure") | display strings by index | route identity assignment |
| `ROUTE_ALTERNATIVES_MAX` | 3 | routes | `GoogleRoutesGateway` truncation |
| `ROUTE_CONGESTION_INDEX_STEP` | 9 | percentage points per route index | `congestion_score` derivation |
| `ROUTE_CONGESTION_FLOOR` | 4 | percent | `congestion_score` derivation |
| `ETA_FALLBACK_BUFFER_MINUTES` | 2.0 | minutes | segment-sum ETA fallback |
| `PLACE_MATCH_TOLERANCE_DEGREES` | 0.0005 | degrees | distinct-endpoint check |

`ROUTE_SCORE_WEIGHTS` has exactly three keys. There is no fourth term.

### Scenario defaults

| Constant | Value | Unit | Consumer |
|----------|-------|------|----------|
| `DEFAULT_HOUR` | 17 | hour of day | `PlanRequest` default |
| `DEFAULT_WEATHER` | 1 | severity index | `PlanRequest` default |
| `DEFAULT_CONGESTION` | 56 | percent | `PlanRequest` default |

The View keeps its own copies of these three defaults in `src/constants/scenario.ts` so the form can render
before the first response. That is the one intentional duplication in the system, and a test asserts the two
sets agree; see the no-magic-numbers rule below.

### Google integration

| Constant | Value | Unit | Consumer |
|----------|-------|------|----------|
| `GOOGLE_PLACES_SEARCH_URL` | `https://places.googleapis.com/v1/places:searchText` | URL | `GooglePlacesGateway` |
| `GOOGLE_ROUTES_COMPUTE_URL` | `https://routes.googleapis.com/directions/v2:computeRoutes` | URL | `GoogleRoutesGateway` |
| `GOOGLE_REGION_CODE` | "US" | region code | both gateways |
| `AUSTIN_LOCATION_BIAS` | circle centered on 30.2672, -97.7431 with radius 35000.0 | degrees and meters | `GooglePlacesGateway` |
| `GOOGLE_PLACES_FIELD_MASK` | `places.displayName,places.formattedAddress,places.location` | field mask | `GooglePlacesGateway` |
| `GOOGLE_ROUTES_FIELD_MASK` | the eleven-entry mask in [google-integrations.md](google-integrations.md) | field mask | `GoogleRoutesGateway` |
| `PLACES_TIMEOUT_SECONDS` | 8.0 | seconds | `GooglePlacesGateway` |
| `ROUTES_TIMEOUT_SECONDS` | 10.0 | seconds | `GoogleRoutesGateway` |
| `HEALTH_PROBE_CACHE_SECONDS` | 30.0 | seconds | `GoogleApiProbe` |

### Response strings

Fixed strings that appear in a response body belong here, because a test can then assert on the constant and
the string exists in exactly one place.

| Constant | Value |
|----------|-------|
| `DATA_SOURCE_SIMULATED` | `Google Routes with departure-hour traffic` |
| `DATA_SOURCE_REALTIME` | `Google Routes with live traffic` |
| `NOTICE_SIMULATED` | `Simulated mode: Google Maps supplies route geometry and departure-hour traffic; scenario controls adjust planning estimates.` |
| `NOTICE_REALTIME` | `Real-Time mode: route, distance, and travel time come from Google Maps traffic-aware routing for the current departure time.` |
| `SERVICE_NAME` | `TrafficScope` |
| `SERVICE_VERSION` | `2.0` |

### Browser map configuration

Served by `GET /api/map/config`. These are Model-side constants combined with the browser credential from
`Settings`.

| Constant | Value | Unit | Consumer |
|----------|-------|------|----------|
| `MAP_DEFAULT_CENTER` | `{"lat": 30.2672, "lng": -97.7431}` | degrees | `GET /api/map/config` |
| `MAP_DEFAULT_ZOOM` | 12 | zoom level | `GET /api/map/config` |
| `MAP_COLOR_SCHEME` | `DARK` | Maps JavaScript API color scheme | `GET /api/map/config` |
| `MAP_LIBRARIES` | ["core", "maps"] | Maps JavaScript API library names | `GET /api/map/config` |

### Heatmap (P3)

Defined only when P3 is taken up. Nothing in P1 or P2 reads these.

| Constant | Value | Unit | Consumer |
|----------|-------|------|----------|
| `HEATMAP_ROWS` | 5 | rows | `app/heatmap/grid.py` |
| `HEATMAP_COLUMNS` | 8 | columns | `app/heatmap/grid.py` |
| `HEATMAP_COVERAGE_BOUNDS` | the Austin service-area box | degrees | `app/heatmap/grid.py` |

## No Magic Numbers

The rule: if a number or a fixed response string carries meaning, it is a named constant in
`app/config/__init__.py` and every consumer imports it.

| Must be a constant | May stay inline |
|--------------------|-----------------|
| Any coefficient, rate, weight, or multiplier | A loop bound derived from a collection length |
| Any threshold, floor, ceiling, or clamp bound | A literal `0`, `1`, or `2` used as an index or an arithmetic identity |
| Any timeout, retry count, or cache duration | A rounding precision that is an inherent property of a display format |
| Any fixed string that appears in a response body | A unit conversion divisor with an unambiguous meaning, such as 1609.344 meters per mile or 60 seconds per minute |
| Any grid dimension or default | A test's own expected value, which should be written literally so the test fails when the constant changes |

Corollaries:

1. A constant is imported by name, never re-declared. Two modules that need the same value import the same
   symbol.
2. Tests assert on literals, not on the constants. A test that reads `BASE_FARE` still passes when
   `BASE_FARE` changes, which defeats its purpose. Documented behavior is pinned with literal expected
   values, and changing a coefficient is expected to fail exactly those tests.
3. Changing a coefficient must not require changing a formula. If it does, the formula has a second constant
   hidden inside it.
4. `src/constants/scenario.ts` is the one permitted duplication, because the form must render before the
   first response arrives. A test asserts the three View defaults equal `DEFAULT_HOUR`, `DEFAULT_WEATHER`, and
   `DEFAULT_CONGESTION`.

## The View Never Imports Coefficients

The View reads results. It does not recompute them.

| Rule | Detail |
|------|--------|
| No fare arithmetic in TypeScript | The price panel renders `estimated_price` and `price_factors`. It never multiplies a subtotal by a multiplier |
| No ETA arithmetic in TypeScript | The route card renders `base_eta_minutes` and `adjusted_eta_minutes`. It never applies a weather or time factor |
| No scoring in TypeScript | The list marks the route whose `id` equals `recommended_route_id`. It never compares `normalized_score` values to pick a winner |
| No weather table in TypeScript | The weather readout renders `label`, both multipliers, and `source` from the response |
| No color table in TypeScript for routes | Each polyline uses `RouteOption.color` from the response |
| Traffic colors are a View concern | Mapping the four `TrafficSpeed` values to stroke colors lives in `src/utils/trafficSegmentColor.ts`, because it is presentation with no Model counterpart |
| Formatting is a View concern | Currency, distance, and duration formatting live in `src/utils/format.ts` and change no value |

The reason is single-sourcing arithmetic. A fare computed in two languages will disagree at the cent, and the
one the user sees would then contradict the breakdown beside it, which is exactly what FR-6.4 forbids. The
same argument applies to the ETA and to the recommendation.

The only numbers the View may originate are the three scenario defaults, which it needs before any response
exists, and pure presentation values such as the debounce interval and layout breakpoints.

## Acceptance Criteria

- [ ] Every coefficient in the catalog is defined exactly once in `app/config/__init__.py`.
- [ ] No module under `app/` other than `app/config/__init__.py` contains a fare rate, a BPR coefficient, a weather multiplier, a score weight, a timeout, or a locked response string as a literal.
- [ ] `ROUTE_SCORE_WEIGHTS` has exactly the keys `time`, `distance`, and `congestion`, and its values sum to 1.0.
- [ ] `WEATHER_TIME_MULTIPLIERS`, `WEATHER_PRICE_MULTIPLIERS`, and `WEATHER_LABELS` each have exactly four entries.
- [ ] `SEGMENT_SPEED_LIMITS_MPH` and `SEGMENT_LANE_COUNTS` each have exactly `SEGMENT_COUNT_MAX` entries.
- [ ] `ROUTE_COLORS`, `ROUTE_NAMES`, and `ROUTE_OBJECTIVES` each have exactly `ROUTE_ALTERNATIVES_MAX` entries.
- [ ] `Settings` reads all three environment variables and treats a whitespace-only key as absent.
- [ ] An absent `GOOGLE_MAPS_API_KEY` yields `maps_not_configured` with HTTP 503 from `POST /api/plan` and `google_maps_configured` `false` from `GET /api/health`, without a crash at import.
- [ ] `GET /api/map/config` returns the browser key and never the server key.
- [ ] No response body, log line, or error `detail` contains the value of `GOOGLE_MAPS_API_KEY`.
- [ ] `map_id` is `null` when `GOOGLE_MAPS_MAP_ID` is unset.
- [ ] The three scenario defaults in `src/constants/scenario.ts` equal the three Python defaults.
- [ ] No file under `src/` contains a fare rate, a BPR coefficient, a weather multiplier, or a score weight.
- [ ] `.env` is git-ignored and `.env.example` lists all three variables with empty values.

## Planned Tests

| Test ID | Level | Target file | Assertion |
|---------|-------|-------------|-----------|
| T-54 | unit | `tests/test_config.py` | Every documented constant exists with its documented value and the indexed tuples have the documented lengths; `ROUTE_SCORE_WEIGHTS` has exactly three keys whose values sum to 1.0; a source scan finds no fare rate, BPR coefficient, weather multiplier, score weight, timeout, or locked response string as a literal outside `app/config/__init__.py`; and `Settings` treats an empty and a whitespace-only `GOOGLE_MAPS_API_KEY` as not configured |
| T-07 | api | `tests/test_api.py` | With no server key set the app imports, `POST /api/plan` returns 503 with `maps_not_configured`, and no response contains the key value |
| T-11 | api | `tests/test_api.py` | `GET /api/map/config` returns the browser key, `map_id` `null` when unset, and the documented center, zoom, color scheme, and libraries |
| T-26 | component | `src/components/ScenarioControls.test.tsx` | The View scenario defaults are 17, 1, and 56, matching the Python defaults |
| T-38 | component | `src/components/PriceSummary.test.tsx` | The panel renders the response values without recomputing the fare, verified by a fixture whose `estimated_price` disagrees with its factors |

## Agent Implementation Notes

- Add a new coefficient to `app/config/__init__.py` first, then import it. Never introduce a literal at a call
  site with a plan to extract it later.
- Keep `Settings` separate from the coefficient constants. Coefficients are not environment variables; making
  one configurable per deployment would make responses irreproducible across instances.
- Do not read `os.environ` outside `app/config/__init__.py`. Inject `Settings` through
  `app/api/dependencies.py` so tests can substitute one.
- A missing credential must not raise at import. The app must start, `GET /api/health` must answer, and only
  `POST /api/plan` may fail with `maps_not_configured`.
- Never log or serialize `google_maps_api_key`. When adding a diagnostic, log its presence as a boolean.
- Keep the locked response strings as constants and assert on their literal text in tests, so an accidental
  edit to a `notice` fails a test rather than shipping.
- When changing a coefficient deliberately, update this catalog, the owning model document, and the tests that
  pin the affected values in one change.
- T-54 includes a source scan. Keep it narrow, matching the specific documented values, so it does not fail on
  an unrelated numeric literal.
