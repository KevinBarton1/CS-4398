BASE_FARE = 2.20
PER_MILE = 1.28
PER_MINUTE = 0.31
MINIMUM_FARE = 7.50


def estimate_price(distance_miles, minutes, congestion, demand, weather, time_factor):
    subtotal = BASE_FARE + distance_miles * PER_MILE + minutes * PER_MINUTE
    demand_multiplier = 1 + max(0, demand - 40) / 150
    congestion_multiplier = 1 + congestion / 500
    weather_multiplier = 1 + weather * 0.035
    total = subtotal * demand_multiplier * congestion_multiplier * weather_multiplier * time_factor
    return max(MINIMUM_FARE, round(total, 2)), {
        "base_and_route": round(subtotal, 2),
        "demand_multiplier": round(demand_multiplier, 2),
        "congestion_multiplier": round(congestion_multiplier, 2),
        "weather_multiplier": round(weather_multiplier, 2),
        "time_multiplier": round(time_factor, 2),
    }

