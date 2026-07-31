from collections.abc import Callable
import json

import httpx

from app.map.types import ResolvedPlace

ENCODED_POLYLINE = "_p~iF~ps|U_ulLnnqC_mqNvxq`@"

PLACES_SUCCESS_PAYLOAD = {
    "places": [
        {
            "displayName": {"text": "Downtown Austin"},
            "formattedAddress": "Downtown Austin, Austin, TX, USA",
            "location": {
                "latitude": 30.2672,
                "longitude": -97.7431,
            },
        }
    ]
}

PLACES_AIRPORT_PAYLOAD = {
    "places": [
        {
            "displayName": {"text": "Austin Airport"},
            "formattedAddress": "Austin-Bergstrom International Airport, Austin, TX, USA",
            "location": {
                "latitude": 30.1975,
                "longitude": -97.6664,
            },
        }
    ]
}

PLACES_SAME_SPOT_PAYLOAD = {
    "places": [
        {
            "displayName": {"text": "Same Spot"},
            "formattedAddress": "Same Spot, Austin, TX, USA",
            "location": {
                "latitude": 30.2672,
                "longitude": -97.7431,
            },
        }
    ]
}

ROUTES_SUCCESS_PAYLOAD = {
    "routes": [
        {
            "duration": "720s",
            "staticDuration": "600s",
            "distanceMeters": 11265,
            "polyline": {"encodedPolyline": ENCODED_POLYLINE},
            "travelAdvisory": {
                "speedReadingIntervals": [
                    {
                        "startPolylinePointIndex": 0,
                        "endPolylinePointIndex": 2,
                        "speed": "TRAFFIC_JAM",
                    }
                ]
            },
            "legs": [
                {
                    "travelAdvisory": {
                        "speedReadingIntervals": [
                            {
                                "startPolylinePointIndex": 0,
                                "endPolylinePointIndex": 1,
                                "speed": "NORMAL",
                            },
                            {
                                "startPolylinePointIndex": 1,
                                "endPolylinePointIndex": 2,
                                "speed": "UNRECOGNIZED",
                            },
                            {
                                "startPolylinePointIndex": 2,
                                "speed": "SLOW",
                            },
                        ]
                    },
                    "steps": [
                        {
                            "distanceMeters": 8046,
                            "duration": "480s",
                            "staticDuration": "420s",
                            "polyline": {
                                "encodedPolyline": ENCODED_POLYLINE
                            },
                            "navigationInstruction": {
                                "instructions": "Head south on Congress Ave"
                            },
                        }
                    ],
                }
            ],
        }
    ]
}


def routes_payload(route_count: int = 1) -> dict:
    templates = [
        ("720s", "600s", 11265),
        ("780s", "630s", 12100),
        ("840s", "660s", 12950),
    ]
    routes = []
    for index in range(min(route_count, len(templates))):
        duration, static_duration, distance = templates[index]
        routes.append(
            {
                "duration": duration,
                "staticDuration": static_duration,
                "distanceMeters": distance,
                "polyline": {"encodedPolyline": ENCODED_POLYLINE},
                "travelAdvisory": {
                    "speedReadingIntervals": [
                        {
                            "startPolylinePointIndex": 0,
                            "endPolylinePointIndex": 2,
                            "speed": "NORMAL",
                        }
                    ]
                },
                "legs": [
                    {
                        "travelAdvisory": {
                            "speedReadingIntervals": [
                                {
                                    "startPolylinePointIndex": 0,
                                    "endPolylinePointIndex": 2,
                                    "speed": "NORMAL",
                                }
                            ]
                        },
                        "steps": [
                            {
                                "distanceMeters": distance,
                                "duration": duration,
                                "staticDuration": static_duration,
                                "polyline": {
                                    "encodedPolyline": ENCODED_POLYLINE
                                },
                                "navigationInstruction": {
                                    "instructions": f"Route leg {index + 1}"
                                },
                            }
                        ],
                    }
                ],
            }
        )
    return {"routes": routes}


def make_mock_async_client(
    handler: Callable[[httpx.Request], httpx.Response],
) -> httpx.AsyncClient:
    return httpx.AsyncClient(transport=httpx.MockTransport(handler))


def mock_json_response(
    request: httpx.Request,
    payload: object,
    status_code: int = 200,
) -> httpx.Response:
    return httpx.Response(
        status_code=status_code,
        json=payload,
        request=request,
    )


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


def make_api_mock_handler(
    *,
    places_empty: bool = False,
    same_place: bool = False,
    routes_empty: bool = False,
    route_count: int = 3,
    upstream_status: int | None = None,
    timeout: bool = False,
) -> tuple[Callable[[httpx.Request], httpx.Response], dict[str, int]]:
    counters = {"places": 0, "routes": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        if timeout:
            raise httpx.TimeoutException("upstream timed out")

        host = request.url.host or ""
        if "places.googleapis.com" in host:
            counters["places"] += 1
            if places_empty:
                return mock_json_response(request, {"places": []})
            if same_place:
                return mock_json_response(request, PLACES_SAME_SPOT_PAYLOAD)
            payload = json.loads(request.content) if request.content else {}
            query = str(payload.get("textQuery", "")).lower()
            if "airport" in query:
                return mock_json_response(request, PLACES_AIRPORT_PAYLOAD)
            return mock_json_response(request, PLACES_SUCCESS_PAYLOAD)

        if "routes.googleapis.com" in host:
            counters["routes"] += 1
            if upstream_status is not None:
                return httpx.Response(
                    status_code=upstream_status,
                    text="private upstream body",
                    request=request,
                )
            if routes_empty:
                return mock_json_response(request, {"routes": []})
            return mock_json_response(request, routes_payload(route_count))

        return httpx.Response(status_code=404, request=request)

    return handler, counters
