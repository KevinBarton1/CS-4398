from .config import BASE_FARE, MINIMUM_FARE, PER_MILE_RATE, PER_MINUTE_RATE


def estimate_price(distance_miles, minutes, congestion, demand, weather_multiplier, time_factor):
    subtotal = BASE_FARE + distance_miles * PER_MILE_RATE + minutes * PER_MINUTE_RATE
    demand_multiplier = 1 + max(0, demand - 40) / 150
    congestion_multiplier = 1 + congestion / 500
    total = subtotal * demand_multiplier * congestion_multiplier * weather_multiplier * time_factor
    final = max(MINIMUM_FARE, total)
    return round(final + 1e-9, 2), {
        "route_subtotal": subtotal,
        "demand_multiplier": demand_multiplier,
        "traffic_multiplier": congestion_multiplier,
        "weather_multiplier": weather_multiplier,
        "time_multiplier": time_factor,
        "unrounded_total": final,
    }
