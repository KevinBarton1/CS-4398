"""T-40: Heatmap grid geometry and congestion value function."""

from __future__ import annotations

import pytest

from app.config import HEATMAP_COLUMNS, HEATMAP_COVERAGE_BOUNDS, HEATMAP_ROWS
from app.heatmap.builder import HeatmapBuilder
from app.heatmap.grid import build_grid


def test_t40_grid_returns_rows_times_columns_cells() -> None:
    cells = build_grid()
    assert len(cells) == HEATMAP_ROWS * HEATMAP_COLUMNS


def test_t40_cells_tile_coverage_box_without_gaps_or_overlaps() -> None:
    cells = build_grid()
    coverage = HEATMAP_COVERAGE_BOUNDS

    assert cells[0].north == coverage["north"]
    assert cells[0].west == coverage["west"]
    assert cells[-1].south == coverage["south"]
    assert cells[HEATMAP_COLUMNS - 1].east == coverage["east"]

    for index, cell in enumerate(cells):
        assert cell.north > cell.south
        assert cell.east > cell.west
        if index % HEATMAP_COLUMNS != HEATMAP_COLUMNS - 1:
            assert cell.east == pytest.approx(cells[index + 1].west)
        if index + HEATMAP_COLUMNS < len(cells):
            assert cell.south == pytest.approx(cells[index + HEATMAP_COLUMNS].north)


def test_t40_values_stay_within_zero_and_one_hundred() -> None:
    builder = HeatmapBuilder()
    grid = builder.build(hour=17, congestion=56)
    assert all(0 <= cell.value <= 100 for cell in grid.cells)


def test_t40_higher_congestion_never_lowers_cell_values() -> None:
    builder = HeatmapBuilder()
    low = builder.build(hour=17, congestion=10)
    high = builder.build(hour=17, congestion=90)
    for low_cell, high_cell in zip(low.cells, high.cells, strict=True):
        assert high_cell.value >= low_cell.value


def test_t40_identical_scenarios_produce_identical_values() -> None:
    builder = HeatmapBuilder()
    first = builder.build(hour=8, congestion=42)
    second = builder.build(hour=8, congestion=42)
    assert [cell.value for cell in first.cells] == [cell.value for cell in second.cells]
