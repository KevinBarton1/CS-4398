import json

import httpx
import pytest

from app.config import Settings
from app.map.errors import (
    InvalidLocationError,
    MapsNotConfiguredError,
    UpstreamTimeoutError,
    UpstreamUnavailableError,
)
from app.map.places import GooglePlacesGateway
from app.map.types import ResolvedPlace
from tests.google_mocks import (
    PLACES_SUCCESS_PAYLOAD,
    make_mock_async_client,
    mock_json_response,
)


async def test_t20_places_request_and_result_match_contract() -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return mock_json_response(request, PLACES_SUCCESS_PAYLOAD)

    async with make_mock_async_client(handler) as client:
        gateway = GooglePlacesGateway(
            Settings(google_maps_api_key="test-server-key"),
            client,
        )
        result = await gateway.resolve("  Downtown   Austin  ")

    assert result == ResolvedPlace(
        name="Downtown Austin",
        latitude=30.2672,
        longitude=-97.7431,
        source="google",
    )
    assert len(requests) == 1
    request = requests[0]
    assert str(request.url) == (
        "https://places.googleapis.com/v1/places:searchText"
    )
    assert request.headers["X-Goog-Api-Key"] == "test-server-key"
    assert request.headers["X-Goog-FieldMask"] == (
        "places.displayName,places.formattedAddress,places.location"
    )
    assert request.extensions["timeout"]["read"] == 8.0
    assert request.extensions["timeout"]["connect"] == 8.0
    assert request.content
    assert request.read()
    assert request.method == "POST"
    payload = json.loads(request.content)
    assert payload == {
        "textQuery": "downtown austin",
        "regionCode": "US",
        "locationBias": {
            "circle": {
                "center": {
                    "latitude": 30.2672,
                    "longitude": -97.7431,
                },
                "radius": 35000.0,
            }
        },
        "maxResultCount": 1,
    }


@pytest.mark.parametrize(
    "payload",
    [
        {"places": []},
        {
            "places": [
                {
                    "displayName": {"text": "Unknown"},
                    "location": {"latitude": 30.2672},
                }
            ]
        },
    ],
)
async def test_t20_unusable_place_raises_invalid_location(
    payload: object,
) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return mock_json_response(request, payload)

    async with make_mock_async_client(handler) as client:
        gateway = GooglePlacesGateway(
            Settings(google_maps_api_key="test-server-key"),
            client,
        )
        with pytest.raises(InvalidLocationError) as raised:
            await gateway.resolve("Mars Colony")

    assert raised.value.code == "invalid_location"
    assert raised.value.status == 400
    assert "Mars Colony" in raised.value.detail


async def test_t20_missing_key_fails_before_transport() -> None:
    calls = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return mock_json_response(request, PLACES_SUCCESS_PAYLOAD)

    async with make_mock_async_client(handler) as client:
        gateway = GooglePlacesGateway(
            Settings(google_maps_api_key=" "),
            client,
        )
        with pytest.raises(MapsNotConfiguredError) as raised:
            await gateway.resolve("Downtown Austin")

    assert calls == 0
    assert raised.value.code == "maps_not_configured"
    assert raised.value.status == 503


@pytest.mark.parametrize(
    ("handler_kind", "exception_type", "status"),
    [
        ("status", UpstreamUnavailableError, 502),
        ("timeout", UpstreamTimeoutError, 504),
    ],
)
async def test_t20_upstream_failures_are_typed_and_sanitized(
    handler_kind: str,
    exception_type: type[Exception],
    status: int,
) -> None:
    credential = "test-server-key"
    upstream_body = "quota project-secret raw upstream body"

    def handler(request: httpx.Request) -> httpx.Response:
        if handler_kind == "timeout":
            raise httpx.ReadTimeout(upstream_body, request=request)
        return httpx.Response(
            status_code=403,
            text=upstream_body,
            request=request,
        )

    async with make_mock_async_client(handler) as client:
        gateway = GooglePlacesGateway(
            Settings(google_maps_api_key=credential),
            client,
        )
        with pytest.raises(exception_type) as raised:
            await gateway.resolve("Downtown Austin")

    error = raised.value
    assert getattr(error, "status") == status
    assert credential not in getattr(error, "detail")
    assert upstream_body not in getattr(error, "detail")


@pytest.mark.asyncio
async def test_t50_places_retries_once_on_transient_upstream_failure() -> None:
    attempts = 0
    success_payload = {
        "places": [
            {
                "displayName": {"text": "Downtown Austin"},
                "location": {"latitude": 30.2672, "longitude": -97.7431},
            }
        ]
    }

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            return httpx.Response(503, request=request)
        return mock_json_response(request, success_payload)

    async with make_mock_async_client(handler) as client:
        place = await GooglePlacesGateway(
            Settings(google_maps_api_key="test-server-key"),
            client,
        ).resolve("Downtown Austin")

    assert attempts == 2
    assert place.name == "Downtown Austin"
