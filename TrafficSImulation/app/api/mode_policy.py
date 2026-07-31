from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from app.api.models import PlanRequest, RoadSegment, Scenario, WeatherState
from app.config import (
    DATA_SOURCE_REALTIME,
    DATA_SOURCE_SIMULATED,
    ETA_FALLBACK_BUFFER_MINUTES,
    NOTICE_REALTIME,
    NOTICE_SIMULATED,
    ROUTE_ALTERNATIVES_MAX,
)
from app.map.types import RawRoute
from app.simulation.traffic import time_of_day_factor

AUSTIN_TIMEZONE = ZoneInfo("America/Chicago")
ROUTING_PREFERENCE = "TRAFFIC_AWARE"


class ModePolicy(ABC):
    @property
    @abstractmethod
    def mode(self) -> str:
        ...

    @property
    @abstractmethod
    def scenario_applied(self) -> bool:
        ...

    @property
    @abstractmethod
    def alternatives(self) -> int:
        ...

    @abstractmethod
    def effective_scenario(self, request: PlanRequest) -> Scenario:
        ...

    @abstractmethod
    def departure_time(self, scenario: Scenario) -> datetime:
        ...

    @abstractmethod
    def routing_preference(self) -> str:
        ...

    @abstractmethod
    def adjusted_eta(
        self,
        route: RawRoute,
        weather: WeatherState,
        segments: list[RoadSegment],
    ) -> float:
        ...

    @abstractmethod
    def pricing_time_multiplier(self, scenario: Scenario) -> float:
        ...

    @abstractmethod
    def data_source(self) -> str:
        ...

    @abstractmethod
    def notice(self) -> str:
        ...


class SimulatedModePolicy(ModePolicy):
    @property
    def mode(self) -> str:
        return "simulated"

    @property
    def scenario_applied(self) -> bool:
        return True

    @property
    def alternatives(self) -> int:
        return ROUTE_ALTERNATIVES_MAX

    def effective_scenario(self, request: PlanRequest) -> Scenario:
        return Scenario(
            hour=request.hour,
            weather=request.weather,
            congestion=request.congestion,
        )

    def departure_time(self, scenario: Scenario) -> datetime:
        now = datetime.now(AUSTIN_TIMEZONE)
        departure = now.replace(
            hour=scenario.hour,
            minute=0,
            second=0,
            microsecond=0,
        )
        if departure <= now:
            departure += timedelta(days=1)
        return departure

    def routing_preference(self) -> str:
        return ROUTING_PREFERENCE

    def adjusted_eta(
        self,
        route: RawRoute,
        weather: WeatherState,
        segments: list[RoadSegment],
    ) -> float:
        base_minutes = _base_duration_minutes(route, segments)
        return base_minutes * weather.time_multiplier

    def pricing_time_multiplier(self, scenario: Scenario) -> float:
        return 1.0

    def data_source(self) -> str:
        return DATA_SOURCE_SIMULATED

    def notice(self) -> str:
        return NOTICE_SIMULATED


class RealTimeModePolicy(ModePolicy):
    @property
    def mode(self) -> str:
        return "realtime"

    @property
    def scenario_applied(self) -> bool:
        return False

    @property
    def alternatives(self) -> int:
        return 1

    def effective_scenario(self, request: PlanRequest) -> Scenario:
        del request
        now = datetime.now(AUSTIN_TIMEZONE)
        return Scenario(hour=now.hour, weather=0, congestion=0)

    def departure_time(self, scenario: Scenario) -> datetime:
        del scenario
        return datetime.now(AUSTIN_TIMEZONE)

    def routing_preference(self) -> str:
        return ROUTING_PREFERENCE

    def adjusted_eta(
        self,
        route: RawRoute,
        weather: WeatherState,
        segments: list[RoadSegment],
    ) -> float:
        del weather
        return _base_duration_minutes(route, segments)

    def pricing_time_multiplier(self, scenario: Scenario) -> float:
        return time_of_day_factor(scenario.hour)

    def data_source(self) -> str:
        return DATA_SOURCE_REALTIME

    def notice(self) -> str:
        return NOTICE_REALTIME


_MODE_POLICIES: dict[str, type[ModePolicy]] = {
    "simulated": SimulatedModePolicy,
    "realtime": RealTimeModePolicy,
}


def resolve_mode_policy(mode: str) -> ModePolicy:
    try:
        policy_cls = _MODE_POLICIES[mode]
    except KeyError as error:
        raise ValueError(f"Unsupported planning mode: {mode}") from error
    return policy_cls()


def _base_duration_minutes(
    route: RawRoute,
    segments: list[RoadSegment],
) -> float:
    if route.duration_seconds is not None:
        return route.duration_seconds / 60
    if route.static_duration_seconds is not None:
        return route.static_duration_seconds / 60
    return (
        sum(segment.adjusted_minutes for segment in segments)
        + ETA_FALLBACK_BUFFER_MINUTES
    )
