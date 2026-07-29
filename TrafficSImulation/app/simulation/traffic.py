from app.api.models import RoadSegment
from app.config import BASE_LANE_CAPACITY, BPR_ALPHA, BPR_BETA, MINIMUM_CRAWL_SPEED_MPH


def _parse_step_seconds(step: dict) -> float:
    for key in ("staticDuration", "duration"):
        value = step.get(key)
        if isinstance(value, str) and value.endswith("s"):
            return float(value[:-1])
        if isinstance(value, dict) and "seconds" in value:
            return float(value["seconds"])
    return 0.0


def _segments_from_google_steps(steps: list[dict], congestion: int, route_index: int) -> list[RoadSegment]:
    segments: list[RoadSegment] = []
    for index, step in enumerate(steps[:2]):
        length_miles = round((step.get("distanceMeters") or 0) / 1609.344, 1) or 0.1
        free_flow = _parse_step_seconds(step) / 60 or length_miles / 45 * 60
        local_congestion = max(5, min(98, congestion + (index * 11) - (route_index * 9)))
        speed_limit = (45, 55)[index]
        lanes = (3, 4)[index]
        capacity = lanes * BASE_LANE_CAPACITY
        flow = round(capacity * local_congestion / 100)
        adjusted = bpr_adjusted_time(free_flow, flow, capacity)
        average_speed = max(MINIMUM_CRAWL_SPEED_MPH, length_miles / (adjusted / 60))
        instruction = (step.get("navigationInstruction") or {}).get("instructions") or f"Segment {index + 1}"
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


def create_segments(route, congestion, route_index):
    google_steps = route.get("google_steps")
    if google_steps:
        google_segments = _segments_from_google_steps(google_steps, congestion, route_index)
        if google_segments:
            return google_segments

    segments = []
    lengths = (route["distance_miles"] * 0.47, route["distance_miles"] * 0.53)
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
        ))
    return segments
