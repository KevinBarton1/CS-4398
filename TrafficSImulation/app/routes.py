from .heatmap import build_heatmap
from .map_service import build_route_options
from .models import RouteOption
from .pricing_model import estimate_price
from .traffic_simulator import create_segments, time_of_day_factor
from .weather_service import weather_adjustment


def _bounded(payload, name, default, low, high):
    try:
        value = int(payload.get(name, default))
    except (TypeError, ValueError):
        value = default
    return max(low, min(high, value))


def plan_route(payload):
    mode = "realtime" if payload.get("mode") == "realtime" else "simulated"
    hour = _bounded(payload, "hour", 17, 0, 23)
    weather_level = _bounded(payload, "weather", 1, 0, 3)
    congestion = _bounded(payload, "congestion", 56, 0, 100)
    demand = _bounded(payload, "demand", 68, 0, 100)
    heatmap_mode = payload.get("heatmap", "congestion")

    if mode == "realtime":
        # Offline reference conditions keep the application useful without external keys.
        congestion, demand, weather_level = 44, 52, 0

    origin_name, destination_name, raw_routes = build_route_options(payload.get("origin"), payload.get("destination"))
    weather = weather_adjustment(weather_level)
    time_factor = time_of_day_factor(hour)
    routes = []
    for index, route in enumerate(raw_routes):
        route_congestion = max(4, congestion - index * 9)
        traffic_factor = 1 + route_congestion / 180
        adjusted_eta = round(route["base_eta_minutes"] * traffic_factor * weather["time_multiplier"] * time_factor, 1)
        price, factors = estimate_price(route["distance_miles"], adjusted_eta, route_congestion, demand, weather_level, time_factor)
        option = RouteOption(
            id=route["id"], name=route["name"], color=route["color"],
            distance_miles=route["distance_miles"], base_eta_minutes=route["base_eta_minutes"],
            adjusted_eta_minutes=adjusted_eta, estimated_price=price,
            congestion_score=route_congestion, demand_score=demand,
            points=route["points"], segments=create_segments(route, route_congestion, weather["time_multiplier"], index),
            factors=factors, data_source="Local reference model" if mode == "realtime" else "Simulated scenario",
        )
        routes.append(option.to_dict())

    recommended = min(routes, key=lambda item: item["adjusted_eta_minutes"] + item["estimated_price"] * 0.32)
    return {
        "origin": origin_name, "destination": destination_name, "mode": mode,
        "weather": weather, "hour": hour, "congestion": congestion, "demand": demand,
        "routes": routes, "recommended_route_id": recommended["id"],
        "heatmap": build_heatmap(congestion, demand, hour, heatmap_mode),
        "notice": "External traffic APIs are not configured; reference mode uses stable local baseline data." if mode == "realtime" else "Traffic, demand, weather, and prices are simulated planning estimates.",
    }

