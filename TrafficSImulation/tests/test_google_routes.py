import copy
import json
from datetime import datetime, timezone

import httpx
import pytest

from app.config import Settings
from app.map.errors import (
    MapsNotConfiguredError,
    NoRouteFoundError,
    UpstreamTimeoutError,
    UpstreamUnavailableError,
)
from app.map.routing import GoogleRoutesGateway
from app.map.types import ResolvedPlace, TrafficInterval, TrafficSpeed
from tests.google_mocks import (
    ENCODED_POLYLINE,
    ROUTES_SUCCESS_PAYLOAD,
    make_mock_async_client,
    mock_json_response,
)

ORIGIN = ResolvedPlace(
    name="Downtown Austin",
    latitude=30.2672,
    longitude=-97.7431,
    source="google",
)
DESTINATION = ResolvedPlace(
    name="Austin Airport",
    latitude=30.1975,
    longitude=-97.6664,
    source="google",
)
DEPARTURE = datetime(2026, 7, 30, 22, 15, tzinfo=timezone.utc)


async def test_t21_routes_request_and_result_match_contract() -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return mock_json_response(request, ROUTES_SUCCESS_PAYLOAD)

    async with make_mock_async_client(handler) as client:
        routes = await GoogleRoutesGateway(
            Settings(google_maps_api_key="test-server-key"),
            client,
        ).compute(ORIGIN, DESTINATION, DEPARTURE, alternatives=True)

    assert len(routes) == 1
    route = routes[0]
    assert route.id == "route-1"
    assert route.distance_miles == 7.0
    assert route.duration_seconds == 720.0
    assert route.static_duration_seconds == 600.0
    assert route.traffic_ratio == 1.2
    assert route.traffic_intervals == [
        TrafficInterval(0, 1, TrafficSpeed.NORMAL),
        TrafficInterval(1, 2, TrafficSpeed.SPEED_UNSPECIFIED),
    ]
    assert len(route.polyline) == 3
    assert route.steps == [
        {
            "distance_meters": 8046,
            "duration_seconds": 480.0,
            "static_duration_seconds": 420.0,
            "polyline": route.polyline,
            "instruction": "Head south on Congress Ave",
        }
    ]

    request = requests[0]
    assert str(request.url) == (
        "https://routes.googleapis.com/directions/v2:computeRoutes"
    )
    assert request.headers["X-Goog-Api-Key"] == "test-server-key"
    assert request.headers["X-Goog-FieldMask"] == (
        "routes.duration,routes.staticDuration,routes.distanceMeters,"
        "routes.polyline.encodedPolyline,"
        "routes.travelAdvisory.speedReadingIntervals,"
        "routes.legs.travelAdvisory.speedReadingIntervals,"
        "routes.legs.steps.distanceMeters,routes.legs.steps.staticDuration,"
        "routes.legs.steps.polyline.encodedPolyline,"
        "routes.legs.steps.navigationInstruction,routes.description,"
        "routes.routeLabels"
    )
    assert request.extensions["timeout"]["read"] == 10.0
    assert json.loads(request.content) == {
        "origin": {
            "location": {
                "latLng": {
                    "latitude": 30.2672,
                    "longitude": -97.7431,
                }
            }
        },
        "destination": {
            "location": {
                "latLng": {
                    "latitude": 30.1975,
                    "longitude": -97.6664,
                }
            }
        },
        "travelMode": "DRIVE",
        "computeAlternativeRoutes": True,
        "routingPreference": "TRAFFIC_AWARE",
        "units": "IMPERIAL",
        "regionCode": "US",
        "departureTime": "2026-07-30T22:15:00Z",
        "extraComputations": ["TRAFFIC_ON_POLYLINE"],
    }


async def test_t21_route_level_intervals_are_the_fallback() -> None:
    payload = copy.deepcopy(ROUTES_SUCCESS_PAYLOAD)
    payload["routes"][0]["legs"][0]["travelAdvisory"] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        return mock_json_response(request, payload)

    async with make_mock_async_client(handler) as client:
        route = (
            await GoogleRoutesGateway(
                Settings(google_maps_api_key="test-server-key"),
                client,
            ).compute(ORIGIN, DESTINATION, DEPARTURE, alternatives=False)
        )[0]

    assert route.traffic_intervals == [
        TrafficInterval(0, 2, TrafficSpeed.TRAFFIC_JAM)
    ]


@pytest.mark.parametrize(
    ("duration", "expected"),
    [
        ("1284s", 1284.0),
        (1284, 1284.0),
        ({"seconds": "1284"}, 1284.0),
        ("not-a-duration", None),
    ],
)
async def test_t21_duration_shapes_are_normalized(
    duration: object,
    expected: float | None,
) -> None:
    payload = copy.deepcopy(ROUTES_SUCCESS_PAYLOAD)
    payload["routes"][0]["duration"] = duration

    def handler(request: httpx.Request) -> httpx.Response:
        return mock_json_response(request, payload)

    async with make_mock_async_client(handler) as client:
        route = (
            await GoogleRoutesGateway(
                Settings(google_maps_api_key="test-server-key"),
                client,
            ).compute(ORIGIN, DESTINATION, DEPARTURE, alternatives=False)
        )[0]

    assert route.duration_seconds == expected


async def test_t21_alternative_count_is_bounded() -> None:
    template = ROUTES_SUCCESS_PAYLOAD["routes"][0]
    payload = {"routes": [copy.deepcopy(template) for _ in range(4)]}
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return mock_json_response(request, payload)

    async with make_mock_async_client(handler) as client:
        gateway = GoogleRoutesGateway(
            Settings(google_maps_api_key="test-server-key"),
            client,
        )
        alternatives = await gateway.compute(
            ORIGIN,
            DESTINATION,
            DEPARTURE,
            alternatives=True,
        )
        single = await gateway.compute(
            ORIGIN,
            DESTINATION,
            DEPARTURE,
            alternatives=False,
        )

    assert [route.id for route in alternatives] == [
        "route-1",
        "route-2",
        "route-3",
    ]
    assert [route.id for route in single] == ["route-1"]
    assert [
        json.loads(request.content)["computeAlternativeRoutes"]
        for request in requests
    ] == [True, False]


async def test_t21_zero_routes_raises_no_route_found() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return mock_json_response(request, {"routes": []})

    async with make_mock_async_client(handler) as client:
        gateway = GoogleRoutesGateway(
            Settings(google_maps_api_key="test-server-key"),
            client,
        )
        with pytest.raises(NoRouteFoundError) as raised:
            await gateway.compute(
                ORIGIN,
                DESTINATION,
                DEPARTURE,
                alternatives=True,
            )

    assert raised.value.code == "no_route_found"
    assert raised.value.status == 400


async def test_t21_missing_key_fails_before_transport() -> None:
    calls = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return mock_json_response(request, ROUTES_SUCCESS_PAYLOAD)

    async with make_mock_async_client(handler) as client:
        gateway = GoogleRoutesGateway(
            Settings(google_maps_api_key=""),
            client,
        )
        with pytest.raises(MapsNotConfiguredError):
            await gateway.compute(
                ORIGIN,
                DESTINATION,
                DEPARTURE,
                alternatives=False,
            )

    assert calls == 0


@pytest.mark.parametrize(
    ("handler_kind", "exception_type", "status"),
    [
        ("status", UpstreamUnavailableError, 502),
        ("timeout", UpstreamTimeoutError, 504),
    ],
)
async def test_t21_upstream_failures_are_typed_and_sanitized(
    handler_kind: str,
    exception_type: type[Exception],
    status: int,
) -> None:
    credential = "test-server-key"
    upstream_body = "billing-account raw upstream body"

    def handler(request: httpx.Request) -> httpx.Response:
        if handler_kind == "timeout":
            raise httpx.ReadTimeout(upstream_body, request=request)
        return httpx.Response(
            status_code=429,
            text=upstream_body,
            request=request,
        )

    async with make_mock_async_client(handler) as client:
        gateway = GoogleRoutesGateway(
            Settings(google_maps_api_key=credential),
            client,
        )
        with pytest.raises(exception_type) as raised:
            await gateway.compute(
                ORIGIN,
                DESTINATION,
                DEPARTURE,
                alternatives=False,
            )

    error = raised.value
    assert getattr(error, "status") == status
    assert credential not in getattr(error, "detail")
    assert upstream_body not in getattr(error, "detail")


def test_t21_fixture_polyline_is_the_shared_known_input() -> None:
    assert ENCODED_POLYLINE == "_p~iF~ps|U_ulLnnqC_mqNvxq`@"


@pytest.mark.asyncio
async def test_t50_retries_once_on_transient_upstream_failure() -> None:
    attempts = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            return httpx.Response(503, request=request)
        return mock_json_response(request, ROUTES_SUCCESS_PAYLOAD)

    async with make_mock_async_client(handler) as client:
        routes = await GoogleRoutesGateway(
            Settings(google_maps_api_key="test-server-key"),
            client,
        ).compute(ORIGIN, DESTINATION, DEPARTURE, alternatives=False)

    assert attempts == 2
    assert len(routes) == 1


@pytest.mark.asyncio
async def test_t50_does_not_retry_non_transient_status() -> None:
    attempts = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        return httpx.Response(429, request=request)

    async with make_mock_async_client(handler) as client:
        gateway = GoogleRoutesGateway(
            Settings(google_maps_api_key="test-server-key"),
            client,
        )
        with pytest.raises(UpstreamUnavailableError):
            await gateway.compute(ORIGIN, DESTINATION, DEPARTURE, alternatives=False)

    assert attempts == 1
