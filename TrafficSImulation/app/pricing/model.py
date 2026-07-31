from dataclasses import asdict, dataclass

from app.config import (
    BASE_FARE,
    MINIMUM_FARE,
    PER_MILE_RATE,
    PER_MINUTE_RATE,
    PRICE_CONGESTION_DIVISOR,
)


@dataclass(frozen=True, slots=True)
class PriceFactors:
    route_subtotal: float
    traffic_multiplier: float
    weather_multiplier: float
    time_multiplier: float
    unrounded_total: float


@dataclass(frozen=True, slots=True)
class PriceEstimate:
    estimated_price: float
    price_factors: PriceFactors


class PricingModel:
    def estimate(
        self,
        distance_miles: float,
        minutes: float,
        congestion_score: int,
        weather_price_multiplier: float,
        time_multiplier: float,
    ) -> PriceEstimate:
        if distance_miles <= 0:
            raise ValueError("Distance must be positive.")
        if minutes <= 0:
            raise ValueError("Duration must be positive.")
        if weather_price_multiplier <= 0:
            raise ValueError("Weather price multiplier must be positive.")
        if time_multiplier <= 0:
            raise ValueError("Time multiplier must be positive.")

        route_subtotal = (
            BASE_FARE
            + distance_miles * PER_MILE_RATE
            + minutes * PER_MINUTE_RATE
        )
        traffic_multiplier = 1 + congestion_score / PRICE_CONGESTION_DIVISOR
        if traffic_multiplier <= 0:
            raise ValueError("Traffic multiplier must be positive.")

        raw_total = (
            route_subtotal
            * traffic_multiplier
            * weather_price_multiplier
            * time_multiplier
        )
        unrounded_total = max(MINIMUM_FARE, raw_total)
        factors = PriceFactors(
            route_subtotal=route_subtotal,
            traffic_multiplier=traffic_multiplier,
            weather_multiplier=weather_price_multiplier,
            time_multiplier=time_multiplier,
            unrounded_total=unrounded_total,
        )
        return PriceEstimate(
            estimated_price=round(unrounded_total + 1e-9, 2),
            price_factors=factors,
        )


def estimate_price(
    distance_miles: float,
    minutes: float,
    congestion: int,
    weather_multiplier: float,
    time_factor: float | None = None,
) -> tuple[float, dict]:
    """Compatibility adapter for the legacy API controller."""
    estimate = PricingModel().estimate(
        distance_miles=distance_miles,
        minutes=minutes,
        congestion_score=congestion,
        weather_price_multiplier=weather_multiplier,
        time_multiplier=1.0 if time_factor is None else time_factor,
    )
    return estimate.estimated_price, asdict(estimate.price_factors)
