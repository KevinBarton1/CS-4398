from app.map.google_places import resolve_place
from app.map.google_routes import compute_route_options


def build_route_options(origin, destination, hour=17, use_traffic=False):
    """Build up to three route alternatives using Google Routes."""
    origin_place = resolve_place(origin)
    destination_place = resolve_place(destination)
    if origin_place.name == destination_place.name:
        raise ValueError("Origin and destination must be different.")

    routes = compute_route_options(
        origin_place,
        destination_place,
        hour=hour,
        use_traffic=use_traffic,
    )
    return origin_place.name, destination_place.name, routes, origin_place, destination_place
