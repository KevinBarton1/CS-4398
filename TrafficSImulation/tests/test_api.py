import json

import httpx
import pytest
from fastapi.testclient import TestClient

from app.config import (
    MAP_COLOR_SCHEME,
    MAP_DEFAULT_CENTER,
    MAP_DEFAULT_ZOOM,
    MAP_LIBRARIES,
    NOTICE_REALTIME,
    NOTICE_SIMULATED,
    SERVICE_NAME,
    SERVICE_VERSION,
    Settings,
)
from tests.conftest import (
    BROWSER_KEY,
    PROBE_FAILED,
    PROBE_OK,
    SERVER_KEY,
    _build_client,
    test_settings,
)
from tests.google_mocks import make_api_mock_handler

PLAN_PAYLOAD = {
    "origin": "Downtown Austin",
    "destination": "Austin Airport",
    "mode": "simulated",
    "hour": 17,
    "weather": 1,
    "congestion": 56,
}


def test_t01_simulated_happy_path(client: TestClient) -> None:
    response = client.post("/api/plan", json=PLAN_PAYLOAD)

    assert response.status_code == 200
    body = response.json()
    assert body["mode"] == "simulated"
    assert body["scenario_applied"] is True
    assert body["scenario"] == {
        "hour": 17,
        "weather": 1,
        "congestion": 56,
    }
    assert body["notice"] == NOTICE_SIMULATED
    assert 1 <= len(body["routes"]) <= 3
    assert body["recommended_route_id"] in {
        route["id"] for route in body["routes"]
    }
    assert body["map_bounds"]
    for route in body["routes"]:
        assert route["objective"]
        assert route["segments"]
        assert route["price_factors"]["unrounded_total"] > 0
        assert "factors" not in route
    assert SERVER_KEY not in json.dumps(body)
    assert "maps_api_key" not in body


def test_t02_realtime_happy_path(test_settings: Settings) -> None:
    handler, _ = make_api_mock_handler(route_count=3)
    with _build_client(test_settings, handler=handler) as test_client:
        response = test_client.post(
            "/api/plan",
            json={
                "origin": "Downtown Austin",
                "destination": "Austin Airport",
                "mode": "realtime",
                "hour": 9,
                "weather": 3,
                "congestion": 90,
            },
        )

        assert response.status_code == 200
        body = response.json()
        assert body["mode"] == "realtime"
        assert body["scenario_applied"] is False
        assert len(body["routes"]) == 1
        assert body["notice"] == NOTICE_REALTIME
        assert body["scenario"]["weather"] == 0
        assert body["scenario"]["congestion"] == 0


def test_t03_out_of_range_scenario_returns_validation_error(
    client: TestClient,
) -> None:
    response = client.post(
        "/api/plan",
        json={**PLAN_PAYLOAD, "weather": 99},
    )

    assert response.status_code == 422
    body = response.json()
    assert body["code"] == "validation_error"
    assert body["detail"] == "Request validation failed."
    assert any(field["field"] == "weather" for field in body["fields"])


def test_t04_unresolvable_location_returns_invalid_location(
    test_settings: Settings,
) -> None:
    handler, _ = make_api_mock_handler(places_empty=True)
    with _build_client(test_settings, handler=handler) as test_client:
        response = test_client.post("/api/plan", json=PLAN_PAYLOAD)

        assert response.status_code == 400
        assert response.json()["code"] == "invalid_location"


def test_t05_same_origin_destination_skips_routing(test_settings: Settings) -> None:
    handler, counters = make_api_mock_handler(same_place=True)
    with _build_client(test_settings, handler=handler) as test_client:
        response = test_client.post(
            "/api/plan",
            json={
                "origin": "Same Spot",
                "destination": "Same Spot",
                "mode": "simulated",
            },
        )

        assert response.status_code == 400
        assert response.json()["code"] == "same_origin_destination"
        assert counters["routes"] == 0


def test_t06_zero_alternatives_returns_no_route_found(
    test_settings: Settings,
) -> None:
    handler, _ = make_api_mock_handler(routes_empty=True)
    with _build_client(test_settings, handler=handler) as test_client:
        response = test_client.post("/api/plan", json=PLAN_PAYLOAD)

        assert response.status_code == 400
        assert response.json()["code"] == "no_route_found"


def test_t07_absent_server_credential_returns_maps_not_configured() -> None:
    handler, _ = make_api_mock_handler(route_count=1)
    with _build_client(
        Settings(
            google_maps_api_key="",
            google_maps_browser_api_key=BROWSER_KEY,
        ),
        handler=handler,
    ) as test_client:
        response = test_client.post("/api/plan", json=PLAN_PAYLOAD)

        assert response.status_code == 503
        body = response.json()
        assert body["code"] == "maps_not_configured"
        assert SERVER_KEY not in json.dumps(body)


def test_t08_upstream_error_returns_sanitized_detail(test_settings: Settings) -> None:
    handler, _ = make_api_mock_handler(upstream_status=403)
    with _build_client(test_settings, handler=handler) as test_client:
        response = test_client.post("/api/plan", json=PLAN_PAYLOAD)

        assert response.status_code == 502
        body = response.json()
        assert body["code"] == "upstream_unavailable"
        assert "private upstream body" not in response.text
        assert "googleapis.com" not in response.text


def test_t09_upstream_timeout_returns_upstream_timeout(
    test_settings: Settings,
) -> None:
    handler, _ = make_api_mock_handler(timeout=True)
    with _build_client(test_settings, handler=handler) as test_client:
        response = test_client.post("/api/plan", json=PLAN_PAYLOAD)

        assert response.status_code == 504
        assert response.json()["code"] == "upstream_timeout"


def test_t10_health_response_shape(client: TestClient) -> None:
    response = client.get("/api/health")

    assert response.status_code == 200
    body = response.json()
    assert body == {
        "status": "ok",
        "service": SERVICE_NAME,
        "version": SERVICE_VERSION,
        "google_maps_configured": True,
        "google_maps": {
            "ok": PROBE_OK.ok,
            "message": PROBE_OK.message,
            "checked_at": PROBE_OK.checked_at,
        },
    }


def test_t10_health_reports_failed_probe_without_error_status(
    client_probe_failed: TestClient,
) -> None:
    response = client_probe_failed.get("/api/health")

    assert response.status_code == 200
    assert response.json()["google_maps"] == {
        "ok": PROBE_FAILED.ok,
        "message": PROBE_FAILED.message,
        "checked_at": PROBE_FAILED.checked_at,
    }


def test_t11_map_config_returns_browser_key_and_map_constants(
    client: TestClient,
) -> None:
    response = client.get("/api/map/config")

    assert response.status_code == 200
    body = response.json()
    assert body["maps_browser_api_key"] == BROWSER_KEY
    assert "maps_api_key" not in body
    assert body["map_id"] is None
    assert body["default_center"] == MAP_DEFAULT_CENTER
    assert body["default_zoom"] == MAP_DEFAULT_ZOOM
    assert body["color_scheme"] == MAP_COLOR_SCHEME
    assert body["libraries"] == MAP_LIBRARIES
    assert SERVER_KEY not in json.dumps(body)


def test_t11_map_config_without_browser_key_returns_503(
    test_settings: Settings,
) -> None:
    handler, _ = make_api_mock_handler(route_count=1)
    with _build_client(
        Settings(
            google_maps_api_key=SERVER_KEY,
            google_maps_browser_api_key="",
        ),
        handler=handler,
    ) as test_client:
        response = test_client.get("/api/map/config")

        assert response.status_code == 503
        assert response.json()["code"] == "maps_not_configured"


def test_t41_heatmap_happy_path(client: TestClient) -> None:
    response = client.post("/api/heatmap", json={"hour": 17, "congestion": 56})

    assert response.status_code == 200
    body = response.json()
    assert body["metric"] == "congestion"
    assert body["rows"] == 5
    assert body["columns"] == 8
    assert len(body["cells"]) == 40
    assert body["scenario"] == {"hour": 17, "weather": 0, "congestion": 56}
    assert body["bounds"]["north"] > body["bounds"]["south"]
    assert body["notice"]
    first = body["cells"][0]
    assert {"row", "column", "value", "bounds"} <= set(first.keys())
    assert 0 <= first["value"] <= 100


def test_t41_heatmap_out_of_range_hour_returns_validation_error(client: TestClient) -> None:
    response = client.post("/api/heatmap", json={"hour": 99, "congestion": 56})

    assert response.status_code == 422
    assert response.json()["code"] == "validation_error"
