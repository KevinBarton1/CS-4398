from app.api.models import RouteOption
from app.config import ROUTE_SCORE_WEIGHTS
from app.map.google_embed import build_map_embed_url, compute_map_view
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


def _route_data_source(mode: str) -> str:
    return "Google Maps" if mode == "realtime" else "Google Maps route geometry"


def _plan_notice(mode: str) -> str:
    if mode == "realtime":
        return "Route geometry and travel times from Google Maps with traffic-aware routing."
    return "Route geometry and distances from Google Maps; demand, weather, and prices remain simulated planning estimates."


def _adjusted_eta_minutes(route, mode, weather, time_factor, bpr_minutes):
    google_duration = route.get("google_duration_seconds")
    google_static = route.get("google_static_duration_seconds")
    if route.get("map_source") == "google" and mode == "realtime" and google_duration:
        adjusted_eta_raw = (google_duration / 60) * weather["time_multiplier"] * time_factor
    elif route.get("map_source") == "google" and google_static:
        adjusted_eta_raw = (google_static / 60) * weather["time_multiplier"] * time_factor
    else:
        adjusted_eta_raw = bpr_minutes * weather["time_multiplier"] * time_factor
    return round(adjusted_eta_raw, 1), adjusted_eta_raw


def plan_route(payload):
    mode = "realtime" if payload.get("mode") == "realtime" else "simulated"
    hour = _bounded(payload, "hour", 17, 0, 23)
    weather_level = _bounded(payload, "weather", 1, 0, 3)
    congestion = _bounded(payload, "congestion", 56, 0, 100)
    demand = _bounded(payload, "demand", 68, 0, 100)

    if mode == "realtime":
        # Reference mode uses traffic-aware Google routing when configured.
        congestion, demand, weather_level = 44, 52, 0

    origin_name, destination_name, raw_routes, origin_place, destination_place = build_route_options(
        payload.get("origin"),
        payload.get("destination"),
        hour=hour,
        use_traffic=mode == "realtime",
    )
    center_lat, center_lng, zoom = compute_map_view(
        origin_place.latitude,
        origin_place.longitude,
        destination_place.latitude,
        destination_place.longitude,
    )
    map_embed_url = build_map_embed_url(center_lat, center_lng, zoom)
    weather = weather_adjustment(weather_level)
    time_factor = time_of_day_factor(hour)
    routes = []
    for index, route in enumerate(raw_routes):
        route_congestion = max(4, congestion - index * 9)
        segments = create_segments(route, route_congestion, index)
        bpr_minutes = sum(segment.adjusted_minutes for segment in segments) + 2
        adjusted_eta, adjusted_eta_raw = _adjusted_eta_minutes(
            route, mode, weather, time_factor, bpr_minutes,
        )
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
            segments=segments, factors=factors, data_source=_route_data_source(mode),
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
        "notice": _plan_notice(mode),
        "map_embed_url": map_embed_url,
    }
