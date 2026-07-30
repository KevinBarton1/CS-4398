from dataclasses import dataclass
from enum import Enum, unique
from typing import Literal


@dataclass(frozen=True, slots=True)
class LatLngPoint:
    lat: float
    lng: float


@dataclass(frozen=True, slots=True)
class RouteBounds:
    north: float
    south: float
    east: float
    west: float


@unique
class TrafficSpeed(str, Enum):
    NORMAL = "NORMAL"
    SLOW = "SLOW"
    TRAFFIC_JAM = "TRAFFIC_JAM"
    SPEED_UNSPECIFIED = "SPEED_UNSPECIFIED"


@dataclass(frozen=True, slots=True)
class TrafficInterval:
    start_index: int
    end_index: int
    speed: TrafficSpeed


@dataclass(frozen=True, slots=True)
class ResolvedPlace:
    name: str
    latitude: float
    longitude: float
    source: Literal["google"]


@dataclass(frozen=True, slots=True)
class RawRoute:
    id: str
    distance_miles: float
    duration_seconds: float | None
    static_duration_seconds: float | None
    traffic_ratio: float
    polyline: list[LatLngPoint]
    traffic_intervals: list[TrafficInterval]
    steps: list[dict[str, object]]
