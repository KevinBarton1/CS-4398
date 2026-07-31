from app.api.models import HeatmapCell, HeatmapRequest, HeatmapResponse, Scenario
from app.heatmap.builder import HeatmapBuilder


class HeatmapService:
    def __init__(self, builder: HeatmapBuilder | None = None) -> None:
        self._builder = builder or HeatmapBuilder()

    def build(self, request: HeatmapRequest) -> HeatmapResponse:
        grid = self._builder.build(request.hour, request.congestion)
        return HeatmapResponse(
            metric=grid.metric,  # type: ignore[arg-type]
            rows=grid.rows,
            columns=grid.columns,
            scenario=Scenario(
                hour=grid.hour,
                weather=0,
                congestion=grid.congestion,
            ),
            bounds=grid.bounds,
            cells=[
                HeatmapCell(
                    row=cell.row,
                    column=cell.column,
                    value=cell.value,
                    bounds=cell.bounds,
                )
                for cell in grid.cells
            ],
            notice=grid.notice,
        )


__all__ = ["HeatmapService"]
