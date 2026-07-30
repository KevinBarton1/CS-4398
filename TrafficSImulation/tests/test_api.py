from unittest.mock import patch

from fastapi.testclient import TestClient

from main import app
from tests.google_mocks import mock_build_route_options


client = TestClient(app)


def test_health_endpoint():
    response = client.get("/api/health")
    assert response.status_code == 200
    body = response.json()
    assert body["version"] == "1.1"
    assert "google_maps_configured" in body
    assert isinstance(body["google_maps_configured"], bool)
    assert "google_maps" in body
    assert "ok" in body["google_maps"]
    assert "message" in body["google_maps"]


@patch("app.api.routes.build_route_options", side_effect=mock_build_route_options)
def test_typed_plan_endpoint(_mock_build):
    response = client.post("/api/plan", json={
        "origin": "Downtown Austin",
        "destination": "Austin Airport",
        "mode": "simulated",
        "hour": 17,
        "weather": 1,
        "congestion": 56,
        "demand": 68,
    })
    assert response.status_code == 200
    result = response.json()
    assert len(result["routes"]) == 3
    assert all(route["objective"] for route in result["routes"])
    assert all("unrounded_total" in route["factors"] for route in result["routes"])
    assert "Google Maps" in result["notice"]
    assert result["map_embed_url"] is None or result["map_embed_url"].startswith("https://www.google.com/maps/embed/v1/view")
    assert "map_view" in result
    assert "center_lat" in result["map_view"]
    assert all("polyline" in route for route in result["routes"])
    assert all("map_view" in route for route in result["routes"])
    assert all("map_embed_url" in route for route in result["routes"])


def test_out_of_range_scenario_is_rejected():
    response = client.post("/api/plan", json={
        "origin": "Downtown Austin",
        "destination": "Austin Airport",
        "weather": 99,
    })
    assert response.status_code == 422


@patch("app.map.google_embed.GOOGLE_MAPS_API_KEY", "test-key")
def test_map_embed_endpoint():
    response = client.post("/api/map/embed", json={
        "center_lat": 30.2324,
        "center_lng": -97.7048,
        "zoom": 13,
    })
    assert response.status_code == 200
    body = response.json()
    assert body["map_embed_url"].startswith("https://www.google.com/maps/embed/v1/view")
    assert "center=30.2324%2C-97.7048" in body["map_embed_url"]
    assert "zoom=13" in body["map_embed_url"]
