"""Congestion intensity assignment for heatmap cells."""

from __future__ import annotations

import math
from dataclasses import dataclass

from app.config import (
    HEATMAP_CENTER_BLEND,
    HEATMAP_CENTER_LAT,
    HEATMAP_CENTER_LNG,
    HEATMAP_COLUMNS,
    HEATMAP_CONGESTION_BLEND,
    HEATMAP_COVERAGE_BOUNDS,
    HEATMAP_HOUR_BLEND,
    HEATMAP_MAX_CENTER_DISTANCE_DEGREES,
    HEATMAP_METRIC,
    HEATMAP_MID_HOUR_FACTOR,
    HEATMAP_NOTICE,
    HEATMAP_OFFPEAK_HOUR_FACTOR,
    HEATMAP_PEAK_HOUR_FACTOR,
    HEATMAP_ROWS,
    OFFPEAK_HOUR_END,
    OFFPEAK_HOUR_START,
    PEAK_HOURS_EVENING,
    PEAK_HOURS_MORNING,
)
from app.heatmap.grid import GridCellGeometry, build_grid
from app.map.types import RouteBounds


@dataclass(frozen=True, slots=True)
class HeatmapCell:
    row: int
    column: int
    value: int
    bounds: RouteBounds


@dataclass(frozen=True, slots=True)
class HeatmapGrid:
    metric: str
    rows: int
    columns: int
    hour: int
    congestion: int
    bounds: RouteBounds
    cells: tuple[HeatmapCell, ...]
    notice: str


def _is_peak_hour(hour: int) -> bool:
    morning_start, morning_end = PEAK_HOURS_MORNING
    evening_start, evening_end = PEAK_HOURS_EVENING
    return morning_start <= hour <= morning_end or evening_start <= hour <= evening_end


def _is_offpeak_hour(hour: int) -> bool:
    if OFFPEAK_HOUR_START <= hour or hour <= OFFPEAK_HOUR_END:
        return True
    return False


def _hour_intensity(hour: int) -> float:
    if _is_peak_hour(hour):
        return HEATMAP_PEAK_HOUR_FACTOR
    if _is_offpeak_hour(hour):
        return HEATMAP_OFFPEAK_HOUR_FACTOR
    return HEATMAP_MID_HOUR_FACTOR


def _center_proximity(lat: float, lng: float) -> float:
    distance = math.hypot(lat - HEATMAP_CENTER_LAT, lng - HEATMAP_CENTER_LNG)
    normalized = min(1.0, distance / HEATMAP_MAX_CENTER_DISTANCE_DEGREES)
    return 1.0 - normalized


def _cell_center(geometry: GridCellGeometry) -> tuple[float, float]:
    lat = (geometry.north + geometry.south) / 2
    lng = (geometry.east + geometry.west) / 2
    return lat, lng


def _cell_value(hour: int, congestion: int, geometry: GridCellGeometry) -> int:
    lat, lng = _cell_center(geometry)
    blend = (
        HEATMAP_CONGESTION_BLEND * (congestion / 100)
        + HEATMAP_CENTER_BLEND * _center_proximity(lat, lng)
        + HEATMAP_HOUR_BLEND * _hour_intensity(hour)
    )
    return max(0, min(100, round(blend * 100)))


class HeatmapBuilder:
    def build(self, hour: int, congestion: int, metric: str = HEATMAP_METRIC) -> HeatmapGrid:
        if metric != HEATMAP_METRIC:
            raise ValueError(f"Unsupported heatmap metric: {metric}")

        coverage = HEATMAP_COVERAGE_BOUNDS
        geometries = build_grid(HEATMAP_ROWS, HEATMAP_COLUMNS, coverage)
        cells = tuple(
            HeatmapCell(
                row=geometry.row,
                column=geometry.column,
                value=_cell_value(hour, congestion, geometry),
                bounds=RouteBounds(
                    north=geometry.north,
                    south=geometry.south,
                    east=geometry.east,
                    west=geometry.west,
                ),
            )
            for geometry in geometries
        )
        return HeatmapGrid(
            metric=HEATMAP_METRIC,
            rows=HEATMAP_ROWS,
            columns=HEATMAP_COLUMNS,
            hour=hour,
            congestion=congestion,
            bounds=RouteBounds(**coverage),
            cells=cells,
            notice=HEATMAP_NOTICE,
        )


__all__ = ["HeatmapBuilder", "HeatmapCell", "HeatmapGrid"]
