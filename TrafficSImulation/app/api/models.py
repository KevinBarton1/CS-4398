from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.config import DEFAULT_CONGESTION, DEFAULT_HOUR, DEFAULT_WEATHER
from app.map.health import ProbeResult
from app.map.types import (
    LatLngPoint,
    RouteBounds,
    TrafficInterval,
    TrafficSpeed,
)

PlanMode = Literal["simulated", "realtime"]
HeatmapMetric = Literal["congestion"]


class ApiModel(BaseModel):
    model_config = ConfigDict(extra="forbid", from_attributes=True)


class PlanRequest(ApiModel):
    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
        strict=True,
    )

    origin: str = Field(min_length=1, max_length=120)
    destination: str = Field(min_length=1, max_length=120)
    mode: PlanMode = "simulated"
    hour: int = Field(default=DEFAULT_HOUR, ge=0, le=23)
    weather: int = Field(default=DEFAULT_WEATHER, ge=0, le=3)
    congestion: int = Field(default=DEFAULT_CONGESTION, ge=0, le=100)


class HeatmapRequest(ApiModel):
    hour: int = Field(default=DEFAULT_HOUR, ge=0, le=23)
    congestion: int = Field(default=DEFAULT_CONGESTION, ge=0, le=100)


class Scenario(ApiModel):
    hour: int = Field(ge=0, le=23)
    weather: int = Field(ge=0, le=3)
    congestion: int = Field(ge=0, le=100)


class WeatherState(ApiModel):
    severity: int = Field(ge=0, le=3)
    label: str
    time_multiplier: float
    price_multiplier: float
    source: str


class PriceFactors(ApiModel):
    route_subtotal: float
    traffic_multiplier: float
    weather_multiplier: float
    time_multiplier: float
    unrounded_total: float


class RoadSegment(ApiModel):
    name: str
    length_miles: float
    lanes: int
    speed_limit_mph: int
    average_speed_mph: float
    volume_vehicles_hour: int
    congestion: float = Field(ge=0.0, le=1.0)
    capacity_vehicles_hour: int
    free_flow_minutes: float
    adjusted_minutes: float
    traffic_ratio: float
    polyline: list[LatLngPoint]


class RouteOption(ApiModel):
    id: str
    name: str
    objective: str
    color: str
    distance_miles: float
    base_eta_minutes: float
    adjusted_eta_minutes: float
    estimated_price: float
    congestion_score: int = Field(ge=0, le=100)
    normalized_score: float = Field(ge=0)
    data_source: str
    polyline: list[LatLngPoint] = Field(min_length=1)
    traffic_intervals: list[TrafficInterval]
    segments: list[RoadSegment] = Field(min_length=1)
    price_factors: PriceFactors
    bounds: RouteBounds


class HeatmapCell(ApiModel):
    row: int = Field(ge=0)
    column: int = Field(ge=0)
    value: int = Field(ge=0, le=100)
    bounds: RouteBounds


class PlanResponse(ApiModel):
    origin: str
    destination: str
    mode: PlanMode
    scenario_applied: bool
    scenario: Scenario
    weather: WeatherState
    routes: list[RouteOption] = Field(min_length=1)
    recommended_route_id: str
    map_bounds: RouteBounds
    notice: str


class HeatmapResponse(ApiModel):
    metric: HeatmapMetric
    rows: int = Field(ge=1)
    columns: int = Field(ge=1)
    scenario: Scenario
    bounds: RouteBounds
    cells: list[HeatmapCell] = Field(min_length=1)
    notice: str


class MapConfigResponse(ApiModel):
    maps_browser_api_key: str
    map_id: str | None
    default_center: LatLngPoint
    default_zoom: int
    color_scheme: str
    libraries: list[str]


class HealthResponse(ApiModel):
    status: str
    service: str
    version: str
    google_maps_configured: bool
    google_maps: ProbeResult


class ValidationField(ApiModel):
    field: str
    message: str


class ErrorResponse(ApiModel):
    detail: str
    code: str
    fields: list[ValidationField] | None = None


__all__ = [
    "ErrorResponse",
    "HealthResponse",
    "HeatmapCell",
    "HeatmapMetric",
    "HeatmapRequest",
    "HeatmapResponse",
    "LatLngPoint",
    "MapConfigResponse",
    "PlanMode",
    "PlanRequest",
    "PlanResponse",
    "PriceFactors",
    "ProbeResult",
    "RoadSegment",
    "RouteBounds",
    "RouteOption",
    "Scenario",
    "TrafficInterval",
    "TrafficSpeed",
    "ValidationField",
    "WeatherState",
]
