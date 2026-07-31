from datetime import datetime, timedelta
from unittest.mock import patch
from zoneinfo import ZoneInfo

import pytest

from app.api.mode_policy import (
    AUSTIN_TIMEZONE,
    ROUTING_PREFERENCE,
    RealTimeModePolicy,
    SimulatedModePolicy,
    resolve_mode_policy,
)
from app.api.models import PlanRequest, RoadSegment, Scenario, WeatherState
from app.config import (
    DATA_SOURCE_REALTIME,
    DATA_SOURCE_SIMULATED,
    ETA_FALLBACK_BUFFER_MINUTES,
    NOTICE_REALTIME,
    NOTICE_SIMULATED,
    ROUTE_ALTERNATIVES_MAX,
)
from app.map.types import LatLngPoint, RawRoute
from app.simulation.traffic import time_of_day_factor

FIXED_NOW = datetime(2026, 7, 30, 14, 30, tzinfo=AUSTIN_TIMEZONE)


def _request(**overrides: object) -> PlanRequest:
    payload = {
        "origin": "Downtown Austin",
        "destination": "Austin Airport",
        "mode": "simulated",
        "hour": 17,
        "weather": 2,
        "congestion": 56,
    }
    payload.update(overrides)
    return PlanRequest(**payload)


def _weather(time_multiplier: float = 1.18) -> WeatherState:
    return WeatherState(
        severity=2,
        label="Heavy rain",
        time_multiplier=time_multiplier,
        price_multiplier=1.07,
        source="Simulated fallback",
    )


def _route(
    *,
    duration_seconds: float | None = 1200.0,
    static_duration_seconds: float | None = 900.0,
) -> RawRoute:
    return RawRoute(
        id="route-1",
        distance_miles=7.0,
        duration_seconds=duration_seconds,
        static_duration_seconds=static_duration_seconds,
        traffic_ratio=1.25,
        polyline=[LatLngPoint(lat=30.2672, lng=-97.7431)],
        traffic_intervals=[],
        steps=[],
    )


def _segment(adjusted_minutes: float = 12.5) -> RoadSegment:
    return RoadSegment(
        name="I-35",
        length_miles=3.2,
        lanes=3,
        speed_limit_mph=55,
        average_speed_mph=42.0,
        volume_vehicles_hour=1200,
        congestion=0.45,
        capacity_vehicles_hour=1560,
        free_flow_minutes=4.2,
        adjusted_minutes=adjusted_minutes,
        traffic_ratio=1.15,
        polyline=[LatLngPoint(lat=30.2672, lng=-97.7431)],
    )


@pytest.mark.parametrize(
    ("mode", "policy_type"),
    [
        ("simulated", SimulatedModePolicy),
        ("realtime", RealTimeModePolicy),
    ],
)
def test_resolve_mode_policy_maps_valid_modes(
    mode: str,
    policy_type: type,
) -> None:
    policy = resolve_mode_policy(mode)

    assert isinstance(policy, policy_type)
    assert policy.mode == mode


def test_resolve_mode_policy_rejects_unknown_mode() -> None:
    with pytest.raises(ValueError, match="Unsupported planning mode"):
        resolve_mode_policy("offline")


@pytest.mark.parametrize(
    ("policy", "alternatives", "scenario_applied"),
    [
        (SimulatedModePolicy(), ROUTE_ALTERNATIVES_MAX, True),
        (RealTimeModePolicy(), 1, False),
    ],
)
def test_policy_alternatives_and_scenario_applied(
    policy,
    alternatives: int,
    scenario_applied: bool,
) -> None:
    assert policy.alternatives == alternatives
    assert policy.scenario_applied is scenario_applied


@patch("app.api.mode_policy.datetime")
def test_simulated_effective_scenario_passes_request_values(mock_datetime) -> None:
    mock_datetime.now.return_value = FIXED_NOW
    policy = SimulatedModePolicy()
    request = _request(hour=9, weather=3, congestion=72)

    scenario = policy.effective_scenario(request)

    assert scenario == Scenario(hour=9, weather=3, congestion=72)


@patch("app.api.mode_policy.datetime")
def test_realtime_effective_scenario_discards_request_values(mock_datetime) -> None:
    mock_datetime.now.return_value = FIXED_NOW
    policy = RealTimeModePolicy()
    request = _request(hour=9, weather=3, congestion=72)

    scenario = policy.effective_scenario(request)

    assert scenario == Scenario(hour=14, weather=0, congestion=0)


@pytest.mark.parametrize(
    ("now", "target_hour", "expected"),
    [
        (
            datetime(2026, 7, 30, 10, 0, tzinfo=AUSTIN_TIMEZONE),
            17,
            datetime(2026, 7, 30, 17, 0, tzinfo=AUSTIN_TIMEZONE),
        ),
        (
            datetime(2026, 7, 30, 17, 30, tzinfo=AUSTIN_TIMEZONE),
            17,
            datetime(2026, 7, 31, 17, 0, tzinfo=AUSTIN_TIMEZONE),
        ),
        (
            datetime(2026, 7, 30, 23, 0, tzinfo=AUSTIN_TIMEZONE),
            6,
            datetime(2026, 7, 31, 6, 0, tzinfo=AUSTIN_TIMEZONE),
        ),
    ],
)
def test_simulated_departure_time_is_next_occurrence_of_hour(
    now: datetime,
    target_hour: int,
    expected: datetime,
) -> None:
    policy = SimulatedModePolicy()
    scenario = Scenario(hour=target_hour, weather=0, congestion=0)

    with patch("app.api.mode_policy.datetime") as mock_datetime:
        mock_datetime.now.return_value = now
        mock_datetime.side_effect = lambda *args, **kwargs: datetime(*args, **kwargs)

        departure = policy.departure_time(scenario)

    assert departure == expected


@patch("app.api.mode_policy.datetime")
def test_realtime_departure_time_is_now(mock_datetime) -> None:
    mock_datetime.now.return_value = FIXED_NOW
    policy = RealTimeModePolicy()

    departure = policy.departure_time(
        Scenario(hour=17, weather=0, congestion=0)
    )

    assert departure == FIXED_NOW
    mock_datetime.now.assert_called_once_with(AUSTIN_TIMEZONE)


@pytest.mark.parametrize(
    "policy",
    [SimulatedModePolicy(), RealTimeModePolicy()],
)
def test_both_policies_use_traffic_aware_routing(policy) -> None:
    assert policy.routing_preference() == ROUTING_PREFERENCE == "TRAFFIC_AWARE"


def test_simulated_adjusted_eta_uses_traffic_aware_duration_and_weather() -> None:
    policy = SimulatedModePolicy()

    eta = policy.adjusted_eta(
        _route(duration_seconds=1200.0),
        _weather(time_multiplier=1.18),
        [_segment()],
    )

    assert eta == pytest.approx((1200.0 / 60) * 1.18)


def test_simulated_adjusted_eta_falls_back_to_static_duration() -> None:
    policy = SimulatedModePolicy()

    eta = policy.adjusted_eta(
        _route(duration_seconds=None, static_duration_seconds=900.0),
        _weather(time_multiplier=1.08),
        [_segment()],
    )

    assert eta == pytest.approx((900.0 / 60) * 1.08)


def test_simulated_adjusted_eta_falls_back_to_segment_sum_plus_buffer() -> None:
    policy = SimulatedModePolicy()
    segments = [_segment(12.5), _segment(8.0)]

    eta = policy.adjusted_eta(
        _route(duration_seconds=None, static_duration_seconds=None),
        _weather(time_multiplier=1.0),
        segments,
    )

    expected_base = 12.5 + 8.0 + ETA_FALLBACK_BUFFER_MINUTES
    assert eta == pytest.approx(expected_base)


def test_realtime_adjusted_eta_uses_traffic_aware_duration_without_factors() -> None:
    policy = RealTimeModePolicy()

    eta = policy.adjusted_eta(
        _route(duration_seconds=1200.0),
        _weather(time_multiplier=1.18),
        [_segment()],
    )

    assert eta == pytest.approx(1200.0 / 60)


def test_realtime_adjusted_eta_falls_back_to_static_duration() -> None:
    policy = RealTimeModePolicy()

    eta = policy.adjusted_eta(
        _route(duration_seconds=None, static_duration_seconds=900.0),
        _weather(),
        [_segment()],
    )

    assert eta == pytest.approx(900.0 / 60)


def test_realtime_adjusted_eta_falls_back_to_segment_sum_plus_buffer() -> None:
    policy = RealTimeModePolicy()
    segments = [_segment(10.0), _segment(6.0)]

    eta = policy.adjusted_eta(
        _route(duration_seconds=None, static_duration_seconds=None),
        _weather(),
        segments,
    )

    assert eta == pytest.approx(10.0 + 6.0 + ETA_FALLBACK_BUFFER_MINUTES)


def test_simulated_pricing_time_multiplier_is_one() -> None:
    policy = SimulatedModePolicy()

    assert policy.pricing_time_multiplier(
        Scenario(hour=8, weather=2, congestion=56)
    ) == 1.0


@patch("app.api.mode_policy.datetime")
def test_realtime_pricing_time_multiplier_uses_time_of_day_factor(
    mock_datetime,
) -> None:
    mock_datetime.now.return_value = datetime(
        2026,
        7,
        30,
        8,
        15,
        tzinfo=AUSTIN_TIMEZONE,
    )
    policy = RealTimeModePolicy()
    scenario = policy.effective_scenario(_request())

    assert policy.pricing_time_multiplier(scenario) == time_of_day_factor(8)


@pytest.mark.parametrize(
    ("policy", "data_source", "notice"),
    [
        (
            SimulatedModePolicy(),
            DATA_SOURCE_SIMULATED,
            NOTICE_SIMULATED,
        ),
        (
            RealTimeModePolicy(),
            DATA_SOURCE_REALTIME,
            NOTICE_REALTIME,
        ),
    ],
)
def test_policy_data_source_and_notice_literals(
    policy,
    data_source: str,
    notice: str,
) -> None:
    assert policy.data_source() == data_source
    assert policy.notice() == notice
