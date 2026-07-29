import httpx

from app.config import (
    AUSTIN_LOCATION_BIAS,
    GOOGLE_MAPS_API_KEY,
    GOOGLE_PLACES_SEARCH_URL,
    GOOGLE_REGION_CODE,
)
from app.map.local import ALIASES, geocode as local_geocode
from app.map.projection import project_lat_lng
from app.map.types import ResolvedPlace

LOCAL_ONLY_KEYS = {"current location"}


def _normalize_query(value: str) -> str:
    return " ".join(str(value or "").strip().lower().split())


def _places_headers() -> dict[str, str]:
    return {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": GOOGLE_MAPS_API_KEY,
        "X-Goog-FieldMask": "places.displayName,places.formattedAddress,places.location",
    }


def search_place(query: str) -> ResolvedPlace | None:
    if not GOOGLE_MAPS_API_KEY:
        return None

    text_query = _normalize_query(query)
    if not text_query:
        return None

    payload = {
        "textQuery": text_query,
        "regionCode": GOOGLE_REGION_CODE,
        "locationBias": AUSTIN_LOCATION_BIAS,
        "maxResultCount": 1,
    }

    try:
        response = httpx.post(
            GOOGLE_PLACES_SEARCH_URL,
            json=payload,
            headers=_places_headers(),
            timeout=8.0,
        )
        response.raise_for_status()
        places = response.json().get("places") or []
        if not places:
            return None

        place = places[0]
        location = place.get("location") or {}
        latitude = location.get("latitude")
        longitude = location.get("longitude")
        if latitude is None or longitude is None:
            return None

        display_name = (
            (place.get("displayName") or {}).get("text")
            or place.get("formattedAddress")
            or text_query
        )
        return ResolvedPlace(
            name=str(display_name),
            latitude=float(latitude),
            longitude=float(longitude),
            point=project_lat_lng(float(latitude), float(longitude)),
            source="google",
        )
    except (httpx.HTTPError, ValueError, TypeError):
        return None


def resolve_place(value: str) -> ResolvedPlace:
    text = _normalize_query(value)
    if not text:
        raise ValueError("Location is required.")

    resolved_key = ALIASES.get(text, text)
    if resolved_key in LOCAL_ONLY_KEYS:
        name, point = local_geocode(value)
        return ResolvedPlace(
            name=name,
            latitude=0.0,
            longitude=0.0,
            point=point,
            source="local",
        )

    google_place = search_place(text)
    if google_place:
        return google_place

    name, point = local_geocode(text)
    return ResolvedPlace(
        name=name,
        latitude=0.0,
        longitude=0.0,
        point=point,
        source="local",
    )
