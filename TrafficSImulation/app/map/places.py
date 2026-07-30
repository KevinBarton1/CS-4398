import httpx

from app.config import (
    AUSTIN_LOCATION_BIAS,
    GOOGLE_PLACES_FIELD_MASK,
    GOOGLE_PLACES_SEARCH_URL,
    GOOGLE_REGION_CODE,
    PLACES_TIMEOUT_SECONDS,
    Settings,
)
from app.map.errors import (
    InvalidLocationError,
    MapsNotConfiguredError,
    UpstreamTimeoutError,
    UpstreamUnavailableError,
)
from app.map.types import ResolvedPlace


class GooglePlacesGateway:
    def __init__(
        self,
        settings: Settings,
        client: httpx.AsyncClient,
    ) -> None:
        self._settings = settings
        self._client = client

    async def resolve(self, query: str) -> ResolvedPlace:
        if not self._settings.google_maps_configured:
            raise MapsNotConfiguredError

        normalized_query = " ".join(query.strip().lower().split())
        if not normalized_query:
            raise InvalidLocationError(query)

        try:
            response = await self._client.post(
                GOOGLE_PLACES_SEARCH_URL,
                json={
                    "textQuery": normalized_query,
                    "regionCode": GOOGLE_REGION_CODE,
                    "locationBias": AUSTIN_LOCATION_BIAS,
                    "maxResultCount": 1,
                },
                headers={
                    "Content-Type": "application/json",
                    "X-Goog-Api-Key": self._settings.google_maps_api_key,
                    "X-Goog-FieldMask": GOOGLE_PLACES_FIELD_MASK,
                },
                timeout=PLACES_TIMEOUT_SECONDS,
            )
            response.raise_for_status()
        except httpx.TimeoutException as error:
            raise UpstreamTimeoutError("Places") from error
        except httpx.HTTPError as error:
            raise UpstreamUnavailableError("Places") from error

        try:
            body = response.json()
            if not isinstance(body, dict):
                raise TypeError("Places response must be an object.")
            places = body.get("places") or []
        except (AttributeError, TypeError, ValueError) as error:
            raise UpstreamUnavailableError("Places") from error

        if not places:
            raise InvalidLocationError(query)
        if not isinstance(places, list) or not isinstance(places[0], dict):
            raise UpstreamUnavailableError("Places")

        place = places[0]
        try:
            location = place.get("location") or {}
            latitude = location.get("latitude")
            longitude = location.get("longitude")
        except AttributeError as error:
            raise UpstreamUnavailableError("Places") from error

        if latitude is None or longitude is None:
            raise InvalidLocationError(query)

        try:
            display_name = place.get("displayName") or {}
            name = (
                display_name.get("text")
                if isinstance(display_name, dict)
                else None
            )
            name = name or place.get("formattedAddress") or normalized_query
            return ResolvedPlace(
                name=str(name),
                latitude=float(latitude),
                longitude=float(longitude),
                source="google",
            )
        except (TypeError, ValueError) as error:
            raise UpstreamUnavailableError("Places") from error
