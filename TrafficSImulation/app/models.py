from dataclasses import asdict, dataclass
from typing import List


@dataclass
class Point:
    x: float
    y: float


@dataclass
class RoadSegment:
    name: str
    length_miles: float
    lanes: int
    speed_limit_mph: int
    average_speed_mph: float
    volume_vehicles_hour: int
    congestion: float


@dataclass
class RouteOption:
    id: str
    name: str
    color: str
    distance_miles: float
    base_eta_minutes: float
    adjusted_eta_minutes: float
    estimated_price: float
    congestion_score: int
    demand_score: int
    points: List[Point]
    segments: List[RoadSegment]
    factors: dict
    data_source: str

    def to_dict(self):
        return asdict(self)

