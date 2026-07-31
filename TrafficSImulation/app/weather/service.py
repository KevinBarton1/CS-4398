from dataclasses import asdict, dataclass

from app.config import (
    WEATHER_LABELS,
    WEATHER_PRICE_MULTIPLIERS,
    WEATHER_SOURCE_SIMULATED,
    WEATHER_TIME_MULTIPLIERS,
)


@dataclass(frozen=True, slots=True)
class WeatherState:
    severity: int
    label: str
    time_multiplier: float
    price_multiplier: float
    source: str


class WeatherService:
    def state(self, severity: int) -> WeatherState:
        level = max(0, min(3, int(severity)))
        return WeatherState(
            severity=level,
            label=WEATHER_LABELS[level],
            time_multiplier=WEATHER_TIME_MULTIPLIERS[level],
            price_multiplier=WEATHER_PRICE_MULTIPLIERS[level],
            source=WEATHER_SOURCE_SIMULATED,
        )


def weather_adjustment(severity: int) -> dict:
    """Compatibility adapter for the legacy API controller."""
    return asdict(WeatherService().state(severity))
