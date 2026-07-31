from typing import Annotated

import httpx
from fastapi import Depends, Request

from app.api.planning import PlanningService
from app.config import Settings, settings
from app.map.health import ProbeResult
from app.map.place_cache import PlaceResolutionCache
from app.map.places import GooglePlacesGateway
from app.map.routing import GoogleRoutesGateway
from app.pricing.model import PricingModel
from app.simulation.scoring import RouteScorer
from app.simulation.segments import SegmentBuilder
from app.weather.service import WeatherService


def get_settings(request: Request) -> Settings:
    return getattr(request.app.state, "settings", settings)


def get_http_client(request: Request) -> httpx.AsyncClient:
    return request.app.state.http_client


def get_probe_result(request: Request) -> ProbeResult:
    return request.app.state.probe_result


def get_place_cache(request: Request) -> PlaceResolutionCache:
    cache = getattr(request.app.state, "place_cache", None)
    if cache is None:
        cache = PlaceResolutionCache()
        request.app.state.place_cache = cache
    return cache


def build_planning_service(
    client: httpx.AsyncClient,
    app_settings: Settings | None = None,
    place_cache: PlaceResolutionCache | None = None,
) -> PlanningService:
    resolved_settings = app_settings or settings
    cache = place_cache or PlaceResolutionCache()
    return PlanningService(
        places=GooglePlacesGateway(resolved_settings, client, cache),
        routing=GoogleRoutesGateway(resolved_settings, client),
        weather=WeatherService(),
        segments=SegmentBuilder(),
        pricing=PricingModel(),
        scorer=RouteScorer(),
        settings=resolved_settings,
    )


def get_planning_service(
    client: Annotated[httpx.AsyncClient, Depends(get_http_client)],
    app_settings: Annotated[Settings, Depends(get_settings)],
    place_cache: Annotated[PlaceResolutionCache, Depends(get_place_cache)],
) -> PlanningService:
    return build_planning_service(client, app_settings, place_cache)


__all__ = [
    "build_planning_service",
    "get_http_client",
    "get_place_cache",
    "get_planning_service",
    "get_probe_result",
    "get_settings",
]
