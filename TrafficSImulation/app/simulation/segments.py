from dataclasses import dataclass

from app.config import (
    BASE_LANE_CAPACITY,
    MINIMUM_CRAWL_SPEED_MPH,
    MINIMUM_SEGMENT_LENGTH_MILES,
    ROUTE_CONGESTION_INDEX_STEP,
    SEGMENT_CONGESTION_INDEX_STEP,
    SEGMENT_CONGESTION_MAX,
    SEGMENT_CONGESTION_MIN,
    SEGMENT_COUNT_MAX,
    SEGMENT_LANE_COUNTS,
    SEGMENT_NAME_MAX_LENGTH,
    SEGMENT_SPEED_LIMITS_MPH,
)
from app.map.types import LatLngPoint, RawRoute
from app.simulation.traffic import bpr_adjusted_time


@dataclass(frozen=True, slots=True)
class RoadSegment:
    name: str
    length_miles: float
    lanes: int
    speed_limit_mph: int
    average_speed_mph: float
    volume_vehicles_hour: int
    congestion: float
    capacity_vehicles_hour: int
    free_flow_minutes: float
    adjusted_minutes: float
    traffic_ratio: float
    polyline: list[LatLngPoint]


class SegmentBuilder:
    def build(
        self,
        route: RawRoute,
        congestion: int,
        route_index: int,
    ) -> list[RoadSegment]:
        steps = route.steps[:SEGMENT_COUNT_MAX]
        if not steps:
            steps = [_synthetic_step(route)]

        slice_indices = _polyline_slice_indices(route.polyline, steps)
        return [
            self._build_segment(
                route,
                step,
                congestion,
                route_index,
                segment_index,
                slice_indices[segment_index],
            )
            for segment_index, step in enumerate(steps)
        ]

    def _build_segment(
        self,
        route: RawRoute,
        step: dict[str, object],
        congestion: int,
        route_index: int,
        segment_index: int,
        slice_indices: tuple[int, int],
    ) -> RoadSegment:
        speed_limit = SEGMENT_SPEED_LIMITS_MPH[segment_index]
        lanes = SEGMENT_LANE_COUNTS[segment_index]
        capacity = lanes * BASE_LANE_CAPACITY
        local_congestion = max(
            SEGMENT_CONGESTION_MIN,
            min(
                SEGMENT_CONGESTION_MAX,
                congestion
                + segment_index * SEGMENT_CONGESTION_INDEX_STEP
                - route_index * ROUTE_CONGESTION_INDEX_STEP,
            ),
        )
        volume = round(capacity * local_congestion / 100)
        length_miles = max(
            MINIMUM_SEGMENT_LENGTH_MILES,
            round(_number(step.get("distance_meters")) / 1609.344, 1),
        )
        static_seconds = _optional_number(
            step.get("static_duration_seconds")
        )
        if static_seconds is not None and static_seconds > 0:
            free_flow_minutes = static_seconds / 60
        else:
            free_flow_minutes = length_miles / speed_limit * 60

        adjusted_minutes = bpr_adjusted_time(
            free_flow_minutes,
            volume,
            capacity,
        )
        average_speed = max(
            MINIMUM_CRAWL_SPEED_MPH,
            length_miles / (adjusted_minutes / 60),
        )
        start_index, end_index = slice_indices
        step_polyline = step.get("polyline")
        if isinstance(step_polyline, list) and len(step_polyline) >= 2:
            polyline = step_polyline
        else:
            polyline = route.polyline[start_index:end_index + 1]

        return RoadSegment(
            name=_segment_name(step, segment_index),
            length_miles=length_miles,
            lanes=lanes,
            speed_limit_mph=speed_limit,
            average_speed_mph=round(average_speed, 1),
            volume_vehicles_hour=volume,
            congestion=round(local_congestion / 100, 2),
            capacity_vehicles_hour=capacity,
            free_flow_minutes=round(free_flow_minutes, 4),
            adjusted_minutes=round(adjusted_minutes, 4),
            traffic_ratio=_traffic_ratio(step, route.traffic_ratio),
            polyline=polyline,
        )


def _synthetic_step(route: RawRoute) -> dict[str, object]:
    return {
        "distance_meters": route.distance_miles * 1609.344,
        "duration_seconds": route.duration_seconds,
        "static_duration_seconds": route.static_duration_seconds,
        "polyline": route.polyline,
        "instruction": "Route segment 1",
    }


def _polyline_slice_indices(
    polyline: list[LatLngPoint],
    steps: list[dict[str, object]],
) -> list[tuple[int, int]]:
    if len(polyline) < 2:
        return [(0, max(0, len(polyline) - 1)) for _ in steps]

    distances = [
        max(0.0, _number(step.get("distance_meters")))
        for step in steps
    ]
    total_distance = sum(distances) or 1.0
    boundaries = [0]
    cumulative_distance = 0.0
    for distance in distances:
        cumulative_distance += distance
        boundary = round(
            cumulative_distance / total_distance * (len(polyline) - 1)
        )
        boundaries.append(min(len(polyline) - 1, boundary))

    slices: list[tuple[int, int]] = []
    for index in range(len(steps)):
        start_index = boundaries[index]
        end_index = boundaries[index + 1]
        if end_index <= start_index:
            end_index = min(len(polyline) - 1, start_index + 1)
        slices.append((start_index, end_index))
    return slices


def _traffic_ratio(
    step: dict[str, object],
    route_ratio: float,
) -> float:
    duration = _optional_number(step.get("duration_seconds"))
    static_duration = _optional_number(
        step.get("static_duration_seconds")
    )
    if (
        duration is not None
        and static_duration is not None
        and static_duration > 0
    ):
        return round(duration / static_duration, 4)
    return round(route_ratio, 4)


def _segment_name(
    step: dict[str, object],
    segment_index: int,
) -> str:
    instruction = str(step.get("instruction") or "").strip()
    return (
        instruction[:SEGMENT_NAME_MAX_LENGTH]
        or f"Segment {segment_index + 1}"
    )


def _number(value: object) -> float:
    number = _optional_number(value)
    return number if number is not None else 0.0


def _optional_number(value: object) -> float | None:
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    return None
