import math


def heatmap_grid(congestion, demand, hour, mode):
    cells = []
    for row in range(5):
        for column in range(8):
            wave = (math.sin(column * 1.31 + row * 0.77 + hour * 0.13) + 1) * 16
            center = max(0, 28 - math.hypot(column - 4, row - 2) * 8)
            if mode == "demand":
                value = demand * 0.62 + wave + center
            elif mode == "profitability":
                value = demand * 0.72 + wave + center - congestion * 0.25
            else:
                value = congestion * 0.66 + wave + center * 0.35
            cells.append({"row": row, "column": column, "value": round(max(3, min(100, value)))})
    return cells
