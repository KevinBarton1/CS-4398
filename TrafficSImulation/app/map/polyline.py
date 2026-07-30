from app.map.types import LatLngPoint


def decode_polyline(encoded: str) -> list[LatLngPoint]:
    """Decode a Google encoded polyline in origin-to-destination order."""
    points: list[LatLngPoint] = []
    index = 0
    latitude = 0
    longitude = 0

    while index < len(encoded):
        latitude_delta, index = _decode_value(encoded, index)
        longitude_delta, index = _decode_value(encoded, index)
        latitude += latitude_delta
        longitude += longitude_delta
        points.append(
            LatLngPoint(
                lat=latitude / 100_000,
                lng=longitude / 100_000,
            )
        )

    return points


def _decode_value(encoded: str, index: int) -> tuple[int, int]:
    result = 0
    shift = 0

    while True:
        byte = ord(encoded[index]) - 63
        index += 1
        result |= (byte & 0x1F) << shift
        if byte < 0x20:
            break
        shift += 5

    value = ~(result >> 1) if result & 1 else result >> 1
    return value, index
