from app.map.polyline import decode_polyline
from app.map.types import LatLngPoint


def test_t18_decodes_known_google_polyline_in_order() -> None:
    encoded = "_p~iF~ps|U_ulLnnqC_mqNvxq`@"

    assert decode_polyline(encoded) == [
        LatLngPoint(lat=38.5, lng=-120.2),
        LatLngPoint(lat=40.7, lng=-120.95),
        LatLngPoint(lat=43.252, lng=-126.453),
    ]


def test_t18_empty_polyline_returns_empty_list() -> None:
    assert decode_polyline("") == []
