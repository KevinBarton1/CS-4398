import ast
from pathlib import Path

import pytest

import app.config as config
from app.config import Settings


def test_documented_constants_match_catalog() -> None:
    expected = {
        "BASE_FARE": 2.20,
        "PER_MILE_RATE": 1.28,
        "PER_MINUTE_RATE": 0.31,
        "MINIMUM_FARE": 7.50,
        "PRICE_CONGESTION_DIVISOR": 500,
        "BPR_ALPHA": 0.15,
        "BPR_BETA": 4,
        "BASE_LANE_CAPACITY": 520,
        "MINIMUM_CRAWL_SPEED_MPH": 6.0,
        "SEGMENT_COUNT_MAX": 2,
        "SEGMENT_SPEED_LIMITS_MPH": (45, 55),
        "SEGMENT_LANE_COUNTS": (3, 4),
        "SEGMENT_CONGESTION_INDEX_STEP": 11,
        "SEGMENT_CONGESTION_MIN": 5,
        "SEGMENT_CONGESTION_MAX": 98,
        "PEAK_TIME_FACTOR": 1.22,
        "OFFPEAK_TIME_FACTOR": 0.92,
        "PEAK_HOURS_MORNING": (7, 9),
        "PEAK_HOURS_EVENING": (16, 18),
        "OFFPEAK_HOUR_START": 22,
        "OFFPEAK_HOUR_END": 6,
        "WEATHER_TIME_MULTIPLIERS": (1.0, 1.08, 1.18, 1.32),
        "WEATHER_PRICE_MULTIPLIERS": (1.0, 1.03, 1.07, 1.12),
        "WEATHER_LABELS": ("Clear", "Light rain", "Heavy rain", "Severe"),
        "WEATHER_SOURCE_SIMULATED": "Simulated fallback",
        "ROUTE_SCORE_WEIGHTS": {
            "time": 0.47,
            "distance": 0.23,
            "congestion": 0.30,
        },
        "ROUTE_COLORS": ["#55d6be", "#ffb35c", "#4d72e8"],
        "ROUTE_NAMES": ("Fastest", "Balanced", "Low traffic"),
        "ROUTE_OBJECTIVES": (
            "Minimum adjusted travel time",
            "Weighted time, distance, and congestion",
            "Minimum congestion exposure",
        ),
        "ROUTE_ALTERNATIVES_MAX": 3,
        "ROUTE_CONGESTION_INDEX_STEP": 9,
        "ROUTE_CONGESTION_FLOOR": 4,
        "ETA_FALLBACK_BUFFER_MINUTES": 2.0,
        "PLACE_MATCH_TOLERANCE_DEGREES": 0.0005,
        "DEFAULT_HOUR": 17,
        "DEFAULT_WEATHER": 1,
        "DEFAULT_CONGESTION": 56,
        "GOOGLE_PLACES_SEARCH_URL": (
            "https://places.googleapis.com/v1/places:searchText"
        ),
        "GOOGLE_ROUTES_COMPUTE_URL": (
            "https://routes.googleapis.com/directions/v2:computeRoutes"
        ),
        "GOOGLE_REGION_CODE": "US",
        "AUSTIN_LOCATION_BIAS": {
            "circle": {
                "center": {"latitude": 30.2672, "longitude": -97.7431},
                "radius": 35000.0,
            }
        },
        "GOOGLE_PLACES_FIELD_MASK": (
            "places.displayName,places.formattedAddress,places.location"
        ),
        "GOOGLE_ROUTES_FIELD_MASK": (
            "routes.duration,routes.staticDuration,routes.distanceMeters,"
            "routes.polyline.encodedPolyline,"
            "routes.travelAdvisory.speedReadingIntervals,"
            "routes.legs.travelAdvisory.speedReadingIntervals,"
            "routes.legs.steps.distanceMeters,routes.legs.steps.staticDuration,"
            "routes.legs.steps.polyline.encodedPolyline,"
            "routes.legs.steps.navigationInstruction,routes.description,"
            "routes.routeLabels"
        ),
        "PLACES_TIMEOUT_SECONDS": 8.0,
        "ROUTES_TIMEOUT_SECONDS": 10.0,
        "HEALTH_PROBE_CACHE_SECONDS": 30.0,
        "DATA_SOURCE_SIMULATED": (
            "Google Routes with departure-hour traffic"
        ),
        "DATA_SOURCE_REALTIME": "Google Routes with live traffic",
        "NOTICE_SIMULATED": (
            "Simulated mode: Google Maps supplies route geometry and "
            "departure-hour traffic; scenario controls adjust planning estimates."
        ),
        "NOTICE_REALTIME": (
            "Real-Time mode: route, distance, and travel time come from Google Maps "
            "traffic-aware routing for the current departure time."
        ),
        "SERVICE_NAME": "TrafficScope",
        "SERVICE_VERSION": "2.0",
        "MAP_DEFAULT_CENTER": {"lat": 30.2672, "lng": -97.7431},
        "MAP_DEFAULT_ZOOM": 12,
        "MAP_COLOR_SCHEME": "DARK",
        "MAP_LIBRARIES": ["core", "maps"],
    }

    for name, value in expected.items():
        assert getattr(config, name) == value


def test_indexed_catalog_lengths_are_consistent() -> None:
    assert len(config.WEATHER_TIME_MULTIPLIERS) == 4
    assert len(config.WEATHER_PRICE_MULTIPLIERS) == 4
    assert len(config.WEATHER_LABELS) == 4
    assert len(config.SEGMENT_SPEED_LIMITS_MPH) == config.SEGMENT_COUNT_MAX
    assert len(config.SEGMENT_LANE_COUNTS) == config.SEGMENT_COUNT_MAX
    assert len(config.ROUTE_COLORS) == config.ROUTE_ALTERNATIVES_MAX
    assert len(config.ROUTE_NAMES) == config.ROUTE_ALTERNATIVES_MAX
    assert len(config.ROUTE_OBJECTIVES) == config.ROUTE_ALTERNATIVES_MAX


def test_route_score_weights_have_documented_shape() -> None:
    assert set(config.ROUTE_SCORE_WEIGHTS) == {"time", "distance", "congestion"}
    assert sum(config.ROUTE_SCORE_WEIGHTS.values()) == pytest.approx(1.0)


@pytest.mark.parametrize("api_key", ["", "   "])
def test_empty_server_key_is_not_configured(api_key: str) -> None:
    configured = Settings(google_maps_api_key=api_key)

    assert configured.google_maps_configured is False


def test_settings_read_environment_and_normalize_empty_map_id(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("GOOGLE_MAPS_API_KEY", "test-server-key")
    monkeypatch.setenv("GOOGLE_MAPS_BROWSER_API_KEY", "test-browser-key")
    monkeypatch.setenv("GOOGLE_MAPS_MAP_ID", " ")

    configured = Settings()

    assert configured.google_maps_api_key == "test-server-key"
    assert configured.google_maps_browser_api_key == "test-browser-key"
    assert configured.google_maps_map_id is None


def test_unset_map_id_defaults_to_none(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("GOOGLE_MAPS_MAP_ID", raising=False)

    assert Settings().google_maps_map_id is None


def test_catalog_literals_are_not_redeclared_outside_config() -> None:
    app_root = Path(__file__).resolve().parents[1] / "app"
    config_path = app_root / "config" / "__init__.py"
    forbidden_numbers = {
        2.20,
        1.28,
        0.31,
        7.50,
        1.08,
        1.18,
        1.32,
        1.03,
        1.07,
        1.12,
        8.0,
        10.0,
        30.0,
    }
    forbidden_strings = {
        "Simulated fallback",
        "Google Routes with departure-hour traffic",
        "Google Routes with live traffic",
        (
            "Simulated mode: Google Maps supplies route geometry and departure-hour "
            "traffic; scenario controls adjust planning estimates."
        ),
        (
            "Real-Time mode: route, distance, and travel time come from Google Maps "
            "traffic-aware routing for the current departure time."
        ),
    }
    duplicate_literals: list[str] = []

    for path in app_root.rglob("*.py"):
        if path == config_path:
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        source = path.read_text(encoding="utf-8")
        if "BPR_ALPHA = 0.15" in source:
            duplicate_literals.append(
                f"{path.relative_to(app_root)} redeclares BPR_ALPHA"
            )
        for node in ast.walk(tree):
            if not isinstance(node, ast.Constant):
                continue
            is_duplicate_number = (
                isinstance(node.value, float)
                and node.value in forbidden_numbers
            )
            is_duplicate_string = (
                isinstance(node.value, str)
                and node.value in forbidden_strings
            )
            if is_duplicate_number or is_duplicate_string:
                duplicate_literals.append(
                    f"{path.relative_to(app_root)}:{node.lineno}={node.value!r}"
                )

    assert duplicate_literals == []
