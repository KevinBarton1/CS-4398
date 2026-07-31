"""T-24: Locked API response field sets and Python–TypeScript mirror."""

from __future__ import annotations

import re
from pathlib import Path

import pytest
from pydantic import BaseModel

from app.api.models import (
    ErrorResponse,
    HealthResponse,
    MapConfigResponse,
    PlanRequest,
    PlanResponse,
    PriceFactors,
    RoadSegment,
    RouteOption,
    Scenario,
    ValidationField,
    WeatherState,
)
from app.map.health import ProbeResult
from app.map.types import LatLngPoint, RouteBounds, TrafficInterval

ROOT = Path(__file__).resolve().parents[1]
TYPES_TS = ROOT / "src" / "types.ts"

# Set to True in prompt 13 after src/types.ts mirrors app/api/models.py.
TYPESCRIPT_MIRROR_ENABLED = False

LOCKED_MODEL_FIELDS: dict[str, set[str]] = {
    "PlanResponse": {
        "origin",
        "destination",
        "mode",
        "scenario_applied",
        "scenario",
        "weather",
        "routes",
        "recommended_route_id",
        "map_bounds",
        "notice",
    },
    "Scenario": {"hour", "weather", "congestion"},
    "WeatherState": {
        "severity",
        "label",
        "time_multiplier",
        "price_multiplier",
        "source",
    },
    "RouteOption": {
        "id",
        "name",
        "objective",
        "color",
        "distance_miles",
        "base_eta_minutes",
        "adjusted_eta_minutes",
        "estimated_price",
        "congestion_score",
        "normalized_score",
        "data_source",
        "polyline",
        "traffic_intervals",
        "segments",
        "price_factors",
        "bounds",
    },
    "PriceFactors": {
        "route_subtotal",
        "traffic_multiplier",
        "weather_multiplier",
        "time_multiplier",
        "unrounded_total",
    },
    "RoadSegment": {
        "name",
        "length_miles",
        "lanes",
        "speed_limit_mph",
        "average_speed_mph",
        "volume_vehicles_hour",
        "congestion",
        "capacity_vehicles_hour",
        "free_flow_minutes",
        "adjusted_minutes",
        "traffic_ratio",
        "polyline",
    },
    "TrafficInterval": {"start_index", "end_index", "speed"},
    "LatLngPoint": {"lat", "lng"},
    "RouteBounds": {"north", "south", "east", "west"},
    "MapConfigResponse": {
        "maps_browser_api_key",
        "map_id",
        "default_center",
        "default_zoom",
        "color_scheme",
        "libraries",
    },
    "HealthResponse": {
        "status",
        "service",
        "version",
        "google_maps_configured",
        "google_maps",
    },
    "ProbeResult": {"ok", "message", "checked_at"},
    "ErrorResponse": {"detail", "code", "fields"},
    "ValidationField": {"field", "message"},
    "PlanRequest": {
        "origin",
        "destination",
        "mode",
        "hour",
        "weather",
        "congestion",
    },
}

MODEL_BY_NAME: dict[str, type[BaseModel]] = {
    "PlanResponse": PlanResponse,
    "Scenario": Scenario,
    "WeatherState": WeatherState,
    "RouteOption": RouteOption,
    "PriceFactors": PriceFactors,
    "RoadSegment": RoadSegment,
    "MapConfigResponse": MapConfigResponse,
    "HealthResponse": HealthResponse,
    "ErrorResponse": ErrorResponse,
    "ValidationField": ValidationField,
    "PlanRequest": PlanRequest,
}

DATACLASS_MODELS = {
    "ProbeResult": ProbeResult,
    "TrafficInterval": TrafficInterval,
    "LatLngPoint": LatLngPoint,
    "RouteBounds": RouteBounds,
}


def _pydantic_field_names(model: type[BaseModel]) -> set[str]:
    return set(model.model_fields.keys())


def _dataclass_field_names(model: type[object]) -> set[str]:
    import dataclasses

    return {field.name for field in dataclasses.fields(model)}  # type: ignore[arg-type]


@pytest.mark.parametrize("model_name", sorted(MODEL_BY_NAME))
def test_t24_pydantic_models_match_locked_field_sets(model_name: str) -> None:
    expected = LOCKED_MODEL_FIELDS[model_name]
    actual = _pydantic_field_names(MODEL_BY_NAME[model_name])
    assert actual == expected


@pytest.mark.parametrize("model_name", sorted(DATACLASS_MODELS))
def test_t24_dataclass_models_match_locked_field_sets(model_name: str) -> None:
    expected = LOCKED_MODEL_FIELDS[model_name]
    actual = _dataclass_field_names(DATACLASS_MODELS[model_name])
    assert actual == expected


def test_t24_route_option_has_price_factors_not_factors() -> None:
    assert "price_factors" in RouteOption.model_fields
    assert "factors" not in RouteOption.model_fields


def test_t24_plan_response_has_no_legacy_embed_fields() -> None:
    forbidden = {
        "hour",
        "congestion",
        "map_embed_url",
        "map_view",
        "directions_embed_url",
    }
    assert forbidden.isdisjoint(PlanResponse.model_fields.keys())


def test_t24_typescript_mirror_extension_point() -> None:
    """Enable by setting TYPESCRIPT_MIRROR_ENABLED after prompt 13."""
    if not TYPESCRIPT_MIRROR_ENABLED:
        pytest.skip("TypeScript mirror assertion deferred to prompt 13")

    assert TYPES_TS.exists(), "src/types.ts must exist for the mirror assertion"

    expected_interfaces = {
        "PlanResult": LOCKED_MODEL_FIELDS["PlanResponse"],
        "RouteOption": LOCKED_MODEL_FIELDS["RouteOption"],
        "PriceFactors": LOCKED_MODEL_FIELDS["PriceFactors"],
        "Scenario": LOCKED_MODEL_FIELDS["Scenario"],
        "MapConfig": LOCKED_MODEL_FIELDS["MapConfigResponse"],
    }
    source = TYPES_TS.read_text(encoding="utf-8")

    for interface_name, fields in expected_interfaces.items():
        match = re.search(
            rf"export interface {interface_name}\s*\{{([^}}]+)\}}",
            source,
            re.DOTALL,
        )
        assert match, f"Missing interface {interface_name} in src/types.ts"
        declared = {
            line.split(":")[0].strip()
            for line in match.group(1).splitlines()
            if line.strip() and not line.strip().startswith("//")
        }
        assert declared == fields

