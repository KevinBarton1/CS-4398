from dataclasses import dataclass
from math import isfinite

from app.config import ROUTE_SCORE_WEIGHTS
from app.simulation.scoring import RouteScorer


@dataclass
class Candidate:
    id: str
    adjusted_eta_minutes: float
    distance_miles: float
    congestion_score: int
    normalized_score: float = 0.0


def test_t17_scores_three_routes_and_recommends_the_lowest() -> None:
    routes = [
        Candidate("route-1", 24.8, 12.4, 56),
        Candidate("route-2", 26.1, 12.8, 47),
        Candidate("route-3", 25.4, 11.9, 38),
    ]
    scorer = RouteScorer()

    scored = scorer.score(routes)

    assert [route.normalized_score for route in scored] == [
        0.9694,
        0.9518,
        0.8748,
    ]
    assert scorer.recommend(scored) == "route-3"


def test_t17_single_route_scores_zero_and_is_recommended() -> None:
    routes = [Candidate("route-1", 22.0, 12.4, 4)]
    scorer = RouteScorer()

    scored = scorer.score(routes)

    assert scored[0].normalized_score == 0.0
    assert isfinite(scored[0].normalized_score)
    assert scorer.recommend(scored) == "route-1"


def test_t17_tie_recommends_the_earlier_input() -> None:
    routes = [
        Candidate("route-2", 20.0, 10.0, 40),
        Candidate("route-1", 20.0, 10.0, 40),
    ]
    scorer = RouteScorer()

    scorer.score(routes)

    assert scorer.recommend(routes) == "route-2"


def test_t17_zero_maximum_contributes_zero() -> None:
    routes = [
        Candidate("route-1", 0.0, 0.0, 0),
        Candidate("route-2", 0.0, 0.0, 0),
    ]

    RouteScorer().score(routes)

    assert [route.normalized_score for route in routes] == [0.0, 0.0]


def test_t17_uses_exactly_the_three_documented_weights() -> None:
    assert ROUTE_SCORE_WEIGHTS == {
        "time": 0.47,
        "distance": 0.23,
        "congestion": 0.30,
    }
