import asyncio
import logging
import time

from app.api.errors import SameOriginDestinationError
from app.api.mode_policy import ModePolicy, resolve_mode_policy
from app.api.models import (
    PlanRequest,
    PlanResponse,
    PriceFactors,
    RoadSegment,
    RouteOption,
    Scenario,
    WeatherState,
)
from app.config import (
    PLACE_MATCH_TOLERANCE_DEGREES,
    ROUTE_COLORS,
    ROUTE_CONGESTION_FLOOR,
    ROUTE_CONGESTION_INDEX_STEP,
    ROUTE_NAMES,
    ROUTE_OBJECTIVES,
    Settings,
)
from app.map.bounds import bounds_for_points, union_bounds
from app.map.places import GooglePlacesGateway
from app.map.routing import GoogleRoutesGateway
from app.map.types import RawRoute, ResolvedPlace
from app.pricing.model import PricingModel
from app.simulation.scoring import RouteScorer
from app.simulation.segments import SegmentBuilder
from app.weather.service import WeatherService

logger = logging.getLogger(__name__)


class PlanningService:
    def __init__(
        self,
        places: GooglePlacesGateway,
        routing: GoogleRoutesGateway,
        weather: WeatherService,
        segments: SegmentBuilder,
        pricing: PricingModel,
        scorer: RouteScorer,
        settings: Settings,
    ) -> None:
        self._places = places
        self._routing = routing
        self._weather = weather
        self._segments = segments
        self._pricing = pricing
        self._scorer = scorer
        self._settings = settings

    async def plan(self, request: PlanRequest) -> PlanResponse:
        started = time.perf_counter()
        policy = resolve_mode_policy(request.mode)
        scenario = policy.effective_scenario(request)
        origin, destination = await self._resolve_endpoints(
            request.origin,
            request.destination,
        )
        raw_routes = await self._routing.compute(
            origin,
            destination,
            policy.departure_time(scenario),
            policy.alternatives > 1,
        )
        weather = self._to_weather_state(
            self._weather.state(scenario.weather)
        )
        routes = [
            self._build_route_option(
                policy,
                scenario,
                weather,
                raw_route,
                index,
            )
            for index, raw_route in enumerate(raw_routes)
        ]
        scored_routes = self._scorer.score(routes)
        recommended_route_id = self._scorer.recommend(scored_routes)
        response = self._assemble_response(
            origin=origin,
            destination=destination,
            policy=policy,
            scenario=scenario,
            weather=weather,
            routes=scored_routes,
            recommended_route_id=recommended_route_id,
        )
        logger.info(
            "Plan completed mode=%s scenario=%s alternatives=%s duration_ms=%.1f",
            response.mode,
            scenario.model_dump(),
            len(response.routes),
            (time.perf_counter() - started) * 1000,
        )
        return response

    async def _resolve_endpoints(
        self,
        origin_text: str,
        destination_text: str,
    ) -> tuple[ResolvedPlace, ResolvedPlace]:
        origin, destination = await asyncio.gather(
            self._places.resolve(origin_text),
            self._places.resolve(destination_text),
        )
        if _same_place(origin, destination):
            raise SameOriginDestinationError
        return origin, destination

    def _build_route_option(
        self,
        policy: ModePolicy,
        scenario: Scenario,
        weather: WeatherState,
        raw_route: RawRoute,
        route_index: int,
    ) -> RouteOption:
        congestion_score = max(
            ROUTE_CONGESTION_FLOOR,
            scenario.congestion - route_index * ROUTE_CONGESTION_INDEX_STEP,
        )
        built_segments = self._segments.build(
            raw_route,
            scenario.congestion,
            route_index,
        )
        api_segments = [
            RoadSegment.model_validate(segment, from_attributes=True)
            for segment in built_segments
        ]
        adjusted_eta_raw = policy.adjusted_eta(
            raw_route,
            weather,
            api_segments,
        )
        price_estimate = self._pricing.estimate(
            distance_miles=raw_route.distance_miles,
            minutes=adjusted_eta_raw,
            congestion_score=congestion_score,
            weather_price_multiplier=weather.price_multiplier,
            time_multiplier=policy.pricing_time_multiplier(scenario),
        )
        return RouteOption(
            id=f"route-{route_index + 1}",
            name=ROUTE_NAMES[route_index],
            objective=ROUTE_OBJECTIVES[route_index],
            color=ROUTE_COLORS[route_index],
            distance_miles=raw_route.distance_miles,
            base_eta_minutes=_base_eta_minutes(
                raw_route,
                adjusted_eta_raw,
                weather,
            ),
            adjusted_eta_minutes=round(adjusted_eta_raw, 1),
            estimated_price=price_estimate.estimated_price,
            congestion_score=congestion_score,
            normalized_score=0.0,
            data_source=policy.data_source(),
            polyline=raw_route.polyline,
            traffic_intervals=raw_route.traffic_intervals,
            segments=api_segments,
            price_factors=PriceFactors.model_validate(
                price_estimate.price_factors,
                from_attributes=True,
            ),
            bounds=bounds_for_points(raw_route.polyline),
        )

    def _assemble_response(
        self,
        *,
        origin: ResolvedPlace,
        destination: ResolvedPlace,
        policy: ModePolicy,
        scenario: Scenario,
        weather: WeatherState,
        routes: list[RouteOption],
        recommended_route_id: str,
    ) -> PlanResponse:
        return PlanResponse(
            origin=origin.name,
            destination=destination.name,
            mode=policy.mode,
            scenario_applied=policy.scenario_applied,
            scenario=scenario,
            weather=weather,
            routes=routes,
            recommended_route_id=recommended_route_id,
            map_bounds=union_bounds([route.bounds for route in routes]),
            notice=policy.notice(),
        )

    @staticmethod
    def _to_weather_state(state: object) -> WeatherState:
        return WeatherState.model_validate(state, from_attributes=True)


def _same_place(origin: ResolvedPlace, destination: ResolvedPlace) -> bool:
    return (
        abs(origin.latitude - destination.latitude)
        <= PLACE_MATCH_TOLERANCE_DEGREES
        and abs(origin.longitude - destination.longitude)
        <= PLACE_MATCH_TOLERANCE_DEGREES
    )


def _base_eta_minutes(
    route: RawRoute,
    adjusted_eta_raw: float,
    weather: WeatherState,
) -> float:
    seconds = route.static_duration_seconds
    if seconds is None:
        seconds = route.duration_seconds
    if seconds is not None:
        return round(seconds / 60, 1)
    if weather.time_multiplier:
        return round(adjusted_eta_raw / weather.time_multiplier, 1)
    return round(adjusted_eta_raw, 1)


__all__ = ["PlanningService"]

