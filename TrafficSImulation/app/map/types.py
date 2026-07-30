from dataclasses import dataclass


@dataclass
class ResolvedPlace:
    name: str
    latitude: float
    longitude: float
    source: str
