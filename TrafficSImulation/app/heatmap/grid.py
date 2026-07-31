"""Grid geometry for the Austin congestion heatmap."""

from __future__ import annotations

from dataclasses import dataclass

from app.config import HEATMAP_COLUMNS, HEATMAP_COVERAGE_BOUNDS, HEATMAP_ROWS


@dataclass(frozen=True, slots=True)
class GridCellGeometry:
    row: int
    column: int
    north: float
    south: float
    east: float
    west: float


def build_grid(
    rows: int = HEATMAP_ROWS,
    columns: int = HEATMAP_COLUMNS,
    coverage: dict[str, float] | None = None,
) -> list[GridCellGeometry]:
    bounds = coverage or HEATMAP_COVERAGE_BOUNDS
    north_edge = bounds["north"]
    south_edge = bounds["south"]
    east_edge = bounds["east"]
    west_edge = bounds["west"]

    lat_step = (north_edge - south_edge) / rows
    lng_step = (east_edge - west_edge) / columns

    cells: list[GridCellGeometry] = []
    for row in range(rows):
        row_north = north_edge - row * lat_step
        row_south = row_north - lat_step
        for column in range(columns):
            cell_west = west_edge + column * lng_step
            cell_east = cell_west + lng_step
            cells.append(
                GridCellGeometry(
                    row=row,
                    column=column,
                    north=row_north,
                    south=row_south,
                    east=cell_east,
                    west=cell_west,
                )
            )
    return cells


__all__ = ["GridCellGeometry", "build_grid"]
