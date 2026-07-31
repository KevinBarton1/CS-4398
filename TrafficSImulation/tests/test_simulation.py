from dataclasses import asdict

import pytest

from app.map.types import LatLngPoint, RawRoute
from app.simulation.segments import SegmentBuilder
from app.simulation.traffic import (
    bpr_adjusted_time,
    time_of_day_factor,
)


def _sample_route(steps: list[dict[str, object]] | None = None) -> RawRoute:
    return RawRoute(
        id="route-1",
        distance_miles=7.0,
        duration_seconds=900.0,
        static_duration_seconds=720.0,
        traffic_ratio=1.25,
        polyline=[
            LatLngPoint(lat=30.2672, lng=-97.7431),
            LatLngPoint(lat=30.2500, lng=-97.7200),
            LatLngPoint(lat=30.2300, lng=-97.6900),
            LatLngPoint(lat=30.2150, lng=-97.6750),
            LatLngPoint(lat=30.1975, lng=-97.6664),
        ],
        traffic_intervals=[],
        steps=steps or [],
    )


def test_t12_bpr_zero_flow_is_exact_identity() -> None:
    assert bpr_adjusted_time(10.0, 0.0, 1000.0) == 10.0


def test_t12_bpr_is_monotonic_and_matches_capacity_value() -> None:
    adjusted = [
        bpr_adjusted_time(10.0, flow, 1000.0)
        for flow in [0.0, 250.0, 500.0, 750.0, 1000.0, 1200.0]
    ]

    assert adjusted == sorted(adjusted)
    assert adjusted[-2] == pytest.approx(11.5)


@pytest.mark.parametrize("capacity", [0.0, -1.0])
def test_t12_bpr_rejects_non_positive_capacity(capacity: float) -> None:
    with pytest.raises(ValueError):
        bpr_adjusted_time(10.0, 100.0, capacity)


def test_t13_time_of_day_factor_covers_every_band() -> None:
    assert time_of_day_factor(8) == 1.22
    assert time_of_day_factor(17) == 1.22
    assert time_of_day_factor(3) == 0.92
    assert time_of_day_factor(22) == 0.92
    assert time_of_day_factor(12) == 1.0
    assert time_of_day_factor(-3) == 0.92
    assert time_of_day_factor(30) == 0.92


def test_t13_time_of_day_factor_matches_all_24_hours() -> None:
    expected = [
        0.92,
        0.92,
        0.92,
        0.92,
        0.92,
        0.92,
        1.0,
        1.22,
        1.22,
        1.22,
        1.0,
        1.0,
        1.0,
        1.0,
        1.0,
        1.0,
        1.22,
        1.22,
        1.22,
        1.0,
        1.0,
        1.0,
        0.92,
        0.92,
    ]

    assert [time_of_day_factor(hour) for hour in range(24)] == expected


def test_t14_worked_segment_and_field_set_match_contract() -> None:
    route = _sample_route(
        [
            {
                "distance_meters": 3218,
                "duration_seconds": 360.0,
                "static_duration_seconds": 300.0,
                "polyline": [],
                "instruction": "South Congress Avenue",
            },
            {
                "distance_meters": 8046,
                "duration_seconds": 480.0,
                "static_duration_seconds": 420.0,
                "polyline": [],
                "instruction": "Airport Boulevard",
            },
        ]
    )

    segments = SegmentBuilder().build(route, congestion=56, route_index=0)

    assert len(segments) == 2
    worked = segments[1]
    assert set(asdict(worked)) == {
        "name",
        "length_miles",
        "lanes",
        "speed_limit_mph",
        "average_speed_mph",
        "volume_vehicles_hour",
        "congestion",
        "capacity_vehicles_hour",
        "free_flow_minutes",
        "adjusted_minutes",
        "traffic_ratio",
        "polyline",
    }
    assert worked.name == "Airport Boulevard"
    assert worked.length_miles == 5.0
    assert worked.lanes == 4
    assert worked.speed_limit_mph == 55
    assert worked.capacity_vehicles_hour == 2080
    assert worked.volume_vehicles_hour == 1394
    assert worked.congestion == 0.67
    assert worked.free_flow_minutes == 7.0
    assert worked.adjusted_minutes == pytest.approx(7.2118)
    assert worked.average_speed_mph == 41.6
    assert worked.traffic_ratio == pytest.approx(1.1429)
    assert worked.polyline == route.polyline[1:]


def test_t14_segment_count_and_statistics_respect_bounds() -> None:
    steps = [
        {
            "distance_meters": 1609.344,
            "duration_seconds": None,
            "static_duration_seconds": None,
            "polyline": [],
            "instruction": f"Segment {index + 1}",
        }
        for index in range(4)
    ]
    route = _sample_route(steps)

    low = SegmentBuilder().build(route, congestion=0, route_index=10)
    high = SegmentBuilder().build(route, congestion=100, route_index=0)

    assert len(low) == 2
    assert len(high) == 2
    assert [segment.congestion for segment in low] == [0.05, 0.05]
    assert [segment.congestion for segment in high] == [0.98, 0.98]
    for segment in low + high:
        assert segment.capacity_vehicles_hour == segment.lanes * 520
        assert (
            segment.volume_vehicles_hour
            <= segment.capacity_vehicles_hour
        )
        assert segment.adjusted_minutes >= segment.free_flow_minutes
        assert segment.average_speed_mph >= 6.0
        assert len(segment.polyline) >= 2


def test_t14_no_steps_produces_one_synthetic_segment() -> None:
    route = _sample_route()

    segments = SegmentBuilder().build(route, congestion=56, route_index=0)

    assert len(segments) == 1
    assert segments[0].name == "Route segment 1"
    assert segments[0].length_miles == 7.0
    assert segments[0].free_flow_minutes == 12.0
    assert segments[0].polyline == route.polyline


def test_t14_step_polyline_is_preferred_and_congestion_is_monotonic() -> None:
    step_polyline = [
        LatLngPoint(lat=30.2672, lng=-97.7431),
        LatLngPoint(lat=30.2600, lng=-97.7300),
    ]
    route = _sample_route(
        [
            {
                "distance_meters": 1609.344,
                "duration_seconds": 360.0,
                "static_duration_seconds": 300.0,
                "polyline": step_polyline,
                "instruction": "Congress Avenue",
            }
        ]
    )

    light = SegmentBuilder().build(route, congestion=10, route_index=0)[0]
    heavy = SegmentBuilder().build(route, congestion=90, route_index=0)[0]

    assert light.polyline == step_polyline
    assert heavy.adjusted_minutes >= light.adjusted_minutes
