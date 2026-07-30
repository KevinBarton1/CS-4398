"""Deployment settings and domain constants for TrafficScope."""

from pathlib import Path

from dotenv import load_dotenv
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_APP_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(_APP_ROOT / ".env")


class Settings(BaseSettings):
    """Values supplied by the deployment environment."""

    model_config = SettingsConfigDict(
        env_prefix="",
        case_sensitive=False,
        extra="ignore",
    )

    google_maps_api_key: str = ""
    google_maps_browser_api_key: str = ""
    google_maps_map_id: str | None = None

    @field_validator("google_maps_map_id", mode="before")
    @classmethod
    def empty_map_id_is_absent(cls, value: object) -> object:
        if isinstance(value, str) and not value.strip():
            return None
        return value

    @property
    def google_maps_configured(self) -> bool:
        return bool(self.google_maps_api_key.strip())


settings = Settings()

# Compatibility for the pre-rewrite gateways. New code receives ``settings``
# through Controller dependencies instead of importing a credential value.
GOOGLE_MAPS_API_KEY = settings.google_maps_api_key

# Pricing
BASE_FARE = 2.20
PER_MILE_RATE = 1.28
PER_MINUTE_RATE = 0.31
MINIMUM_FARE = 7.50
PRICE_CONGESTION_DIVISOR = 500

# Traffic and segments
BPR_ALPHA = 0.15
BPR_BETA = 4
BASE_LANE_CAPACITY = 520
MINIMUM_CRAWL_SPEED_MPH = 6.0
SEGMENT_COUNT_MAX = 2
SEGMENT_SPEED_LIMITS_MPH = (45, 55)
SEGMENT_LANE_COUNTS = (3, 4)
SEGMENT_CONGESTION_INDEX_STEP = 11
SEGMENT_CONGESTION_MIN = 5
SEGMENT_CONGESTION_MAX = 98
PEAK_TIME_FACTOR = 1.22
OFFPEAK_TIME_FACTOR = 0.92
PEAK_HOURS_MORNING = (7, 9)
PEAK_HOURS_EVENING = (16, 18)
OFFPEAK_HOUR_START = 22
OFFPEAK_HOUR_END = 6

# Weather
WEATHER_TIME_MULTIPLIERS = (1.0, 1.08, 1.18, 1.32)
WEATHER_PRICE_MULTIPLIERS = (1.0, 1.03, 1.07, 1.12)
WEATHER_LABELS = ("Clear", "Light rain", "Heavy rain", "Severe")
WEATHER_SOURCE_SIMULATED = "Simulated fallback"

# Route identity and scoring
ROUTE_SCORE_WEIGHTS = {
    "time": 0.47,
    "distance": 0.23,
    "congestion": 0.30,
}
ROUTE_COLORS = ["#55d6be", "#ffb35c", "#4d72e8"]
ROUTE_NAMES = ("Fastest", "Balanced", "Low traffic")
ROUTE_OBJECTIVES = (
    "Minimum adjusted travel time",
    "Weighted time, distance, and congestion",
    "Minimum congestion exposure",
)
ROUTE_ALTERNATIVES_MAX = 3
ROUTE_CONGESTION_INDEX_STEP = 9
ROUTE_CONGESTION_FLOOR = 4
ETA_FALLBACK_BUFFER_MINUTES = 2.0
PLACE_MATCH_TOLERANCE_DEGREES = 0.0005

# Scenario defaults
DEFAULT_HOUR = 17
DEFAULT_WEATHER = 1
DEFAULT_CONGESTION = 56

# Google integration
GOOGLE_PLACES_SEARCH_URL = "https://places.googleapis.com/v1/places:searchText"
GOOGLE_ROUTES_COMPUTE_URL = "https://routes.googleapis.com/directions/v2:computeRoutes"
GOOGLE_REGION_CODE = "US"
AUSTIN_LOCATION_BIAS = {
    "circle": {
        "center": {"latitude": 30.2672, "longitude": -97.7431},
        "radius": 35000.0,
    }
}
GOOGLE_PLACES_FIELD_MASK = (
    "places.displayName,places.formattedAddress,places.location"
)
GOOGLE_ROUTES_FIELD_MASK = (
    "routes.duration,routes.staticDuration,routes.distanceMeters,"
    "routes.polyline.encodedPolyline,"
    "routes.travelAdvisory.speedReadingIntervals,"
    "routes.legs.travelAdvisory.speedReadingIntervals,"
    "routes.legs.steps.distanceMeters,routes.legs.steps.staticDuration,"
    "routes.legs.steps.polyline.encodedPolyline,"
    "routes.legs.steps.navigationInstruction,routes.description,routes.routeLabels"
)
PLACES_TIMEOUT_SECONDS = 8.0
ROUTES_TIMEOUT_SECONDS = 10.0
HEALTH_PROBE_CACHE_SECONDS = 30.0

# Fixed response strings
DATA_SOURCE_SIMULATED = "Google Routes with departure-hour traffic"
DATA_SOURCE_REALTIME = "Google Routes with live traffic"
NOTICE_SIMULATED = (
    "Simulated mode: Google Maps supplies route geometry and departure-hour "
    "traffic; scenario controls adjust planning estimates."
)
NOTICE_REALTIME = (
    "Real-Time mode: route, distance, and travel time come from Google Maps "
    "traffic-aware routing for the current departure time."
)
SERVICE_NAME = "TrafficScope"
SERVICE_VERSION = "2.0"

# Browser map configuration
MAP_DEFAULT_CENTER = {"lat": 30.2672, "lng": -97.7431}
MAP_DEFAULT_ZOOM = 12
MAP_COLOR_SCHEME = "DARK"
MAP_LIBRARIES = ["core", "maps"]
