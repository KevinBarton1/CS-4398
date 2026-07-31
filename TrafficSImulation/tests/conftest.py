from pathlib import Path

import httpx
import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.map.health import ProbeResult
from main import create_app
from tests.google_mocks import make_api_mock_handler

SERVER_KEY = "test-server-key-should-not-leak"
BROWSER_KEY = "test-browser-key-for-map"
NO_STATIC = Path("__missing_frontend_build__")
PROBE_OK = ProbeResult(
    ok=True,
    message="Places and Routes reachable.",
    checked_at="2026-07-30T21:00:00Z",
)
PROBE_FAILED = ProbeResult(
    ok=False,
    message="Places service check failed.",
    checked_at="2026-07-30T21:00:00Z",
)


@pytest.fixture
def test_settings() -> Settings:
    return Settings(
        google_maps_api_key=SERVER_KEY,
        google_maps_browser_api_key=BROWSER_KEY,
    )


def _build_client(
    test_settings: Settings,
    *,
    handler=None,
    probe_result: ProbeResult = PROBE_OK,
    static_dir: Path = NO_STATIC,
) -> TestClient:
    transport = httpx.MockTransport(handler or make_api_mock_handler()[0])
    async_client = httpx.AsyncClient(transport=transport)
    application = create_app(
        app_settings=test_settings,
        http_client=async_client,
        probe_result=probe_result,
        static_dir=static_dir,
    )
    return TestClient(application, raise_server_exceptions=True)


@pytest.fixture
def client(test_settings: Settings):
    handler, _ = make_api_mock_handler(route_count=3)
    with _build_client(test_settings, handler=handler) as test_client:
        yield test_client


@pytest.fixture
def client_probe_failed(test_settings: Settings):
    handler, _ = make_api_mock_handler(route_count=1)
    with _build_client(
        test_settings,
        handler=handler,
        probe_result=PROBE_FAILED,
    ) as test_client:
        yield test_client
