def decode_polyline(encoded: str) -> list[dict[str, float]]:
    """Decode a Google encoded polyline into {lat, lng} pairs."""
    coordinates: list[dict[str, float]] = []
    index = 0
    lat = 0
    lng = 0
    length = len(encoded)

    while index < length:
        shift = 0
        result = 0
        while True:
            byte = ord(encoded[index]) - 63
            index += 1
            result |= (byte & 0x1F) << shift
            shift += 5
            if byte < 0x20:
                break
        lat += (~(result >> 1) if result & 1 else (result >> 1))

        shift = 0
        result = 0
        while True:
            byte = ord(encoded[index]) - 63
            index += 1
            result |= (byte & 0x1F) << shift
            shift += 5
            if byte < 0x20:
                break
        lng += (~(result >> 1) if result & 1 else (result >> 1))

        coordinates.append({"lat": lat / 1e5, "lng": lng / 1e5})

    return coordinates
