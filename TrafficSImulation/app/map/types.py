from dataclasses import dataclass

from app.api.models import Point


@dataclass
class ResolvedPlace:
    name: str
    latitude: float
    longitude: float
    point: Point
    source: str
