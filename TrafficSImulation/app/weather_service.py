WEATHER_LABELS = ["Clear", "Light rain", "Heavy rain", "Severe"]


def weather_adjustment(severity):
    severity = max(0, min(3, int(severity)))
    return {
        "severity": severity,
        "label": WEATHER_LABELS[severity],
        "time_multiplier": [1.0, 1.08, 1.18, 1.32][severity],
        "source": "Simulated fallback",
    }

