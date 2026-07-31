from dataclasses import asdict

import pytest

from app.weather.service import WeatherService


@pytest.mark.parametrize(
    ("severity", "label", "time_multiplier", "price_multiplier"),
    [
        (0, "Clear", 1.0, 1.0),
        (1, "Light rain", 1.08, 1.03),
        (2, "Heavy rain", 1.18, 1.07),
        (3, "Severe", 1.32, 1.12),
    ],
)
def test_weather_state_matches_documented_scenarios(
    severity: int,
    label: str,
    time_multiplier: float,
    price_multiplier: float,
) -> None:
    state = WeatherService().state(severity)

    assert asdict(state) == {
        "severity": severity,
        "label": label,
        "time_multiplier": time_multiplier,
        "price_multiplier": price_multiplier,
        "source": "Simulated fallback",
    }


@pytest.mark.parametrize(("requested", "clamped"), [(-1, 0), (9, 3)])
def test_weather_severity_is_clamped(requested: int, clamped: int) -> None:
    assert WeatherService().state(requested).severity == clamped


def test_weather_multipliers_increase_with_severity() -> None:
    states = [WeatherService().state(severity) for severity in range(4)]

    assert all(
        later.time_multiplier > earlier.time_multiplier
        for earlier, later in zip(states, states[1:])
    )
    assert all(
        later.price_multiplier > earlier.price_multiplier
        for earlier, later in zip(states, states[1:])
    )
