"""T-24: Locked API response field sets and Python–TypeScript mirror."""

from __future__ import annotations

import re
from pathlib import Path

import pytest
from pydantic import BaseModel

from app.api.models import (
    ErrorResponse,
    HealthResponse,
    HeatmapCell,
    HeatmapRequest,
    HeatmapResponse,
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
from app.config import DEFAULT_CONGESTION, DEFAULT_HOUR, DEFAULT_WEATHER
from app.map.health import ProbeResult
from app.map.types import LatLngPoint, RouteBounds, TrafficInterval

ROOT = Path(__file__).resolve().parents[1]
TYPES_TS = ROOT / "src" / "types.ts"
SCENARIO_TS = ROOT / "src" / "constants" / "scenario.ts"

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
    "HeatmapRequest": {"hour", "congestion"},
    "HeatmapCell": {"row", "column", "value", "bounds"},
    "HeatmapResponse": {
        "metric",
        "rows",
        "columns",
        "scenario",
        "bounds",
        "cells",
        "notice",
    },
}

TYPESCRIPT_INTERFACE_MIRROR: dict[str, tuple[str, set[str]]] = {
    "PlanResponse": ("PlanResult", LOCKED_MODEL_FIELDS["PlanResponse"]),
    "RouteOption": ("RouteOption", LOCKED_MODEL_FIELDS["RouteOption"]),
    "PriceFactors": ("PriceFactors", LOCKED_MODEL_FIELDS["PriceFactors"]),
    "RoadSegment": ("RoadSegment", LOCKED_MODEL_FIELDS["RoadSegment"]),
    "Scenario": ("Scenario", LOCKED_MODEL_FIELDS["Scenario"]),
    "WeatherState": ("WeatherState", LOCKED_MODEL_FIELDS["WeatherState"]),
    "MapConfigResponse": ("MapConfig", LOCKED_MODEL_FIELDS["MapConfigResponse"]),
    "HealthResponse": ("HealthResponse", LOCKED_MODEL_FIELDS["HealthResponse"]),
    "PlanRequest": ("PlanRequest", LOCKED_MODEL_FIELDS["PlanRequest"]),
    "HeatmapRequest": ("HeatmapRequest", LOCKED_MODEL_FIELDS["HeatmapRequest"]),
    "HeatmapResponse": ("HeatmapResult", LOCKED_MODEL_FIELDS["HeatmapResponse"]),
    "HeatmapCell": ("HeatmapCell", LOCKED_MODEL_FIELDS["HeatmapCell"]),
    "ErrorResponse": ("ApiError", LOCKED_MODEL_FIELDS["ErrorResponse"]),
    "ValidationField": ("ValidationField", LOCKED_MODEL_FIELDS["ValidationField"]),
    "LatLngPoint": ("LatLngPoint", LOCKED_MODEL_FIELDS["LatLngPoint"]),
    "RouteBounds": ("RouteBounds", LOCKED_MODEL_FIELDS["RouteBounds"]),
    "TrafficInterval": ("TrafficInterval", LOCKED_MODEL_FIELDS["TrafficInterval"]),
    "ProbeResult": ("ProbeResult", LOCKED_MODEL_FIELDS["ProbeResult"]),
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
    "HeatmapRequest": HeatmapRequest,
    "HeatmapResponse": HeatmapResponse,
    "HeatmapCell": HeatmapCell,
}

DATACLASS_MODELS = {
    "ProbeResult": ProbeResult,
    "TrafficInterval": TrafficInterval,
    "LatLngPoint": LatLngPoint,
    "RouteBounds": RouteBounds,
}

TYPESCRIPT_TYPE_ALIASES = {
    "Mode": {"simulated", "realtime"},
    "TrafficSpeed": {
        "NORMAL",
        "SLOW",
        "TRAFFIC_JAM",
        "SPEED_UNSPECIFIED",
    },
    "RequestState": {"idle", "loading", "success", "empty", "error"},
}


def _pydantic_field_names(model: type[BaseModel]) -> set[str]:
    return set(model.model_fields.keys())


def _dataclass_field_names(model: type[object]) -> set[str]:
    import dataclasses

    return {field.name for field in dataclasses.fields(model)}  # type: ignore[arg-type]


def _parse_typescript_interface(source: str, interface_name: str) -> set[str]:
    match = re.search(
        rf"export interface {interface_name}\s*\{{([^}}]+)\}}",
        source,
        re.DOTALL,
    )
    assert match, f"Missing interface {interface_name} in src/types.ts"
    return {
        line.split(":")[0].strip()
        for line in match.group(1).splitlines()
        if line.strip() and not line.strip().startswith("//")
    }


def _parse_typescript_type_alias(source: str, alias_name: str) -> set[str]:
    match = re.search(
        rf"export type {alias_name} = (.+?);",
        source,
        re.DOTALL,
    )
    assert match, f"Missing type alias {alias_name} in src/types.ts"
    return set(re.findall(r'"([^"]+)"', match.group(1)))


def _parse_typescript_const(source: str, name: str) -> int:
    match = re.search(rf"export const {name} = (\d+);", source)
    assert match, f"Missing constant {name}"
    return int(match.group(1))


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
        "heatmap",
    }
    assert forbidden.isdisjoint(PlanResponse.model_fields.keys())


@pytest.mark.parametrize(
    ("python_model", "typescript_name", "expected_fields"),
    [
        (python_model, ts_name, fields)
        for python_model, (ts_name, fields) in TYPESCRIPT_INTERFACE_MIRROR.items()
    ],
)
def test_t24_typescript_interfaces_mirror_python_models(
    python_model: str,
    typescript_name: str,
    expected_fields: set[str],
) -> None:
    del python_model
    source = TYPES_TS.read_text(encoding="utf-8")
    declared = _parse_typescript_interface(source, typescript_name)
    assert declared == expected_fields


@pytest.mark.parametrize(
    ("alias_name", "expected_literals"),
    sorted(TYPESCRIPT_TYPE_ALIASES.items()),
)
def test_t24_typescript_type_aliases_are_declared(
    alias_name: str,
    expected_literals: set[str],
) -> None:
    source = TYPES_TS.read_text(encoding="utf-8")
    declared = _parse_typescript_type_alias(source, alias_name)
    assert declared == expected_literals


def test_t24_scenario_defaults_match_python() -> None:
    source = SCENARIO_TS.read_text(encoding="utf-8")
    assert _parse_typescript_const(source, "DEFAULT_HOUR") == DEFAULT_HOUR
    assert _parse_typescript_const(source, "DEFAULT_WEATHER") == DEFAULT_WEATHER
    assert _parse_typescript_const(source, "DEFAULT_CONGESTION") == DEFAULT_CONGESTION
