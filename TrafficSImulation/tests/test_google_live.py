"""T-57: Opt-in live Google credential probe."""

import httpx
import pytest

from app.config import settings
from app.map.health import GoogleApiProbe

# Default suite excludes this module via pytest.ini: addopts = -m "not live"
# Opt in with: pytest -m live tests/test_google_live.py
# Or run the full live slice: pytest -m live


@pytest.mark.live
@pytest.mark.asyncio
async def test_t57_live_google_probe_reaches_places_and_routes() -> None:
    if not settings.google_maps_configured:
        pytest.skip("GOOGLE_MAPS_API_KEY is not configured")

    async with httpx.AsyncClient() as client:
        result = await GoogleApiProbe(settings, client).check()

    assert result.ok is True, result.message
    assert result.checked_at.endswith("Z")
