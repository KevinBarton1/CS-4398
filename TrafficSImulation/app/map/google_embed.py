from urllib.parse import urlencode

from app.config import GOOGLE_MAPS_API_KEY

EMBED_BASE_URL = "https://www.google.com/maps/embed/v1/view"


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
