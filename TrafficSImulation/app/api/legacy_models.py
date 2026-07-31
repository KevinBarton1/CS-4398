from dataclasses import asdict, dataclass
from typing import List

from pydantic import BaseModel, Field


class MapEmbedRequest(BaseModel):
    center_lat: float = Field(ge=-90, le=90)
    center_lng: float = Field(ge=-180, le=180)
    zoom: int = Field(ge=1, le=18)


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
    traffic_ratio: float = 1.0
    polyline: List[dict] | None = None

    def to_dict(self):
        payload = asdict(self)
        payload["polyline"] = self.polyline or []
        return payload


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
    objective: str
    normalized_score: float
    segments: List[RoadSegment]
    factors: dict
    data_source: str
    polyline: List[dict]

    def to_dict(self):
        return {
            **asdict(self),
            "segments": [
                segment.to_dict() if hasattr(segment, "to_dict") else segment
                for segment in self.segments
            ],
        }
