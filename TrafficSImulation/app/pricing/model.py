from app.config import BASE_FARE, MINIMUM_FARE, PER_MILE_RATE, PER_MINUTE_RATE


def estimate_price(distance_miles, minutes, congestion, weather_multiplier, time_factor=None):
    subtotal = BASE_FARE + distance_miles * PER_MILE_RATE + minutes * PER_MINUTE_RATE
    congestion_multiplier = 1 + congestion / 500
    total = subtotal * congestion_multiplier * weather_multiplier
    if time_factor is not None:
        total *= time_factor
    final = max(MINIMUM_FARE, total)
    factors = {
        "route_subtotal": subtotal,
        "traffic_multiplier": congestion_multiplier,
        "weather_multiplier": weather_multiplier,
        "unrounded_total": final,
    }
    if time_factor is not None:
        factors["time_multiplier"] = time_factor
    return round(final + 1e-9, 2), factors
