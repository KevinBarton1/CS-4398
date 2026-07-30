from dataclasses import asdict, dataclass
from typing import List

from pydantic import BaseModel, Field


class PlanRequest(BaseModel):
    origin: str = Field(min_length=1, max_length=120)
    destination: str = Field(min_length=1, max_length=120)
    mode: str = "simulated"
    hour: int = Field(default=17, ge=0, le=23)
    weather: int = Field(default=1, ge=0, le=3)
    congestion: int = Field(default=56, ge=0, le=100)
    demand: int = Field(default=68, ge=0, le=100)


@dataclass
class RoadSegment:
    name: str
    length_miles: float
    lanes: int
    speed_limit_mph: int
    average_speed_mph: float
    volume_vehicles_hour: int
    congestion: float
    capacity_vehicles_hour: int
    free_flow_minutes: float
    adjusted_minutes: float


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
    objective: str
    normalized_score: float
    segments: List[RoadSegment]
    factors: dict
    data_source: str

    def to_dict(self):
        return asdict(self)
