from app.api.models import RoadSegment
from app.config import BASE_LANE_CAPACITY, BPR_ALPHA, BPR_BETA, MINIMUM_CRAWL_SPEED_MPH
from app.map.polyline import decode_polyline


def _parse_step_seconds(step: dict, prefer_static: bool = True) -> float:
    keys = ("staticDuration", "duration") if prefer_static else ("duration", "staticDuration")
    for key in keys:
        value = step.get(key)
        if isinstance(value, str) and value.endswith("s"):
            return float(value[:-1])
        if isinstance(value, dict) and "seconds" in value:
            return float(value["seconds"])
    return 0.0


def _step_traffic_ratio(step: dict, route_traffic_ratio: float = 1.0) -> float:
    static_seconds = _parse_step_seconds(step, prefer_static=True)
    duration_seconds = _parse_step_seconds(step, prefer_static=False)
    if static_seconds > 0 and duration_seconds > 0:
        return round(duration_seconds / static_seconds, 4)
    return route_traffic_ratio


def _segment_polyline(step: dict, route_polyline: list[dict], start_index: int, end_index: int) -> list[dict]:
    encoded = (step.get("polyline") or {}).get("encodedPolyline") or ""
    if encoded:
        decoded = decode_polyline(encoded)
        if decoded:
            return decoded
    if route_polyline and end_index > start_index:
        return route_polyline[start_index:end_index + 1]
    return route_polyline[:2] if route_polyline else []


def _polyline_slice_indices(route_polyline: list[dict], step_distances: list[float]) -> list[tuple[int, int]]:
    if len(route_polyline) < 2 or not step_distances:
        return [(0, max(0, len(route_polyline) - 1))]

    total_distance = sum(step_distances) or 1.0
    cumulative = 0.0
    boundaries = [0]
    for distance in step_distances:
        cumulative += distance / total_distance
        boundaries.append(min(len(route_polyline) - 1, round(cumulative * (len(route_polyline) - 1))))

    slices: list[tuple[int, int]] = []
    for index in range(len(step_distances)):
        start = boundaries[index]
        end = boundaries[index + 1] if index + 1 < len(boundaries) else len(route_polyline) - 1
        if end <= start:
            end = min(len(route_polyline) - 1, start + 1)
        slices.append((start, end))
    return slices


def _segments_from_google_steps(
    steps: list[dict],
    congestion: int,
    route_index: int,
    route_polyline: list[dict],
    route_traffic_ratio: float = 1.0,
) -> list[RoadSegment]:
    segments: list[RoadSegment] = []
    step_distances = [(step.get("distanceMeters") or 0) for step in steps[:2]]
    slice_indices = _polyline_slice_indices(route_polyline, step_distances)

    for index, step in enumerate(steps[:2]):
        length_miles = round((step.get("distanceMeters") or 0) / 1609.344, 1) or 0.1
        free_flow = _parse_step_seconds(step, prefer_static=True) / 60 or length_miles / 45 * 60
        local_congestion = max(5, min(98, congestion + (index * 11) - (route_index * 9)))
        speed_limit = (45, 55)[index]
        lanes = (3, 4)[index]
        capacity = lanes * BASE_LANE_CAPACITY
        flow = round(capacity * local_congestion / 100)
        adjusted = bpr_adjusted_time(free_flow, flow, capacity)
        average_speed = max(MINIMUM_CRAWL_SPEED_MPH, length_miles / (adjusted / 60))
        instruction = (step.get("navigationInstruction") or {}).get("instructions") or f"Segment {index + 1}"
        start_index, end_index = slice_indices[index] if index < len(slice_indices) else (0, max(0, len(route_polyline) - 1))
        segments.append(RoadSegment(
            name=instruction[:80],
            length_miles=length_miles,
            lanes=lanes,
            speed_limit_mph=speed_limit,
            average_speed_mph=round(average_speed, 1),
            volume_vehicles_hour=flow,
            congestion=round(local_congestion / 100, 2),
            capacity_vehicles_hour=capacity,
            free_flow_minutes=round(free_flow, 4),
            adjusted_minutes=round(adjusted, 4),
            traffic_ratio=_step_traffic_ratio(step, route_traffic_ratio),
            polyline=_segment_polyline(step, route_polyline, start_index, end_index),
        ))
    return segments or []


def time_of_day_factor(hour):
    hour = max(0, min(23, int(hour)))
    if 7 <= hour <= 9 or 16 <= hour <= 18:
        return 1.22
    if hour < 6 or hour >= 22:
        return 0.92
    return 1.0


def bpr_adjusted_time(free_flow_minutes, flow, capacity):
    """Bureau of Public Roads link-performance function."""
    if capacity <= 0:
        raise ValueError("Road capacity must be positive.")
    return free_flow_minutes * (1 + BPR_ALPHA * (flow / capacity) ** BPR_BETA)


def _fallback_segment_polyline(route_polyline: list[dict], index: int) -> list[dict]:
    if len(route_polyline) < 2:
        return route_polyline
    midpoint = max(1, len(route_polyline) // 2)
    if index == 0:
        return route_polyline[:midpoint + 1]
    return route_polyline[midpoint:]


def create_segments(route, congestion, route_index):
    route_polyline = route.get("polyline") or []
    google_steps = route.get("google_steps")
    if google_steps:
        google_segments = _segments_from_google_steps(
            google_steps, congestion, route_index, route_polyline,
            route.get("traffic_ratio") or 1.0,
        )
        if google_segments:
            return google_segments

    segments = []
    lengths = (route["distance_miles"] * 0.47, route["distance_miles"] * 0.53)
    route_traffic_ratio = route.get("traffic_ratio") or 1.0
    for index, (name, length) in enumerate(zip(route["road_names"], lengths)):
        local_congestion = max(5, min(98, congestion + (index * 11) - (route_index * 9)))
        speed_limit = (45, 55)[index]
        lanes = (3, 4)[index]
        capacity = lanes * BASE_LANE_CAPACITY
        flow = round(capacity * local_congestion / 100)
        free_flow = length / speed_limit * 60
        adjusted = bpr_adjusted_time(free_flow, flow, capacity)
        average_speed = max(MINIMUM_CRAWL_SPEED_MPH, length / (adjusted / 60))
        segments.append(RoadSegment(
            name=name,
            length_miles=round(length, 1),
            lanes=lanes,
            speed_limit_mph=speed_limit,
            average_speed_mph=round(average_speed, 1),
            volume_vehicles_hour=flow,
            congestion=round(local_congestion / 100, 2),
            capacity_vehicles_hour=capacity,
            free_flow_minutes=round(free_flow, 4),
            adjusted_minutes=round(adjusted, 4),
            traffic_ratio=route_traffic_ratio,
            polyline=_fallback_segment_polyline(route_polyline, index),
        ))
    return segments
