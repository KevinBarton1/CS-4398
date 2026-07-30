from app.map.types import LatLngPoint, RouteBounds


def bounds_for_points(points: list[LatLngPoint]) -> RouteBounds:
    if not points:
        raise ValueError("Cannot compute bounds for an empty point list.")

    return RouteBounds(
        north=max(point.lat for point in points),
        south=min(point.lat for point in points),
        east=max(point.lng for point in points),
        west=min(point.lng for point in points),
    )


def union_bounds(bounds: list[RouteBounds]) -> RouteBounds:
    if not bounds:
        raise ValueError("Cannot compute a union for an empty bounds list.")

    return RouteBounds(
        north=max(box.north for box in bounds),
        south=min(box.south for box in bounds),
        east=max(box.east for box in bounds),
        west=min(box.west for box in bounds),
    )
