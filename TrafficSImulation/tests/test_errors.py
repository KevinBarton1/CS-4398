import logging

from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.api.errors import (
    InvalidLocationError,
    MapsNotConfiguredError,
    NoRouteFoundError,
    SameOriginDestinationError,
    UpstreamTimeoutError,
    UpstreamUnavailableError,
    register_exception_handlers,
)
from app.api.models import PlanRequest


def test_t49_upstream_error_response_and_log_are_sanitized(caplog) -> None:
    app = FastAPI()
    register_exception_handlers(app)

    @app.get("/failure")
    async def failure() -> None:
        raise UpstreamUnavailableError("Routes")

    forbidden = (
        "Traceback",
        ".py",
        "googleapis.com",
        "secret-api-key",
    )
    with caplog.at_level(logging.INFO):
        response = TestClient(app).get("/failure")

    assert response.status_code == 502
    assert response.json() == {
        "detail": "The Google Routes service returned an error. Try again shortly.",
        "code": "upstream_unavailable",
    }
    assert all(value not in response.text for value in forbidden)
    messages = "".join(
        record.getMessage()
        for record in caplog.records
        if record.name == "app.api.errors"
    )
    assert "Traceback" not in messages
    assert "googleapis.com" not in messages
    assert "secret-api-key" not in messages


def test_domain_error_catalog_declares_locked_codes_and_statuses() -> None:
    assert [
        (error.code, error.status)
        for error in (
            InvalidLocationError,
            SameOriginDestinationError,
            NoRouteFoundError,
            MapsNotConfiguredError,
            UpstreamUnavailableError,
            UpstreamTimeoutError,
        )
    ] == [
        ("invalid_location", 400),
        ("same_origin_destination", 400),
        ("no_route_found", 400),
        ("maps_not_configured", 503),
        ("upstream_unavailable", 502),
        ("upstream_timeout", 504),
    ]


def test_validation_handler_flattens_fields_into_locked_envelope() -> None:
    app = FastAPI()
    register_exception_handlers(app)

    @app.post("/plan")
    async def plan(_: PlanRequest) -> None:
        return None

    response = TestClient(app).post(
        "/plan",
        json={
            "origin": "   ",
            "destination": "Austin Airport",
            "weather": 99,
            "retired": True,
        },
    )

    assert response.status_code == 422
    assert response.json()["detail"] == "Request validation failed."
    assert response.json()["code"] == "validation_error"
    assert {item["field"] for item in response.json()["fields"]} == {
        "origin",
        "weather",
        "retired",
    }


def test_plan_request_trims_text_and_uses_documented_defaults() -> None:
    request = PlanRequest(origin=" Downtown ", destination=" Airport ")

    assert request.model_dump() == {
        "origin": "Downtown",
        "destination": "Airport",
        "mode": "simulated",
        "hour": 17,
        "weather": 1,
        "congestion": 56,
    }


def test_plan_request_rejects_an_unknown_mode() -> None:
    try:
        PlanRequest(
            origin="Downtown",
            destination="Airport",
            mode="reference",
        )
    except ValidationError as error:
        assert error.errors()[0]["loc"] == ("mode",)
    else:
        raise AssertionError("Unknown modes must be rejected.")
