import re
from datetime import datetime, timezone

import httpx

from app.config import (
    GOOGLE_REGION_CODE,
    GOOGLE_ROUTES_COMPUTE_URL,
    GOOGLE_ROUTES_FIELD_MASK,
    ROUTES_TIMEOUT_SECONDS,
    ROUTE_ALTERNATIVES_MAX,
    Settings,
)
from app.map.errors import (
    MapsNotConfiguredError,
    NoRouteFoundError,
    UpstreamTimeoutError,
    UpstreamUnavailableError,
)
from app.map.polyline import decode_polyline
from app.map.retry import with_upstream_retry
from app.map.types import (
    RawRoute,
    ResolvedPlace,
    TrafficInterval,
    TrafficSpeed,
)

_DURATION_PATTERN = re.compile(r"(\d+(?:\.\d+)?)s")


class GoogleRoutesGateway:
    def __init__(
        self,
        settings: Settings,
        client: httpx.AsyncClient,
    ) -> None:
        self._settings = settings
        self._client = client

    async def compute(
        self,
        origin: ResolvedPlace,
        destination: ResolvedPlace,
        departure: datetime,
        alternatives: bool,
    ) -> list[RawRoute]:
        if not self._settings.google_maps_configured:
            raise MapsNotConfiguredError

        try:
            response = await with_upstream_retry(
                lambda: self._post_routes_request(
                    origin,
                    destination,
                    departure,
                    alternatives,
                )
            )
        except httpx.TimeoutException as error:
            raise UpstreamTimeoutError("Routes") from error
        except httpx.HTTPError as error:
            raise UpstreamUnavailableError("Routes") from error

        try:
            routes = response.json().get("routes") or []
        except (
            AttributeError,
            IndexError,
            KeyError,
            TypeError,
            ValueError,
        ) as error:
            raise UpstreamUnavailableError("Routes") from error

        if not routes:
            raise NoRouteFoundError

        limit = ROUTE_ALTERNATIVES_MAX if alternatives else 1
        try:
            return [
                _normalize_route(index, route)
                for index, route in enumerate(routes[:limit])
            ]
        except (AttributeError, TypeError, ValueError) as error:
            raise UpstreamUnavailableError("Routes") from error

    async def _post_routes_request(
        self,
        origin: ResolvedPlace,
        destination: ResolvedPlace,
        departure: datetime,
        alternatives: bool,
    ) -> httpx.Response:
        response = await self._client.post(
            GOOGLE_ROUTES_COMPUTE_URL,
            json={
                "origin": _waypoint(origin),
                "destination": _waypoint(destination),
                "travelMode": "DRIVE",
                "computeAlternativeRoutes": alternatives,
                "routingPreference": "TRAFFIC_AWARE",
                "units": "IMPERIAL",
                "regionCode": GOOGLE_REGION_CODE,
                "departureTime": _format_departure(departure),
                "extraComputations": ["TRAFFIC_ON_POLYLINE"],
            },
            headers={
                "Content-Type": "application/json",
                "X-Goog-Api-Key": self._settings.google_maps_api_key,
                "X-Goog-FieldMask": GOOGLE_ROUTES_FIELD_MASK,
            },
            timeout=ROUTES_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        return response


def _waypoint(place: ResolvedPlace) -> dict[str, object]:
    return {
        "location": {
            "latLng": {
                "latitude": place.latitude,
                "longitude": place.longitude,
            }
        }
    }


def _format_departure(departure: datetime) -> str:
    if departure.tzinfo is None:
        departure = departure.replace(tzinfo=timezone.utc)
    return (
        departure.astimezone(timezone.utc)
        .isoformat()
        .replace("+00:00", "Z")
    )


def _parse_duration(value: object) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        match = _DURATION_PATTERN.fullmatch(value.strip())
        return float(match.group(1)) if match else None
    if isinstance(value, dict) and "seconds" in value:
        seconds = value["seconds"]
        if isinstance(seconds, bool):
            return None
        try:
            return float(seconds)
        except (TypeError, ValueError):
            return None
    return None


def _normalize_route(index: int, route: dict[str, object]) -> RawRoute:
    if "distanceMeters" not in route:
        raise ValueError("Route distance is missing.")

    encoded = _encoded_polyline(route)
    if not encoded:
        raise ValueError("Route geometry is missing.")

    duration = _parse_duration(route.get("duration"))
    static_duration = _parse_duration(route.get("staticDuration"))
    traffic_ratio = 1.0
    if (
        duration is not None
        and static_duration is not None
        and static_duration > 0
    ):
        traffic_ratio = round(duration / static_duration, 4)

    return RawRoute(
        id=f"route-{index + 1}",
        distance_miles=round(
            float(route["distanceMeters"]) / 1609.344,
            1,
        ),
        duration_seconds=duration,
        static_duration_seconds=static_duration,
        traffic_ratio=traffic_ratio,
        polyline=decode_polyline(encoded),
        traffic_intervals=_extract_intervals(route),
        steps=_normalize_steps(route),
    )


def _encoded_polyline(route: dict[str, object]) -> str:
    polyline = route.get("polyline") or {}
    if not isinstance(polyline, dict):
        return ""
    encoded = polyline.get("encodedPolyline")
    return str(encoded) if encoded else ""


def _extract_intervals(
    route: dict[str, object],
) -> list[TrafficInterval]:
    intervals: list[TrafficInterval] = []
    legs = route.get("legs") or []
    if not isinstance(legs, list):
        raise TypeError("Route legs must be a list.")

    for leg in legs:
        if not isinstance(leg, dict):
            raise TypeError("Route leg must be an object.")
        advisory = leg.get("travelAdvisory") or {}
        if not isinstance(advisory, dict):
            raise TypeError("Travel advisory must be an object.")
        intervals.extend(
            _normalize_intervals(
                advisory.get("speedReadingIntervals") or []
            )
        )

    if not intervals:
        advisory = route.get("travelAdvisory") or {}
        if not isinstance(advisory, dict):
            raise TypeError("Travel advisory must be an object.")
        intervals.extend(
            _normalize_intervals(
                advisory.get("speedReadingIntervals") or []
            )
        )
    return intervals


def _normalize_intervals(items: object) -> list[TrafficInterval]:
    if not isinstance(items, list):
        raise TypeError("Speed intervals must be a list.")

    normalized: list[TrafficInterval] = []
    for item in items:
        if not isinstance(item, dict):
            raise TypeError("Speed interval must be an object.")
        end_index = item.get("endPolylinePointIndex")
        if end_index is None:
            continue
        raw_speed = item.get("speed") or TrafficSpeed.NORMAL.value
        try:
            speed = TrafficSpeed(raw_speed)
        except ValueError:
            speed = TrafficSpeed.SPEED_UNSPECIFIED
        normalized.append(
            TrafficInterval(
                start_index=int(
                    item.get("startPolylinePointIndex") or 0
                ),
                end_index=int(end_index),
                speed=speed,
            )
        )
    return normalized


def _normalize_steps(route: dict[str, object]) -> list[dict[str, object]]:
    legs = route.get("legs") or []
    if not isinstance(legs, list) or not legs:
        return []
    first_leg = legs[0]
    if not isinstance(first_leg, dict):
        raise TypeError("Route leg must be an object.")
    steps = first_leg.get("steps") or []
    if not isinstance(steps, list):
        raise TypeError("Route steps must be a list.")

    normalized: list[dict[str, object]] = []
    for step in steps:
        if not isinstance(step, dict):
            raise TypeError("Route step must be an object.")
        instruction = step.get("navigationInstruction") or {}
        if not isinstance(instruction, dict):
            instruction = {}
        step_polyline = step.get("polyline") or {}
        if not isinstance(step_polyline, dict):
            step_polyline = {}
        encoded = step_polyline.get("encodedPolyline") or ""
        normalized.append(
            {
                "distance_meters": int(step.get("distanceMeters") or 0),
                "duration_seconds": _parse_duration(step.get("duration")),
                "static_duration_seconds": _parse_duration(
                    step.get("staticDuration")
                ),
                "polyline": decode_polyline(str(encoded)) if encoded else [],
                "instruction": str(
                    instruction.get("instructions") or ""
                ),
            }
        )
    return normalized
