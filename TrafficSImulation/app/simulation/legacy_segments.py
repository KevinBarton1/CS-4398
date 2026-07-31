from app.config import (
    BASE_LANE_CAPACITY,
    MINIMUM_CRAWL_SPEED_MPH,
    MINIMUM_SEGMENT_LENGTH_MILES,
    ROUTE_CONGESTION_INDEX_STEP,
    SEGMENT_CONGESTION_INDEX_STEP,
    SEGMENT_CONGESTION_MAX,
    SEGMENT_CONGESTION_MIN,
    SEGMENT_LANE_COUNTS,
    SEGMENT_NAME_MAX_LENGTH,
    SEGMENT_SPEED_LIMITS_MPH,
)
from app.map.polyline import decode_polyline
from app.simulation.segments import RoadSegment
from app.simulation.traffic import bpr_adjusted_time


def _parse_step_seconds(
    step: dict,
    prefer_static: bool = True,
) -> float:
    keys = (
        ("staticDuration", "duration")
        if prefer_static
        else ("duration", "staticDuration")
    )
    for key in keys:
        value = step.get(key)
        if isinstance(value, str) and value.endswith("s"):
            return float(value[:-1])
        if isinstance(value, dict) and "seconds" in value:
            return float(value["seconds"])
    return 0.0


def _step_traffic_ratio(
    step: dict,
    route_traffic_ratio: float = 1.0,
) -> float:
    static_seconds = _parse_step_seconds(step, prefer_static=True)
    duration_seconds = _parse_step_seconds(step, prefer_static=False)
    if static_seconds > 0 and duration_seconds > 0:
        return round(duration_seconds / static_seconds, 4)
    return route_traffic_ratio


def _polyline_slice_indices(
    route_polyline: list,
    step_distances: list[float],
) -> list[tuple[int, int]]:
    if len(route_polyline) < 2 or not step_distances:
        return [(0, max(0, len(route_polyline) - 1))]
    total_distance = sum(step_distances) or 1.0
    cumulative = 0.0
    boundaries = [0]
    for distance in step_distances:
        cumulative += distance / total_distance
        boundaries.append(
            min(
                len(route_polyline) - 1,
                round(cumulative * (len(route_polyline) - 1)),
            )
        )
    slices = []
    for index in range(len(step_distances)):
        start = boundaries[index]
        end = boundaries[index + 1]
        if end <= start:
            end = min(len(route_polyline) - 1, start + 1)
        slices.append((start, end))
    return slices


def _segment_polyline(
    step: dict,
    route_polyline: list,
    start_index: int,
    end_index: int,
) -> list:
    encoded = (step.get("polyline") or {}).get("encodedPolyline") or ""
    if encoded:
        decoded = decode_polyline(encoded)
        if decoded:
            return decoded
    if route_polyline and end_index > start_index:
        return route_polyline[start_index:end_index + 1]
    return route_polyline[:2] if route_polyline else []


def create_segments(
    route: dict,
    congestion: int,
    route_index: int,
) -> list[RoadSegment]:
    route_polyline = route.get("polyline") or []
    steps = (route.get("google_steps") or [])[:2]
    if not steps:
        return _fallback_segments(
            route,
            congestion,
            route_index,
            route_polyline,
        )

    step_distances = [step.get("distanceMeters") or 0 for step in steps]
    slice_indices = _polyline_slice_indices(
        route_polyline,
        step_distances,
    )
    segments = []
    for index, step in enumerate(steps):
        length = round(
            (step.get("distanceMeters") or 0) / 1609.344,
            1,
        ) or MINIMUM_SEGMENT_LENGTH_MILES
        speed_limit = SEGMENT_SPEED_LIMITS_MPH[index]
        lanes = SEGMENT_LANE_COUNTS[index]
        free_flow = (
            _parse_step_seconds(step, prefer_static=True) / 60
            or length / speed_limit * 60
        )
        segments.append(
            _legacy_segment(
                step,
                route_polyline,
                route.get("traffic_ratio") or 1.0,
                congestion,
                route_index,
                index,
                length,
                lanes,
                speed_limit,
                free_flow,
                slice_indices[index],
            )
        )
    return segments


def _legacy_segment(
    step: dict,
    route_polyline: list,
    route_ratio: float,
    congestion: int,
    route_index: int,
    index: int,
    length: float,
    lanes: int,
    speed_limit: int,
    free_flow: float,
    slice_indices: tuple[int, int],
) -> RoadSegment:
    local_congestion = max(
        SEGMENT_CONGESTION_MIN,
        min(
            SEGMENT_CONGESTION_MAX,
            congestion
            + index * SEGMENT_CONGESTION_INDEX_STEP
            - route_index * ROUTE_CONGESTION_INDEX_STEP,
        ),
    )
    capacity = lanes * BASE_LANE_CAPACITY
    flow = round(capacity * local_congestion / 100)
    adjusted = bpr_adjusted_time(free_flow, flow, capacity)
    average_speed = max(
        MINIMUM_CRAWL_SPEED_MPH,
        length / (adjusted / 60),
    )
    instruction = (
        (step.get("navigationInstruction") or {}).get("instructions")
        or f"Segment {index + 1}"
    )
    start_index, end_index = slice_indices
    return RoadSegment(
        name=instruction[:SEGMENT_NAME_MAX_LENGTH],
        length_miles=length,
        lanes=lanes,
        speed_limit_mph=speed_limit,
        average_speed_mph=round(average_speed, 1),
        volume_vehicles_hour=flow,
        congestion=round(local_congestion / 100, 2),
        capacity_vehicles_hour=capacity,
        free_flow_minutes=round(free_flow, 4),
        adjusted_minutes=round(adjusted, 4),
        traffic_ratio=_step_traffic_ratio(step, route_ratio),
        polyline=_segment_polyline(
            step,
            route_polyline,
            start_index,
            end_index,
        ),
    )


def _fallback_segments(
    route: dict,
    congestion: int,
    route_index: int,
    route_polyline: list,
) -> list[RoadSegment]:
    length = route["distance_miles"]
    return [
        _legacy_segment(
            {},
            route_polyline,
            route.get("traffic_ratio") or 1.0,
            congestion,
            route_index,
            0,
            round(length, 1),
            SEGMENT_LANE_COUNTS[0],
            SEGMENT_SPEED_LIMITS_MPH[0],
            length / SEGMENT_SPEED_LIMITS_MPH[0] * 60,
            (0, max(0, len(route_polyline) - 1)),
        )
    ]
