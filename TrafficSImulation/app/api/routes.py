from app.api.models import RouteOption
from app.config import ROUTE_SCORE_WEIGHTS
from app.heatmap.builder import build_heatmap
from app.map.service import build_route_options
from app.pricing.model import estimate_price
from app.simulation.traffic import create_segments, time_of_day_factor
from app.weather.service import weather_adjustment


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
        segments = create_segments(route, route_congestion, index)
        bpr_minutes = sum(segment.adjusted_minutes for segment in segments) + 2
        adjusted_eta_raw = bpr_minutes * weather["time_multiplier"] * time_factor
        adjusted_eta = round(adjusted_eta_raw, 1)
        price, factors = estimate_price(
            route["distance_miles"], adjusted_eta_raw, route_congestion, demand,
            weather["price_multiplier"], time_factor,
        )
        option = RouteOption(
            id=route["id"], name=route["name"], color=route["color"],
            distance_miles=route["distance_miles"], base_eta_minutes=route["base_eta_minutes"],
            adjusted_eta_minutes=adjusted_eta, estimated_price=price,
            congestion_score=route_congestion, demand_score=demand,
            objective=route["objective"], normalized_score=0,
            points=route["points"], segments=segments,
            factors=factors, data_source="Local reference model" if mode == "realtime" else "Simulated scenario",
        )
        routes.append(option.to_dict())

    maxima = {
        "time": max(item["adjusted_eta_minutes"] for item in routes),
        "distance": max(item["distance_miles"] for item in routes),
        "congestion": max(item["congestion_score"] for item in routes),
    }
    for item in routes:
        item["normalized_score"] = round(
            ROUTE_SCORE_WEIGHTS["time"] * item["adjusted_eta_minutes"] / maxima["time"]
            + ROUTE_SCORE_WEIGHTS["distance"] * item["distance_miles"] / maxima["distance"]
            + ROUTE_SCORE_WEIGHTS["congestion"] * item["congestion_score"] / maxima["congestion"]
            - ROUTE_SCORE_WEIGHTS["demand"] * item["demand_score"] / 100,
            4,
        )
    recommended = min(routes, key=lambda item: item["normalized_score"])
    return {
        "origin": origin_name, "destination": destination_name, "mode": mode,
        "weather": weather, "hour": hour, "congestion": congestion, "demand": demand,
        "routes": routes, "recommended_route_id": recommended["id"],
        "heatmap": build_heatmap(congestion, demand, hour, heatmap_mode),
        "notice": "External traffic APIs are not configured; reference mode uses stable local baseline data." if mode == "realtime" else "Traffic, demand, weather, and prices are simulated planning estimates.",
    }
