from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.dependencies import get_planning_service, get_probe_result, get_settings
from app.api.models import (
    HealthResponse,
    MapConfigResponse,
    PlanRequest,
    PlanResponse,
)
from app.api.planning import PlanningService
from app.config import (
    MAP_COLOR_SCHEME,
    MAP_DEFAULT_CENTER,
    MAP_DEFAULT_ZOOM,
    MAP_LIBRARIES,
    SERVICE_NAME,
    SERVICE_VERSION,
    Settings,
)
from app.map.errors import MapsNotConfiguredError
from app.map.health import ProbeResult
from app.map.types import LatLngPoint

router = APIRouter(prefix="/api")


@router.post("/plan")
async def plan_trip(
    request: PlanRequest,
    planner: Annotated[PlanningService, Depends(get_planning_service)],
) -> PlanResponse:
    return await planner.plan(request)


@router.get("/health")
async def health(
    app_settings: Annotated[Settings, Depends(get_settings)],
    probe: Annotated[ProbeResult, Depends(get_probe_result)],
) -> HealthResponse:
    return HealthResponse(
        status="ok",
        service=SERVICE_NAME,
        version=SERVICE_VERSION,
        google_maps_configured=app_settings.google_maps_configured,
        google_maps=probe,
    )


@router.get("/map/config")
async def map_config(
    app_settings: Annotated[Settings, Depends(get_settings)],
) -> MapConfigResponse:
    browser_key = app_settings.google_maps_browser_api_key.strip()
    if not browser_key:
        raise MapsNotConfiguredError
    return MapConfigResponse(
        maps_browser_api_key=browser_key,
        map_id=app_settings.google_maps_map_id,
        default_center=LatLngPoint(**MAP_DEFAULT_CENTER),
        default_zoom=MAP_DEFAULT_ZOOM,
        color_scheme=MAP_COLOR_SCHEME,
        libraries=list(MAP_LIBRARIES),
    )


__all__ = ["router"]
