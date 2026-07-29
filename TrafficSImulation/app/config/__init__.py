"""Single source of truth for TrafficScope simulation coefficients."""

BASE_FARE = 2.20
PER_MILE_RATE = 1.28
PER_MINUTE_RATE = 0.31
MINIMUM_FARE = 7.50

BPR_ALPHA = 0.15
BPR_BETA = 4
BASE_LANE_CAPACITY = 520
MINIMUM_CRAWL_SPEED_MPH = 6.0

WEATHER_TIME_MULTIPLIERS = (1.0, 1.08, 1.18, 1.32)
WEATHER_PRICE_MULTIPLIERS = (1.0, 1.03, 1.07, 1.12)
WEATHER_LABELS = ("Clear", "Light rain", "Heavy rain", "Severe")

ROUTE_SCORE_WEIGHTS = {
    "time": 0.42,
    "distance": 0.18,
    "congestion": 0.25,
    "demand": 0.15,
}
