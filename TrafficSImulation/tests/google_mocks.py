from app.map.types import ResolvedPlace


def mock_google_routes():
    step = {
        "distanceMeters": 8046,
        "staticDuration": "600s",
        "navigationInstruction": {"instructions": "Head south on Congress Ave"},
    }
    templates = [
        ("Fastest", "Minimum adjusted time", "#55d6be", 6.9, 14.1),
        ("Balanced", "Weighted time, distance, congestion and demand", "#ffb35c", 7.5, 13.8),
        ("Low traffic", "Minimum congestion exposure", "#8aa8ff", 8.1, 13.6),
    ]
    routes = []
    for index, (name, objective, color, distance, base_eta) in enumerate(templates):
        routes.append({
            "id": f"route-{index + 1}",
            "name": name,
            "objective": objective,
            "color": color,
            "distance_miles": distance,
            "base_eta_minutes": base_eta,
            "road_names": ["Congress Ave", "Airport Blvd"],
            "google_steps": [step],
            "google_duration_seconds": base_eta * 60,
            "google_static_duration_seconds": base_eta * 60,
            "map_source": "google",
        })
    return routes


def mock_build_route_options(origin, destination, hour=17, use_traffic=False):
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
    return "Downtown Austin", "Austin Airport", mock_google_routes(), origin_place, destination_place
