from app.api.models import Point
from app.config import AUSTIN_BOUNDS, SVG_HEIGHT, SVG_WIDTH


def project_lat_lng(latitude: float, longitude: float) -> Point:
    """Project WGS84 coordinates onto the Austin SVG viewBox."""
    lat_span = AUSTIN_BOUNDS["lat_max"] - AUSTIN_BOUNDS["lat_min"]
    lng_span = AUSTIN_BOUNDS["lng_max"] - AUSTIN_BOUNDS["lng_min"]
    x = (longitude - AUSTIN_BOUNDS["lng_min"]) / lng_span * SVG_WIDTH
    y = (AUSTIN_BOUNDS["lat_max"] - latitude) / lat_span * SVG_HEIGHT
    return Point(
        x=round(max(0.0, min(SVG_WIDTH, x)), 1),
        y=round(max(0.0, min(SVG_HEIGHT, y)), 1),
    )


def simplify_polyline(points: list[Point], max_points: int = 24) -> list[Point]:
    if len(points) <= max_points:
        return points
    step = max(1, (len(points) - 1) // (max_points - 1))
    simplified = [points[index] for index in range(0, len(points), step)]
    if simplified[-1] is not points[-1]:
        simplified.append(points[-1])
    return simplified
