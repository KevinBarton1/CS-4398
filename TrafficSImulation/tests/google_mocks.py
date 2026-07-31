from collections.abc import Callable
import json

import httpx

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
