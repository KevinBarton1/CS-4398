import re
from datetime import datetime, timedelta, timezone

import httpx

from app.config import (
    GOOGLE_MAPS_API_KEY,
    GOOGLE_REGION_CODE,
    GOOGLE_ROUTES_COMPUTE_URL,
    GOOGLE_ROUTES_FIELD_MASK,
    ROUTE_COLORS,
)
from app.map.google_errors import format_google_api_error
from app.map.types import ResolvedPlace


ROUTE_NAMES = ("Fastest", "Balanced", "Low traffic")
ROUTE_OBJECTIVES = (
    "Minimum adjusted time",
    "Weighted time, distance, congestion and demand",
    "Minimum congestion exposure",
)


def _parse_duration_seconds(value) -> float | None:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        match = re.fullmatch(r"(\d+(?:\.\d+)?)s", value.strip())
        if match:
            return float(match.group(1))
    if isinstance(value, dict) and "seconds" in value:
        return float(value["seconds"])
    return None


def _require_api_key() -> None:
    if not GOOGLE_MAPS_API_KEY:
        raise ValueError("GOOGLE_MAPS_API_KEY is not configured.")


def _routes_headers() -> dict[str, str]:
    return {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": GOOGLE_MAPS_API_KEY,
        "X-Goog-FieldMask": GOOGLE_ROUTES_FIELD_MASK,
    }


def _waypoint(place: ResolvedPlace) -> dict:
    return {
        "location": {
            "latLng": {
                "latitude": place.latitude,
                "longitude": place.longitude,
            }
        }
    }


def _extract_road_names(steps: list[dict]) -> list[str]:
    names: list[str] = []
    for step in steps:
        instruction = (step.get("navigationInstruction") or {}).get("instructions") or ""
        road = ""
        if " on " in instruction.lower():
            road = re.split(r"\s+on\s+", instruction, maxsplit=1, flags=re.IGNORECASE)[-1].strip()
            road = re.sub(r"\s+toward.*$", "", road, flags=re.IGNORECASE)
        if not road:
            match = re.search(r"\bon\s+(.+?)(?:\s+toward|\s*$)", instruction, re.IGNORECASE)
            road = match.group(1).strip() if match else instruction.strip()
        if road and road not in names:
            names.append(road[:80])
        if len(names) >= 2:
            break
    if not names:
        return ["Route segment 1", "Route segment 2"]
    if len(names) == 1:
        names.append(f"{names[0]} continuation")
    return names[:2]


def _build_route_option(index: int, route: dict) -> dict:
    legs = route.get("legs") or []
    steps = legs[0].get("steps") if legs else []
    steps = steps or []

    distance_miles = round((route.get("distanceMeters") or 0) / 1609.344, 1)
    static_seconds = _parse_duration_seconds(route.get("staticDuration"))
    duration_seconds = _parse_duration_seconds(route.get("duration"))
    base_seconds = static_seconds or duration_seconds or 0

    return {
        "id": f"route-{index + 1}",
        "name": ROUTE_NAMES[index] if index < len(ROUTE_NAMES) else f"Route {index + 1}",
        "objective": ROUTE_OBJECTIVES[index] if index < len(ROUTE_OBJECTIVES) else route.get("description", "Route option"),
        "color": ROUTE_COLORS[index % len(ROUTE_COLORS)],
        "distance_miles": distance_miles,
        "base_eta_minutes": round(base_seconds / 60, 1),
        "road_names": _extract_road_names(steps),
        "google_steps": steps,
        "google_duration_seconds": duration_seconds,
        "google_static_duration_seconds": static_seconds,
        "map_source": "google",
    }


def compute_route_options(
    origin: ResolvedPlace,
    destination: ResolvedPlace,
    hour: int = 17,
    use_traffic: bool = False,
) -> list[dict]:
    _require_api_key()

    departure = datetime.now(timezone.utc).replace(
        hour=max(0, min(23, int(hour))),
        minute=0,
        second=0,
        microsecond=0,
    )
    if departure <= datetime.now(timezone.utc):
        departure += timedelta(days=1)

    payload = {
        "origin": _waypoint(origin),
        "destination": _waypoint(destination),
        "travelMode": "DRIVE",
        "computeAlternativeRoutes": True,
        "routingPreference": "TRAFFIC_AWARE" if use_traffic else "TRAFFIC_UNAWARE",
        "units": "IMPERIAL",
        "regionCode": GOOGLE_REGION_CODE,
    }
    # departureTime is only valid with traffic-aware routing preferences.
    if use_traffic:
        payload["departureTime"] = departure.isoformat().replace("+00:00", "Z")

    try:
        response = httpx.post(
            GOOGLE_ROUTES_COMPUTE_URL,
            json=payload,
            headers=_routes_headers(),
            timeout=10.0,
        )
        response.raise_for_status()
    except httpx.HTTPStatusError as error:
        detail = format_google_api_error(error.response)
        raise ValueError(f"Routes API HTTP {error.response.status_code}: {detail}") from error
    except httpx.HTTPError as error:
        raise ValueError(f"Routes API request failed: {error}") from error

    routes = response.json().get("routes") or []
    if not routes:
        raise ValueError("Google Routes returned no route alternatives for this trip.")

    return [
        _build_route_option(index, route)
        for index, route in enumerate(routes[:3])
    ]
