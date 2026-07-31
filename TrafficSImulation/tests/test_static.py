from pathlib import Path

import httpx
import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.map.health import ProbeResult
from main import create_app
from tests.conftest import BROWSER_KEY, SERVER_KEY
from tests.google_mocks import make_api_mock_handler


@pytest.fixture
def static_app(tmp_path: Path):
    dist = tmp_path / "dist"
    dist.mkdir()
    (dist / "index.html").write_text("<html>TrafficScope</html>", encoding="utf-8")
    (dist / "app.js").write_text("console.log('ok');", encoding="utf-8")
    outside = tmp_path / "outside.txt"
    outside.write_text("secret", encoding="utf-8")

    handler, _ = make_api_mock_handler(route_count=1)
    async_client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    application = create_app(
        app_settings=Settings(
            google_maps_api_key=SERVER_KEY,
            google_maps_browser_api_key=BROWSER_KEY,
        ),
        http_client=async_client,
        probe_result=ProbeResult(
            ok=True,
            message="Places and Routes reachable.",
            checked_at="2026-07-30T21:00:00Z",
        ),
        static_dir=dist,
    )
    with TestClient(application) as test_client:
        yield test_client


def test_t42_spa_fallback_refuses_paths_outside_dist(static_app: TestClient) -> None:
    response = static_app.get("/%2e%2e/outside.txt")

    assert response.status_code == 404
    assert "secret" not in response.text


def test_t42_spa_fallback_serves_files_inside_dist(static_app: TestClient) -> None:
    response = static_app.get("/app.js")

    assert response.status_code == 200
    assert "console.log" in response.text


def test_t42_spa_fallback_serves_index_for_unknown_in_dist_paths(
    static_app: TestClient,
) -> None:
    response = static_app.get("/unknown/route")

    assert response.status_code == 200
    assert "TrafficScope" in response.text
