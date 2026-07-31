from typing import Protocol, TypeVar

from app.config import ROUTE_SCORE_WEIGHTS


class ScoredRoute(Protocol):
    id: str
    adjusted_eta_minutes: float
    distance_miles: float
    congestion_score: int
    normalized_score: float


RouteT = TypeVar("RouteT", bound=ScoredRoute)


class RouteScorer:
    def score(self, routes: list[RouteT]) -> list[RouteT]:
        if len(routes) == 1:
            routes[0].normalized_score = 0.0
            return routes
        if not routes:
            return routes

        max_time = max(route.adjusted_eta_minutes for route in routes)
        max_distance = max(route.distance_miles for route in routes)
        max_congestion = max(route.congestion_score for route in routes)

        for route in routes:
            route.normalized_score = round(
                ROUTE_SCORE_WEIGHTS["time"]
                * self._normalize(route.adjusted_eta_minutes, max_time)
                + ROUTE_SCORE_WEIGHTS["distance"]
                * self._normalize(route.distance_miles, max_distance)
                + ROUTE_SCORE_WEIGHTS["congestion"]
                * self._normalize(route.congestion_score, max_congestion),
                4,
            )
        return routes

    def recommend(self, routes: list[ScoredRoute]) -> str:
        if not routes:
            raise ValueError("At least one scored route is required.")
        return min(routes, key=lambda route: route.normalized_score).id

    @staticmethod
    def _normalize(value: float, maximum: float) -> float:
        return value / maximum if maximum else 0.0
