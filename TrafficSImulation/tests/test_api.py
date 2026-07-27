from fastapi.testclient import TestClient

from main import app


client = TestClient(app)


def test_health_endpoint():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["version"] == "1.1"


def test_typed_plan_endpoint():
    response = client.post("/api/plan", json={
        "origin": "Downtown Austin",
        "destination": "Austin Airport",
        "mode": "simulated",
        "heatmap": "congestion",
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


def test_out_of_range_scenario_is_rejected():
    response = client.post("/api/plan", json={
        "origin": "Downtown Austin",
        "destination": "Austin Airport",
        "weather": 99,
    })
    assert response.status_code == 422
