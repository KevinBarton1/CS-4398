import math

from .models import RoadSegment


def time_of_day_factor(hour):
    hour = max(0, min(23, int(hour)))
    if 7 <= hour <= 9 or 16 <= hour <= 18:
        return 1.22
    if hour < 6 or hour >= 22:
        return 0.92
    return 1.0


def create_segments(route, congestion, weather_multiplier, route_index):
    segments = []
    lengths = (route["distance_miles"] * 0.47, route["distance_miles"] * 0.53)
    for index, (name, length) in enumerate(zip(route["road_names"], lengths)):
        local_congestion = max(5, min(98, congestion + (index * 11) - (route_index * 9)))
        speed_limit = (45, 55)[index]
        average_speed = max(8, speed_limit * (1 - local_congestion * 0.0065) / weather_multiplier)
        segments.append(RoadSegment(
            name=name,
            length_miles=round(length, 1),
            lanes=(3, 4)[index],
            speed_limit_mph=speed_limit,
            average_speed_mph=round(average_speed, 1),
            volume_vehicles_hour=round(550 + local_congestion * 21),
            congestion=round(local_congestion / 100, 2),
        ))
    return segments


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

