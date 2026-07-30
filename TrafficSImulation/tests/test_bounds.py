import pytest

from app.map.bounds import bounds_for_points, union_bounds
from app.map.types import LatLngPoint, RouteBounds


def test_t19_bounds_for_points_encloses_known_points() -> None:
    points = [
        LatLngPoint(lat=30.2672, lng=-97.7431),
        LatLngPoint(lat=30.1975, lng=-97.6664),
        LatLngPoint(lat=30.3010, lng=-97.8100),
    ]

    result = bounds_for_points(points)

    assert result == RouteBounds(
        north=30.3010,
        south=30.1975,
        east=-97.6664,
        west=-97.8100,
    )


def test_t19_single_point_produces_zero_area_bounds() -> None:
    point = LatLngPoint(lat=30.2672, lng=-97.7431)

    assert bounds_for_points([point]) == RouteBounds(
        north=30.2672,
        south=30.2672,
        east=-97.7431,
        west=-97.7431,
    )


def test_t19_empty_points_raise_value_error() -> None:
    with pytest.raises(ValueError):
        bounds_for_points([])


def test_t19_union_bounds_contains_every_input_box() -> None:
    boxes = [
        RouteBounds(
            north=30.30,
            south=30.20,
            east=-97.70,
            west=-97.80,
        ),
        RouteBounds(
            north=30.45,
            south=30.35,
            east=-97.55,
            west=-97.65,
        ),
    ]

    result = union_bounds(boxes)

    assert result == RouteBounds(
        north=30.45,
        south=30.20,
        east=-97.55,
        west=-97.80,
    )
    for box in boxes:
        assert result.north >= box.north
        assert result.south <= box.south
        assert result.east >= box.east
        assert result.west <= box.west


def test_t19_empty_bounds_raise_value_error() -> None:
    with pytest.raises(ValueError):
        union_bounds([])
