import asyncio
from unittest.mock import patch

import httpx
import pytest

from app.api.errors import SameOriginDestinationError
from app.api.mode_policy import SimulatedModePolicy
from app.api.models import PlanRequest, RoadSegment, Scenario
from app.api.planning import PlanningService
from app.api.dependencies import build_planning_service
from app.config import (
    ETA_FALLBACK_BUFFER_MINUTES,
    ROUTE_CONGESTION_FLOOR,
    Settings,
)
from app.map.place_cache import PlaceResolutionCache
from app.map.places import GooglePlacesGateway
from app.map.types import LatLngPoint, RawRoute, ResolvedPlace, RouteBounds
from app.pricing.model import PricingModel
from app.simulation.scoring import RouteScorer
from app.simulation.segments import RoadSegment as SegmentRoadSegment
from app.simulation.segments import SegmentBuilder
from app.weather.service import WeatherService
from tests.google_mocks import make_api_mock_handler, make_mock_async_client


def _request(**overrides: object) -> PlanRequest:
    payload = {
        "origin": "Downtown Austin",
        "destination": "Austin Airport",
        "mode": "simulated",
        "hour": 17,
        "weather": 2,
        "congestion": 56,
    }
    payload.update(overrides)
    return PlanRequest(**payload)


def _place(name: str, lat: float = 30.2672, lng: float = -97.7431) -> ResolvedPlace:
    return ResolvedPlace(
        name=name,
        latitude=lat,
        longitude=lng,
        source="google",
    )


def _route(
    *,
    duration_seconds: float | None = 1200.0,
    static_duration_seconds: float | None = 900.0,
    route_id: str = "route-1",
) -> RawRoute:
    return RawRoute(
        id=route_id,
        distance_miles=7.0,
        duration_seconds=duration_seconds,
        static_duration_seconds=static_duration_seconds,
        traffic_ratio=1.25,
        polyline=[
            LatLngPoint(lat=30.2672, lng=-97.7431),
            LatLngPoint(lat=30.1975, lng=-97.6664),
        ],
        traffic_intervals=[],
        steps=[],
    )


def _simulation_segment(adjusted_minutes: float) -> SegmentRoadSegment:
    return SegmentRoadSegment(
        name="I-35",
        length_miles=3.2,
        lanes=3,
        speed_limit_mph=55,
        average_speed_mph=42.0,
        volume_vehicles_hour=1200,
        congestion=0.45,
        capacity_vehicles_hour=1560,
        free_flow_minutes=4.2,
        adjusted_minutes=adjusted_minutes,
        traffic_ratio=1.15,
        polyline=[LatLngPoint(lat=30.2672, lng=-97.7431)],
    )


class RecordingPlacesGateway:
    def __init__(
        self,
        origin: ResolvedPlace,
        destination: ResolvedPlace,
        log: list[str],
    ) -> None:
        self._origin = origin
        self._destination = destination
        self._log = log
        self.in_flight = 0
        self.max_in_flight = 0
        self._lock = asyncio.Lock()

    async def resolve(self, query: str) -> ResolvedPlace:
        self._log.append(f"places:{query}")
        async with self._lock:
            self.in_flight += 1
            self.max_in_flight = max(self.max_in_flight, self.in_flight)
        await asyncio.sleep(0.02)
        async with self._lock:
            self.in_flight -= 1
        if query == _request().origin:
            return self._origin
        return self._destination


class RecordingRoutesGateway:
    def __init__(self, routes: list[RawRoute], log: list[str]) -> None:
        self._routes = routes
        self._log = log
        self.call_count = 0

    async def compute(self, origin, destination, departure, alternatives) -> list[RawRoute]:
        del origin, destination, departure, alternatives
        self._log.append("routing")
        self.call_count += 1
        return self._routes


class RecordingWeatherService:
    def __init__(self, log: list[str]) -> None:
        self._log = log

    def state(self, severity: int):
        self._log.append("weather")
        return WeatherService().state(severity)


class RecordingSegmentBuilder:
    def __init__(self, log: list[str], inner: SegmentBuilder | None = None) -> None:
        self._log = log
        self._inner = inner or SegmentBuilder()

    def build(self, route, congestion, route_index):
        self._log.append("segments")
        return self._inner.build(route, congestion, route_index)


class RecordingPricingModel:
    def __init__(self, log: list[str]) -> None:
        self._log = log
        self._inner = PricingModel()

    def estimate(self, **kwargs):
        self._log.append("pricing")
        return self._inner.estimate(**kwargs)


class RecordingRouteScorer:
    def __init__(self, log: list[str]) -> None:
        self._log = log
        self._inner = RouteScorer()

    def score(self, routes):
        self._log.append("score")
        return self._inner.score(routes)

    def recommend(self, routes):
        self._log.append("recommend")
        return self._inner.recommend(routes)


class RecordingSimulatedModePolicy(SimulatedModePolicy):
    def __init__(self, log: list[str]) -> None:
        self._log = log

    def effective_scenario(self, request: PlanRequest) -> Scenario:
        self._log.append("effective_scenario")
        return super().effective_scenario(request)

    def adjusted_eta(self, route, weather, segments):
        self._log.append("adjusted_eta")
        return super().adjusted_eta(route, weather, segments)


def _planning_service(
    *,
    places: RecordingPlacesGateway,
    routing: RecordingRoutesGateway,
    log: list[str],
    segments: RecordingSegmentBuilder | None = None,
) -> PlanningService:
    return PlanningService(
        places=places,
        routing=routing,
        weather=RecordingWeatherService(log),
        segments=segments or RecordingSegmentBuilder(log),
        pricing=RecordingPricingModel(log),
        scorer=RecordingRouteScorer(log),
        settings=Settings(google_maps_api_key="test-key"),
    )


@pytest.mark.asyncio
async def test_t23_workflow_steps_run_in_documented_order() -> None:
    log: list[str] = []
    policy = RecordingSimulatedModePolicy(log)
    places = RecordingPlacesGateway(
        _place("Downtown Austin"),
        _place("Austin Airport", lat=30.1975, lng=-97.6664),
        log,
    )
    routing = RecordingRoutesGateway([_route()], log)
    service = _planning_service(places=places, routing=routing, log=log)

    def resolve_policy(_mode: str):
        log.append("resolve_mode_policy")
        return policy

    with patch(
        "app.api.planning.resolve_mode_policy",
        side_effect=resolve_policy,
    ):
        await service.plan(_request())

    assert log == [
        "resolve_mode_policy",
        "effective_scenario",
        f"places:{_request().origin}",
        f"places:{_request().destination}",
        "routing",
        "weather",
        "segments",
        "adjusted_eta",
        "pricing",
        "score",
        "recommend",
    ]


@pytest.mark.asyncio
async def test_t23_places_resolutions_run_concurrently() -> None:
    log: list[str] = []
    places = RecordingPlacesGateway(
        _place("Downtown Austin"),
        _place("Austin Airport", lat=30.1975, lng=-97.6664),
        log,
    )
    routing = RecordingRoutesGateway([_route()], log)
    service = _planning_service(places=places, routing=routing, log=log)

    await service.plan(_request())

    assert places.max_in_flight == 2


@pytest.mark.asyncio
async def test_t23_same_place_short_circuits_before_routing() -> None:
    log: list[str] = []
    same = _place("Same Spot")
    places = RecordingPlacesGateway(same, same, log)
    routing = RecordingRoutesGateway([_route()], log)
    service = _planning_service(places=places, routing=routing, log=log)

    with pytest.raises(SameOriginDestinationError):
        await service.plan(_request(origin="Same Spot", destination="Same Spot"))

    assert routing.call_count == 0


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("duration_seconds", "static_duration_seconds", "expected_adjusted"),
    [
        (1200.0, 900.0, round((1200.0 / 60) * 1.18, 1)),
        (None, 900.0, round((900.0 / 60) * 1.18, 1)),
        (
            None,
            None,
            round((12.5 + 8.0 + ETA_FALLBACK_BUFFER_MINUTES) * 1.18, 1),
        ),
    ],
)
async def test_t23_adjusted_eta_fallback_chain(
    duration_seconds: float | None,
    static_duration_seconds: float | None,
    expected_adjusted: float,
) -> None:
    class FixedSegmentBuilder:
        def build(self, route, congestion, route_index):
            del route, congestion, route_index
            return [_simulation_segment(12.5), _simulation_segment(8.0)]

    log: list[str] = []
    places = RecordingPlacesGateway(
        _place("Downtown Austin"),
        _place("Austin Airport", lat=30.1975, lng=-97.6664),
        log,
    )
    routing = RecordingRoutesGateway(
        [
            _route(
                duration_seconds=duration_seconds,
                static_duration_seconds=static_duration_seconds,
            )
        ],
        log,
    )
    service = PlanningService(
        places=places,
        routing=routing,
        weather=RecordingWeatherService(log),
        segments=FixedSegmentBuilder(),
        pricing=PricingModel(),
        scorer=RouteScorer(),
        settings=Settings(google_maps_api_key="test-key"),
    )

    response = await service.plan(_request())

    assert response.routes[0].adjusted_eta_minutes == pytest.approx(expected_adjusted)


@pytest.mark.asyncio
async def test_t23_recommended_route_id_matches_lowest_score() -> None:
    log: list[str] = []
    places = RecordingPlacesGateway(
        _place("Downtown Austin"),
        _place("Austin Airport", lat=30.1975, lng=-97.6664),
        log,
    )
    routing = RecordingRoutesGateway(
        [
            _route(route_id="route-1", duration_seconds=1500.0),
            _route(route_id="route-2", duration_seconds=900.0),
            _route(route_id="route-3", duration_seconds=1800.0),
        ],
        log,
    )
    service = PlanningService(
        places=places,
        routing=routing,
        weather=RecordingWeatherService(log),
        segments=SegmentBuilder(),
        pricing=PricingModel(),
        scorer=RouteScorer(),
        settings=Settings(google_maps_api_key="test-key"),
    )

    response = await service.plan(_request())

    recommended = next(
        route for route in response.routes
        if route.id == response.recommended_route_id
    )
    assert recommended.normalized_score == min(
        route.normalized_score for route in response.routes
    )


@pytest.mark.asyncio
async def test_t23_map_bounds_unions_route_bounds() -> None:
    log: list[str] = []
    places = RecordingPlacesGateway(
        _place("Downtown Austin"),
        _place("Austin Airport", lat=30.1975, lng=-97.6664),
        log,
    )
    routing = RecordingRoutesGateway([_route()], log)
    service = PlanningService(
        places=places,
        routing=routing,
        weather=RecordingWeatherService(log),
        segments=SegmentBuilder(),
        pricing=PricingModel(),
        scorer=RouteScorer(),
        settings=Settings(google_maps_api_key="test-key"),
    )

    response = await service.plan(_request())

    assert response.map_bounds == RouteBounds(
        north=max(route.bounds.north for route in response.routes),
        south=min(route.bounds.south for route in response.routes),
        east=max(route.bounds.east for route in response.routes),
        west=min(route.bounds.west for route in response.routes),
    )


@pytest.mark.asyncio
async def test_t23_congestion_score_uses_route_index_step() -> None:
    log: list[str] = []
    places = RecordingPlacesGateway(
        _place("Downtown Austin"),
        _place("Austin Airport", lat=30.1975, lng=-97.6664),
        log,
    )
    routing = RecordingRoutesGateway(
        [_route(route_id="route-1"), _route(route_id="route-2")],
        log,
    )
    service = PlanningService(
        places=places,
        routing=routing,
        weather=RecordingWeatherService(log),
        segments=SegmentBuilder(),
        pricing=PricingModel(),
        scorer=RouteScorer(),
        settings=Settings(google_maps_api_key="test-key"),
    )

    response = await service.plan(_request(congestion=56))

    assert [route.congestion_score for route in response.routes] == [56, 47]
    assert all(score >= ROUTE_CONGESTION_FLOOR for score in [56, 47])


@pytest.mark.asyncio
async def test_t47_scenario_only_replan_uses_place_cache() -> None:
    places_calls = 0
    base_handler, _ = make_api_mock_handler(route_count=3)

    def counting_handler(request: httpx.Request) -> httpx.Response:
        nonlocal places_calls
        if "places.googleapis.com" in str(request.url):
            places_calls += 1
        return base_handler(request)

    cache = PlaceResolutionCache()
    async with make_mock_async_client(counting_handler) as client:
        service = build_planning_service(
            client,
            Settings(google_maps_api_key="test-key"),
            cache,
        )
        await service.plan(_request(congestion=56))
        assert places_calls == 2
        await service.plan(_request(congestion=72))
        assert places_calls == 2


@pytest.mark.asyncio
async def test_t47_place_gateway_cache_prevents_repeat_transport() -> None:
    base_handler, _ = make_api_mock_handler(route_count=1)
    calls = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return base_handler(request)

    cache = PlaceResolutionCache()
    async with make_mock_async_client(handler) as client:
        gateway = GooglePlacesGateway(
            Settings(google_maps_api_key="test-key"),
            client,
            cache,
        )
        first = await gateway.resolve("Downtown Austin")
        second = await gateway.resolve("  downtown   austin ")

    assert first.name == second.name
    assert calls == 1
