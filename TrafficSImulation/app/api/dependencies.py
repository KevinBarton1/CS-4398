import httpx

from app.api.planning import PlanningService
from app.config import Settings, settings
from app.map.places import GooglePlacesGateway
from app.map.routing import GoogleRoutesGateway
from app.pricing.model import PricingModel
from app.simulation.scoring import RouteScorer
from app.simulation.segments import SegmentBuilder
from app.weather.service import WeatherService


def build_planning_service(
    client: httpx.AsyncClient,
    app_settings: Settings | None = None,
) -> PlanningService:
    resolved_settings = app_settings or settings
    return PlanningService(
        places=GooglePlacesGateway(resolved_settings, client),
        routing=GoogleRoutesGateway(resolved_settings, client),
        weather=WeatherService(),
        segments=SegmentBuilder(),
        pricing=PricingModel(),
        scorer=RouteScorer(),
        settings=resolved_settings,
    )


__all__ = ["build_planning_service"]
