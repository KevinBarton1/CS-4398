"""Single source of truth for TrafficScope simulation coefficients."""

import os
from pathlib import Path

from dotenv import load_dotenv

_APP_ROOT = Path(__file__).resolve().parent.parent.parent
load_dotenv(_APP_ROOT / ".env")

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

ROUTE_COLORS = ["#55d6be", "#ffb35c", "#8aa8ff"]

GOOGLE_MAPS_API_KEY = os.environ.get("GOOGLE_MAPS_API_KEY", "").strip()
GOOGLE_PLACES_SEARCH_URL = "https://places.googleapis.com/v1/places:searchText"
GOOGLE_ROUTES_COMPUTE_URL = "https://routes.googleapis.com/directions/v2:computeRoutes"
GOOGLE_REGION_CODE = "US"

SVG_WIDTH = 1000
SVG_HEIGHT = 650
AUSTIN_BOUNDS = {
    "lat_min": 30.05,
    "lat_max": 30.55,
    "lng_min": -97.95,
    "lng_max": -97.55,
}
AUSTIN_LOCATION_BIAS = {
    "circle": {
        "center": {"latitude": 30.2672, "longitude": -97.7431},
        "radius": 35000.0,
    }
}

GOOGLE_ROUTES_FIELD_MASK = (
    "routes.duration,routes.staticDuration,routes.distanceMeters,"
    "routes.polyline.encodedPolyline,routes.legs.steps.distanceMeters,"
    "routes.legs.steps.staticDuration,routes.legs.steps.duration,"
    "routes.legs.steps.navigationInstruction,routes.description,routes.routeLabels"
)
