import pytest

from app.config import GOOGLE_MAPS_API_KEY
from app.map.google_startup_check import verify_google_maps


@pytest.mark.skipif(not GOOGLE_MAPS_API_KEY, reason="GOOGLE_MAPS_API_KEY not set in .env")
def test_google_maps_startup_probe():
    status = verify_google_maps()
    assert status["configured"] is True
    assert status["places_ok"] is True, status.get("places_message", status.get("message"))
    assert status["routes_ok"] is True, status.get("routes_message", status.get("message"))
    assert status["ok"] is True, status.get("message")
