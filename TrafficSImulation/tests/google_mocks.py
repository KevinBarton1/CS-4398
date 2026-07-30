from app.map.types import ResolvedPlace


def _mock_polyline(offset: float = 0.0) -> list[dict[str, float]]:
    return [
        {"lat": 30.2672 + offset, "lng": -97.7431},
        {"lat": 30.2500 + offset, "lng": -97.7200},
        {"lat": 30.2300 + offset, "lng": -97.6900},
        {"lat": 30.1975 + offset, "lng": -97.6664},
    ]


def mock_google_routes():
    step = {
        "distanceMeters": 8046,
        "staticDuration": "600s",
        "duration": "720s",
        "navigationInstruction": {"instructions": "Head south on Congress Ave"},
    }
    templates = [
        ("Fastest", "Minimum adjusted time", "#55d6be", 6.9, 14.1, 16.0),
        ("Balanced", "Weighted time, distance, congestion and demand", "#ffb35c", 7.5, 13.8, 15.5),
        ("Low traffic", "Minimum congestion exposure", "#4d72e8", 8.1, 13.6, 14.8),
    ]
    routes = []
    for index, (name, objective, color, distance, base_eta, traffic_eta) in enumerate(templates):
        routes.append({
            "id": f"route-{index + 1}",
            "name": name,
            "objective": objective,
            "color": color,
            "distance_miles": distance,
            "base_eta_minutes": base_eta,
            "road_names": ["Congress Ave", "Airport Blvd"],
            "google_steps": [step],
            "google_duration_seconds": traffic_eta * 60,
            "google_static_duration_seconds": base_eta * 60,
            "traffic_ratio": round(traffic_eta / base_eta, 4),
            "traffic_intervals": [
                {"start_index": 0, "end_index": 2, "speed": "NORMAL"},
                {"start_index": 2, "end_index": 4, "speed": "SLOW"},
            ],
            "polyline": _mock_polyline(index * 0.004),
            "map_source": "google",
        })
    return routes


def mock_build_route_options(
    origin,
    destination,
    hour=17,
    use_traffic=True,
    compute_alternatives=True,
):
    origin_place = ResolvedPlace(
        name="Downtown Austin",
        latitude=30.2672,
        longitude=-97.7431,
        source="google",
    )
    destination_place = ResolvedPlace(
        name="Austin Airport",
        latitude=30.1975,
        longitude=-97.6664,
        source="google",
    )
    routes = mock_google_routes()
    if not compute_alternatives:
        routes = routes[:1]
    return "Downtown Austin", "Austin Airport", routes, origin_place, destination_place
