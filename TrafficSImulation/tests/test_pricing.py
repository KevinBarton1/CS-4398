from dataclasses import asdict

import pytest

from app.pricing.model import PricingModel


@pytest.mark.parametrize(
    (
        "distance_miles",
        "minutes",
        "congestion_score",
        "weather_multiplier",
        "time_multiplier",
        "route_subtotal",
        "traffic_multiplier",
        "unrounded_total",
        "estimated_price",
    ),
    [
        (12.4, 24.8, 56, 1.03, 1.0, 25.76, 1.112, 29.5044736, 29.50),
        (12.4, 22.0, 4, 1.0, 1.22, 24.892, 1.008, 30.61118592, 30.61),
        (0.6, 3.0, 4, 1.0, 1.0, 3.898, 1.008, 7.50, 7.50),
    ],
)
def test_pricing_matches_documented_worked_examples(
    distance_miles: float,
    minutes: float,
    congestion_score: int,
    weather_multiplier: float,
    time_multiplier: float,
    route_subtotal: float,
    traffic_multiplier: float,
    unrounded_total: float,
    estimated_price: float,
) -> None:
    estimate = PricingModel().estimate(
        distance_miles,
        minutes,
        congestion_score,
        weather_multiplier,
        time_multiplier,
    )

    assert estimate.estimated_price == estimated_price
    assert estimate.price_factors.route_subtotal == pytest.approx(route_subtotal)
    assert estimate.price_factors.traffic_multiplier == pytest.approx(
        traffic_multiplier
    )
    assert estimate.price_factors.weather_multiplier == weather_multiplier
    assert estimate.price_factors.time_multiplier == time_multiplier
    assert estimate.price_factors.unrounded_total == pytest.approx(
        unrounded_total
    )


def test_price_factors_reproduce_the_fare() -> None:
    estimate = PricingModel().estimate(12.4, 24.8, 56, 1.03, 1.0)
    factors = estimate.price_factors
    reproduced = max(
        7.50,
        factors.route_subtotal
        * factors.traffic_multiplier
        * factors.weather_multiplier
        * factors.time_multiplier,
    )

    assert set(asdict(factors)) == {
        "route_subtotal",
        "traffic_multiplier",
        "weather_multiplier",
        "time_multiplier",
        "unrounded_total",
    }
    assert reproduced == pytest.approx(factors.unrounded_total)
    assert round(factors.unrounded_total, 2) == estimate.estimated_price
    assert round(factors.unrounded_total + 1e-9, 2) == estimate.estimated_price


def test_minimum_fare_floor_applies() -> None:
    estimate = PricingModel().estimate(0.6, 3.0, 4, 1.0, 1.0)

    assert estimate.price_factors.time_multiplier == 1.0
    assert estimate.price_factors.unrounded_total == 7.50
    assert estimate.estimated_price == 7.50


def test_minimum_fare_stays_binding_as_adjustments_rise() -> None:
    prices = [
        PricingModel().estimate(0.6, 3.0, congestion, weather, 1.0)
        .estimated_price
        for congestion, weather in ((4, 1.0), (100, 1.0), (100, 1.12))
    ]

    assert prices == [7.50, 7.50, 7.50]


def test_price_increases_with_congestion_above_the_fare_floor() -> None:
    prices = [
        PricingModel().estimate(12.4, 24.8, congestion, 1.0, 1.0)
        .estimated_price
        for congestion in (4, 40, 100)
    ]

    assert prices[0] < prices[1] < prices[2]


@pytest.mark.parametrize(
    ("distance", "minutes", "weather_multiplier", "time_multiplier"),
    [
        (0.0, 10.0, 1.0, 1.0),
        (-1.0, 10.0, 1.0, 1.0),
        (1.0, 0.0, 1.0, 1.0),
        (1.0, -1.0, 1.0, 1.0),
        (1.0, 10.0, 0.0, 1.0),
        (1.0, 10.0, -1.0, 1.0),
        (1.0, 10.0, 1.0, 0.0),
        (1.0, 10.0, 1.0, -1.0),
    ],
)
def test_pricing_rejects_non_positive_inputs(
    distance: float,
    minutes: float,
    weather_multiplier: float,
    time_multiplier: float,
) -> None:
    with pytest.raises(ValueError):
        PricingModel().estimate(
            distance,
            minutes,
            4,
            weather_multiplier,
            time_multiplier,
        )
