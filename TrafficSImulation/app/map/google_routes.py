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
from app.map.polyline import decode_polyline
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


def _extract_speed_intervals(route: dict) -> list[dict]:
    intervals: list[dict] = []

    def append_intervals(items: list[dict]) -> None:
        for item in items:
            end_index = item.get("endPolylinePointIndex")
            if end_index is None:
                continue
            intervals.append({
                "start_index": int(item.get("startPolylinePointIndex") or 0),
                "end_index": int(end_index),
                "speed": item.get("speed") or "NORMAL",
            })

    for leg in route.get("legs") or []:
        advisory = leg.get("travelAdvisory") or {}
        append_intervals(advisory.get("speedReadingIntervals") or [])

    if not intervals:
        route_advisory = route.get("travelAdvisory") or {}
        append_intervals(route_advisory.get("speedReadingIntervals") or [])

    return intervals


def _traffic_ratio(duration_seconds: float | None, static_seconds: float | None) -> float:
    if not duration_seconds or not static_seconds or static_seconds <= 0:
        return 1.0
    return round(duration_seconds / static_seconds, 4)


def _build_route_option(index: int, route: dict) -> dict:
    legs = route.get("legs") or []
    steps = legs[0].get("steps") if legs else []
    steps = steps or []

    distance_miles = round((route.get("distanceMeters") or 0) / 1609.344, 1)
    static_seconds = _parse_duration_seconds(route.get("staticDuration"))
    duration_seconds = _parse_duration_seconds(route.get("duration"))
    base_seconds = static_seconds or duration_seconds or 0
    traffic_ratio = _traffic_ratio(duration_seconds, static_seconds)

    encoded_polyline = (route.get("polyline") or {}).get("encodedPolyline") or ""
    polyline = decode_polyline(encoded_polyline) if encoded_polyline else []

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
        "traffic_ratio": traffic_ratio,
        "traffic_intervals": _extract_speed_intervals(route),
        "polyline": polyline,
        "map_source": "google",
    }


def compute_route_options(
    origin: ResolvedPlace,
    destination: ResolvedPlace,
    hour: int = 17,
    use_traffic: bool = True,
    compute_alternatives: bool = True,
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
        "computeAlternativeRoutes": compute_alternatives,
        "routingPreference": "TRAFFIC_AWARE" if use_traffic else "TRAFFIC_UNAWARE",
        "units": "IMPERIAL",
        "regionCode": GOOGLE_REGION_CODE,
    }
    # departureTime is only valid with traffic-aware routing preferences.
    if use_traffic:
        payload["departureTime"] = departure.isoformat().replace("+00:00", "Z")
        payload["extraComputations"] = ["TRAFFIC_ON_POLYLINE"]

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

    limit = 3 if compute_alternatives else 1
    return [
        _build_route_option(index, route)
        for index, route in enumerate(routes[:limit])
    ]
