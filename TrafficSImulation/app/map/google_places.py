import httpx

from app.config import (
    AUSTIN_LOCATION_BIAS,
    GOOGLE_MAPS_API_KEY,
    GOOGLE_PLACES_FIELD_MASK,
    GOOGLE_PLACES_SEARCH_URL,
    GOOGLE_REGION_CODE,
    PLACES_TIMEOUT_SECONDS,
)
from app.map.types import ResolvedPlace


def _normalize_query(value: str) -> str:
    return " ".join(str(value or "").strip().lower().split())


def _require_api_key() -> None:
    if not GOOGLE_MAPS_API_KEY:
        raise ValueError("GOOGLE_MAPS_API_KEY is not configured.")


def _places_headers() -> dict[str, str]:
    return {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": GOOGLE_MAPS_API_KEY,
        "X-Goog-FieldMask": GOOGLE_PLACES_FIELD_MASK,
    }


def search_place(query: str) -> ResolvedPlace:
    _require_api_key()

    text_query = _normalize_query(query)
    if not text_query:
        raise ValueError("Location is required.")

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
            timeout=PLACES_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
    except httpx.HTTPStatusError as error:
        detail = error.response.text.strip().replace("\n", " ")[:240]
        raise ValueError(f"Places API HTTP {error.response.status_code}: {detail}") from error
    except httpx.HTTPError as error:
        raise ValueError(f"Places API request failed: {error}") from error

    places = response.json().get("places") or []
    if not places:
        raise ValueError(f'Could not geocode "{query}" using Google Places.')

    place = places[0]
    location = place.get("location") or {}
    latitude = location.get("latitude")
    longitude = location.get("longitude")
    if latitude is None or longitude is None:
        raise ValueError(f'Google Places returned no coordinates for "{query}".')

    display_name = (
        (place.get("displayName") or {}).get("text")
        or place.get("formattedAddress")
        or text_query
    )
    return ResolvedPlace(
        name=str(display_name),
        latitude=float(latitude),
        longitude=float(longitude),
        source="google",
    )


def resolve_place(value: str) -> ResolvedPlace:
    text = _normalize_query(value)
    if not text:
        raise ValueError("Location is required.")
    if text == "current location":
        raise ValueError(
            "Current location is not supported without coordinates. Enter an address instead."
        )
    return search_place(text)
