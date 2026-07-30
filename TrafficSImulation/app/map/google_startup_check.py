import httpx

from app.config import (
    AUSTIN_LOCATION_BIAS,
    GOOGLE_MAPS_API_KEY,
    GOOGLE_PLACES_SEARCH_URL,
    GOOGLE_REGION_CODE,
    GOOGLE_ROUTES_COMPUTE_URL,
    PLACES_TIMEOUT_SECONDS,
    ROUTES_TIMEOUT_SECONDS,
)
from app.map.google_places import search_place
from app.map.types import ResolvedPlace

_STARTUP_STATUS: dict | None = None


def _places_probe() -> tuple[bool, str]:
    try:
        response = httpx.post(
            GOOGLE_PLACES_SEARCH_URL,
            json={
                "textQuery": "Downtown Austin, TX",
                "regionCode": GOOGLE_REGION_CODE,
                "locationBias": AUSTIN_LOCATION_BIAS,
                "maxResultCount": 1,
            },
            headers={
                "Content-Type": "application/json",
                "X-Goog-Api-Key": GOOGLE_MAPS_API_KEY,
                "X-Goog-FieldMask": "places.displayName,places.location",
            },
            timeout=PLACES_TIMEOUT_SECONDS,
        )
        if response.status_code != 200:
            detail = response.text.strip().replace("\n", " ")[:240]
            return False, f"Places API HTTP {response.status_code}: {detail}"
        places = response.json().get("places") or []
        if not places:
            return False, "Places API returned no results for Downtown Austin, TX."
        return True, "Places Text Search OK."
    except httpx.HTTPError as error:
        return False, f"Places API request failed: {error}"


def _routes_probe(origin: ResolvedPlace, destination: ResolvedPlace) -> tuple[bool, str]:
    try:
        response = httpx.post(
            GOOGLE_ROUTES_COMPUTE_URL,
            json={
                "origin": {
                    "location": {
                        "latLng": {
                            "latitude": origin.latitude,
                            "longitude": origin.longitude,
                        }
                    }
                },
                "destination": {
                    "location": {
                        "latLng": {
                            "latitude": destination.latitude,
                            "longitude": destination.longitude,
                        }
                    }
                },
                "travelMode": "DRIVE",
                "routingPreference": "TRAFFIC_UNAWARE",
                "units": "IMPERIAL",
                "regionCode": GOOGLE_REGION_CODE,
            },
            headers={
                "Content-Type": "application/json",
                "X-Goog-Api-Key": GOOGLE_MAPS_API_KEY,
                "X-Goog-FieldMask": "routes.distanceMeters,routes.duration",
            },
            timeout=ROUTES_TIMEOUT_SECONDS,
        )
        if response.status_code != 200:
            detail = response.text.strip().replace("\n", " ")[:240]
            return False, f"Routes API HTTP {response.status_code}: {detail}"
        routes = response.json().get("routes") or []
        if not routes:
            return False, "Routes API returned no routes for the Austin probe trip."
        return True, "Routes computeRoutes OK."
    except httpx.HTTPError as error:
        return False, f"Routes API request failed: {error}"


def verify_google_maps() -> dict:
    """Probe Places and Routes when a key is configured."""
    if not GOOGLE_MAPS_API_KEY:
        return {
            "configured": False,
            "ok": False,
            "places_ok": False,
            "routes_ok": False,
            "message": "GOOGLE_MAPS_API_KEY is not configured.",
        }

    places_ok, places_message = _places_probe()
    routes_ok = False
    routes_message = "Routes API skipped because Places probe failed."

    if places_ok:
        origin = search_place("Downtown Austin, TX")
        destination = search_place("Austin-Bergstrom International Airport, TX")
        if origin and destination:
            routes_ok, routes_message = _routes_probe(origin, destination)
        else:
            routes_message = "Could not resolve Austin probe locations through Places API."

    ok = places_ok and routes_ok
    if ok:
        message = "Google Maps Places and Routes APIs are reachable."
    elif not places_ok:
        message = places_message
    else:
        message = routes_message

    return {
        "configured": True,
        "ok": ok,
        "places_ok": places_ok,
        "routes_ok": routes_ok,
        "places_message": places_message,
        "routes_message": routes_message,
        "message": message,
    }


def run_startup_check() -> dict:
    global _STARTUP_STATUS
    _STARTUP_STATUS = verify_google_maps()
    return _STARTUP_STATUS


def get_startup_status() -> dict:
    if _STARTUP_STATUS is None:
        return {
            "configured": bool(GOOGLE_MAPS_API_KEY),
            "ok": False,
            "places_ok": False,
            "routes_ok": False,
            "message": "Startup Google Maps check has not run yet.",
        }
    return _STARTUP_STATUS
