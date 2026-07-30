import math

from urllib.parse import urlencode

from app.config import GOOGLE_MAPS_API_KEY

EMBED_BASE_URL = "https://www.google.com/maps/embed/v1/view"
DIRECTIONS_BASE_URL = "https://www.google.com/maps/embed/v1/directions"


def compute_map_view(
    origin_lat: float,
    origin_lng: float,
    destination_lat: float,
    destination_lng: float,
) -> tuple[float, float, int]:
    center_lat = (origin_lat + destination_lat) / 2
    center_lng = (origin_lng + destination_lng) / 2
    span = max(abs(origin_lat - destination_lat), abs(origin_lng - destination_lng))
    if span > 0.5:
        zoom = 10
    elif span > 0.2:
        zoom = 11
    elif span > 0.1:
        zoom = 12
    elif span > 0.05:
        zoom = 13
    else:
        zoom = 14
    return center_lat, center_lng, zoom


def compute_map_view_for_polyline(
    polyline: list[dict[str, float]],
    viewport_aspect: float = 1.35,
    padding: float = 0.15,
) -> tuple[float, float, int]:
    """Fit center and zoom so an entire route polyline is visible."""
    if len(polyline) < 2:
        if polyline:
            return polyline[0]["lat"], polyline[0]["lng"], 14
        return 30.27, -97.74, 12

    lats = [point["lat"] for point in polyline]
    lngs = [point["lng"] for point in polyline]
    min_lat, max_lat = min(lats), max(lats)
    min_lng, max_lng = min(lngs), max(lngs)

    center_lat = (min_lat + max_lat) / 2
    center_lng = (min_lng + max_lng) / 2

    lat_span = max(max_lat - min_lat, 0.001) * (1 + padding)
    lng_span = max(max_lng - min_lng, 0.001) * (1 + padding)
    lng_span /= max(math.cos(math.radians(center_lat)), 0.01)

    lat_zoom = math.log2(180 / lat_span)
    lng_zoom = math.log2(180 * viewport_aspect / lng_span)
    zoom = int(min(lat_zoom, lng_zoom))
    return center_lat, center_lng, max(1, min(18, zoom))


def build_map_embed_url(center_lat: float, center_lng: float, zoom: int = 12) -> str | None:
    if not GOOGLE_MAPS_API_KEY:
        return None
    params = urlencode({
        "key": GOOGLE_MAPS_API_KEY,
        "center": f"{center_lat},{center_lng}",
        "zoom": zoom,
        "maptype": "roadmap",
    })
    return f"{EMBED_BASE_URL}?{params}"


def build_directions_embed_url(origin: str, destination: str) -> str | None:
    if not GOOGLE_MAPS_API_KEY:
        return None
    params = urlencode({
        "key": GOOGLE_MAPS_API_KEY,
        "origin": origin,
        "destination": destination,
        "mode": "driving",
    })
    return f"{DIRECTIONS_BASE_URL}?{params}"
