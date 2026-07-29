from app.map.google_places import resolve_place
from app.map.google_routes import compute_route_options
from app.map.local import build_route_options as local_build_route_options


def geocode(value):
    """Resolve a location to a display name and SVG point, with Google Places fallback."""
    resolved = resolve_place(value)
    return resolved.name, resolved.point


def build_route_options(origin, destination, hour=17, use_traffic=False):
    """Build up to three route alternatives using Google Routes, falling back locally."""
    origin_place = resolve_place(origin)
    destination_place = resolve_place(destination)
    if origin_place.name == destination_place.name:
        raise ValueError("Origin and destination must be different.")

    google_routes = compute_route_options(
        origin_place,
        destination_place,
        hour=hour,
        use_traffic=use_traffic,
    )
    if google_routes:
        return origin_place.name, destination_place.name, google_routes

    return local_build_route_options(origin, destination)
