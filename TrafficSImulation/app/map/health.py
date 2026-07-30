import logging
from dataclasses import dataclass
from datetime import datetime, timezone

import httpx

from app.config import HEALTH_PROBE_CACHE_SECONDS, Settings
from app.map.errors import (
    InvalidLocationError,
    MapsNotConfiguredError,
    NoRouteFoundError,
    UpstreamTimeoutError,
    UpstreamUnavailableError,
)
from app.map.places import GooglePlacesGateway
from app.map.routing import GoogleRoutesGateway

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class ProbeResult:
    ok: bool
    message: str
    checked_at: str


class GoogleApiProbe:
    def __init__(
        self,
        settings: Settings,
        client: httpx.AsyncClient,
    ) -> None:
        self._settings = settings
        self._places = GooglePlacesGateway(settings, client)
        self._routes = GoogleRoutesGateway(settings, client)
        self._cached_result: ProbeResult | None = None
        self._cached_at: datetime | None = None

    async def check(self) -> ProbeResult:
        now = datetime.now(timezone.utc)
        cached_result = self._cached_result
        if cached_result is not None and self._cache_is_fresh(now):
            return cached_result

        try:
            result = await self._run_check(now)
        except Exception:
            result = ProbeResult(
                ok=False,
                message="Google API reachability check failed.",
                checked_at=now.isoformat().replace("+00:00", "Z"),
            )
        self._cached_result = result
        self._cached_at = now
        if not result.ok:
            logger.warning("Google API probe failed: %s", result.message)
        return result

    def _cache_is_fresh(self, now: datetime) -> bool:
        if self._cached_result is None or self._cached_at is None:
            return False
        return (
            now - self._cached_at
        ).total_seconds() < HEALTH_PROBE_CACHE_SECONDS

    async def _run_check(self, now: datetime) -> ProbeResult:
        checked_at = now.isoformat().replace("+00:00", "Z")
        if not self._settings.google_maps_configured:
            return ProbeResult(
                ok=False,
                message="The server Google credential is not configured.",
                checked_at=checked_at,
            )

        try:
            origin = await self._places.resolve("Downtown Austin, TX")
            destination = await self._places.resolve(
                "Austin-Bergstrom International Airport, TX"
            )
        except UpstreamTimeoutError:
            return ProbeResult(False, "Places service timed out.", checked_at)
        except (
            InvalidLocationError,
            MapsNotConfiguredError,
            UpstreamUnavailableError,
        ):
            return ProbeResult(False, "Places service check failed.", checked_at)

        try:
            await self._routes.compute(
                origin,
                destination,
                now,
                alternatives=False,
            )
        except UpstreamTimeoutError:
            return ProbeResult(False, "Routes service timed out.", checked_at)
        except (
            MapsNotConfiguredError,
            NoRouteFoundError,
            UpstreamUnavailableError,
        ):
            return ProbeResult(False, "Routes service check failed.", checked_at)

        return ProbeResult(
            ok=True,
            message="Places and Routes reachable.",
            checked_at=checked_at,
        )
