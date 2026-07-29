import math
from difflib import get_close_matches

from app.api.models import Point
from app.config import ROUTE_COLORS


PLACES = {
    "downtown austin": Point(500, 330),
    "ut austin": Point(490, 218),
    "austin airport": Point(795, 495),
    "the domain": Point(505, 72),
    "zilker park": Point(392, 390),
    "mueller": Point(650, 225),
    "south congress": Point(520, 485),
    "round rock": Point(610, 20),
    "cedar park": Point(315, 35),
    "east austin": Point(675, 342),
    "barton springs": Point(350, 405),
    "current location": Point(455, 305),
}

ALIASES = {
    "downtown": "downtown austin", "airport": "austin airport", "aus": "austin airport",
    "ut": "ut austin", "university of texas": "ut austin", "domain": "the domain",
    "zilker": "zilker park", "soco": "south congress", "east": "east austin",
    "barton": "barton springs", "roundrock": "round rock",
}

ROAD_NAMES = [
    "Lamar Blvd", "I-35", "MoPac Expressway", "Airport Blvd", "Riverside Dr", "Congress Ave",
]


def geocode(value):
    key = " ".join(str(value or "").strip().lower().split())
    key = ALIASES.get(key, key)
    if key in PLACES:
        return key.title(), PLACES[key]
    matches = get_close_matches(key, PLACES.keys(), n=1, cutoff=0.68)
    if matches:
        return matches[0].title(), PLACES[matches[0]]
    choices = ", ".join(name.title() for name in list(PLACES)[:6])
    raise ValueError(f'Unknown location "{value}". Try {choices}.')


def _distance_miles(a, b):
    return math.hypot(b.x - a.x, b.y - a.y) * 0.018 + 0.8


def build_route_options(origin, destination):
    origin_name, start = geocode(origin)
    destination_name, end = geocode(destination)
    if origin_name == destination_name:
        raise ValueError("Origin and destination must be different.")

    dx, dy = end.x - start.x, end.y - start.y
    length = max(math.hypot(dx, dy), 1)
    normal = Point(-dy / length, dx / length)
    midpoint = Point((start.x + end.x) / 2, (start.y + end.y) / 2)
    base_distance = _distance_miles(start, end)
    options = []
    for index, offset in enumerate((0, 68, -92)):
        bend = Point(midpoint.x + normal.x * offset, midpoint.y + normal.y * offset)
        distance = base_distance * (1 + index * 0.09)
        average_speed = (34, 38, 42)[index]
        options.append({
            "id": f"route-{index + 1}",
            "name": ("Fastest", "Balanced", "Low traffic")[index],
            "objective": (
                "Minimum adjusted time",
                "Weighted time, distance, congestion and demand",
                "Minimum congestion exposure",
            )[index],
            "color": ROUTE_COLORS[index],
            "distance_miles": round(distance, 1),
            "base_eta_minutes": round(distance / average_speed * 60 + 2, 1),
            "points": [start, bend, end],
            "road_names": [
                ROAD_NAMES[(index * 2) % len(ROAD_NAMES)],
                ROAD_NAMES[(index * 2 + 1) % len(ROAD_NAMES)],
            ],
            "map_source": "local",
        })
    return origin_name, destination_name, options
