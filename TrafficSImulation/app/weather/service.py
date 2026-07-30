from app.config import (
    WEATHER_LABELS,
    WEATHER_PRICE_MULTIPLIERS,
    WEATHER_SOURCE_SIMULATED,
    WEATHER_TIME_MULTIPLIERS,
)


def weather_adjustment(severity):
    severity = max(0, min(3, int(severity)))
    return {
        "severity": severity,
        "label": WEATHER_LABELS[severity],
        "time_multiplier": WEATHER_TIME_MULTIPLIERS[severity],
        "price_multiplier": WEATHER_PRICE_MULTIPLIERS[severity],
        "source": WEATHER_SOURCE_SIMULATED,
    }
