import httpx

from app.config import Settings
from app.map.health import GoogleApiProbe
from tests.google_mocks import (
    PLACES_SUCCESS_PAYLOAD,
    ROUTES_SUCCESS_PAYLOAD,
    make_mock_async_client,
    mock_json_response,
)


async def test_t10_probe_caches_success_without_live_calls() -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        if "places.googleapis.com" in request.url.host:
            return mock_json_response(request, PLACES_SUCCESS_PAYLOAD)
        return mock_json_response(request, ROUTES_SUCCESS_PAYLOAD)

    async with make_mock_async_client(handler) as client:
        probe = GoogleApiProbe(
            Settings(google_maps_api_key="test-server-key"),
            client,
        )
        first = await probe.check()
        second = await probe.check()

    assert first.ok is True
    assert first.message == "Places and Routes reachable."
    assert first.checked_at.endswith("Z")
    assert second is first
    assert len(requests) == 3


async def test_t10_probe_never_raises_or_leaks_failure_details() -> None:
    credential = "test-server-key"
    upstream_body = "private Google quota body"

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            status_code=403,
            text=upstream_body,
            request=request,
        )

    async with make_mock_async_client(handler) as client:
        result = await GoogleApiProbe(
            Settings(google_maps_api_key=credential),
            client,
        ).check()

    assert result.ok is False
    assert result.message == "Places service check failed."
    assert credential not in result.message
    assert upstream_body not in result.message


async def test_t10_probe_with_missing_key_makes_no_request() -> None:
    calls = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return mock_json_response(request, PLACES_SUCCESS_PAYLOAD)

    async with make_mock_async_client(handler) as client:
        result = await GoogleApiProbe(
            Settings(google_maps_api_key=" "),
            client,
        ).check()

    assert result.ok is False
    assert "not configured" in result.message
    assert calls == 0


async def test_t10_probe_contains_unexpected_transport_failure() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise RuntimeError("internal transport detail")

    async with make_mock_async_client(handler) as client:
        result = await GoogleApiProbe(
            Settings(google_maps_api_key="test-server-key"),
            client,
        ).check()

    assert result.ok is False
    assert result.message == "Google API reachability check failed."
    assert "internal transport detail" not in result.message
