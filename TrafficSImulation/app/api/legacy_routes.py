from app.api.legacy_models import RouteOption
from app.config import ROUTE_SCORE_WEIGHTS
from app.map.google_embed import (
    build_directions_embed_url,
    build_map_embed_url,
    compute_map_view_for_polyline,
)
from app.map.service import build_route_options
from app.pricing.model import estimate_price
from app.simulation.legacy_segments import create_segments
from app.simulation.traffic import time_of_day_factor
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
        return "Real-Time mode: route, distance, and travel time from Google Maps with traffic-aware routing."
    return (
        "Route geometry and distances from Google Maps with departure-hour traffic; "
        "weather adjusts planning estimates."
    )


def _adjusted_eta_minutes(route, mode, weather, time_factor, bpr_minutes):
    google_duration = route.get("google_duration_seconds")
    google_static = route.get("google_static_duration_seconds")
    if route.get("map_source") == "google" and google_duration and google_static:
        if mode == "simulated":
            adjusted_eta_raw = (google_duration / 60) * weather["time_multiplier"]
        else:
            adjusted_eta_raw = (google_duration / 60) * weather["time_multiplier"] * time_factor
    elif route.get("map_source") == "google" and google_static:
        adjusted_eta_raw = (google_static / 60) * weather["time_multiplier"]
        if mode == "realtime":
            adjusted_eta_raw *= time_factor
    else:
        adjusted_eta_raw = bpr_minutes * weather["time_multiplier"]
        if mode == "realtime":
            adjusted_eta_raw *= time_factor
    return round(adjusted_eta_raw, 1), adjusted_eta_raw


def plan_route(payload):
    mode = "realtime" if payload.get("mode") == "realtime" else "simulated"
    hour = _bounded(payload, "hour", 17, 0, 23)
    weather_level = _bounded(payload, "weather", 1, 0, 3)
    congestion = _bounded(payload, "congestion", 56, 0, 100)

    if mode == "realtime":
        congestion, weather_level = 44, 0

    origin_name, destination_name, raw_routes, _, _ = build_route_options(
        payload.get("origin"),
        payload.get("destination"),
        hour=hour,
        use_traffic=True,
        compute_alternatives=mode == "simulated",
    )
    if mode == "realtime":
        raw_routes = raw_routes[:1]
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
            route["distance_miles"],
            adjusted_eta_raw,
            route_congestion,
            weather["price_multiplier"],
            time_factor if mode == "realtime" else None,
        )
        polyline = route.get("polyline") or []
        center_lat, center_lng, zoom = compute_map_view_for_polyline(polyline)
        option = RouteOption(
            id=route["id"], name=route["name"], color=route["color"],
            distance_miles=route["distance_miles"], base_eta_minutes=route["base_eta_minutes"],
            adjusted_eta_minutes=adjusted_eta, estimated_price=price,
            congestion_score=route_congestion,
            objective=route["objective"], normalized_score=0,
            segments=segments, factors=factors, data_source=_route_data_source(mode),
            polyline=polyline,
        )
        route_dict = option.to_dict()
        route_dict["traffic_intervals"] = route.get("traffic_intervals") or []
        route_dict["map_view"] = {
            "center_lat": center_lat,
            "center_lng": center_lng,
            "zoom": zoom,
        }
        route_dict["map_embed_url"] = build_map_embed_url(center_lat, center_lng, zoom)
        routes.append(route_dict)

    maxima = {
        "time": max(item["adjusted_eta_minutes"] for item in routes),
        "distance": max(item["distance_miles"] for item in routes),
        "congestion": max(item["congestion_score"] for item in routes),
    }
    for item in routes:
        item["normalized_score"] = round(
            ROUTE_SCORE_WEIGHTS["time"] * item["adjusted_eta_minutes"] / maxima["time"]
            + ROUTE_SCORE_WEIGHTS["distance"] * item["distance_miles"] / maxima["distance"]
            + ROUTE_SCORE_WEIGHTS["congestion"] * item["congestion_score"] / maxima["congestion"],
            4,
        )
    recommended = min(routes, key=lambda item: item["normalized_score"])
    directions_embed_url = build_directions_embed_url(origin_name, destination_name)
    response = {
        "origin": origin_name, "destination": destination_name, "mode": mode,
        "weather": weather, "hour": hour, "congestion": congestion,
        "routes": routes, "recommended_route_id": recommended["id"],
        "notice": _plan_notice(mode),
        "map_embed_url": recommended["map_embed_url"],
        "map_view": recommended["map_view"],
        "directions_embed_url": directions_embed_url,
    }
    return response
