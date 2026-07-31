import type { LatLngPoint, RouteOption, TrafficInterval, TrafficSpeed } from "../types";
import { trafficSegmentColor } from "../utils/trafficSegmentColor";

export interface DrawablePolyline {
  key: string;
  routeId: string;
  path: LatLngPoint[];
  color: string;
  opacity: number;
  weight: number;
  zIndex: number;
}

function clamp(value: number, min: number, max: number): number {
  return Math.max(min, Math.min(max, value));
}

export function intervalsForRoute(route: RouteOption): TrafficInterval[] {
  if (route.traffic_intervals.length > 0) {
    return route.traffic_intervals;
  }
  if (route.polyline.length < 2) {
    return [];
  }
  return [{ start_index: 0, end_index: route.polyline.length - 1, speed: "NORMAL" }];
}

export function sliceIntervalPath(
  polyline: LatLngPoint[],
  interval: TrafficInterval,
): LatLngPoint[] {
  if (polyline.length < 2) {
    return [];
  }
  const start = clamp(interval.start_index, 0, polyline.length - 2);
  const end = clamp(interval.end_index, start + 1, polyline.length - 1);
  return polyline.slice(start, end + 1);
}

export function buildDrawablePolylines(
  routes: RouteOption[],
  selectedRouteId: string | undefined,
  congestion: number,
  weatherSeverity: number,
): DrawablePolyline[] {
  const drawable: DrawablePolyline[] = [];

  for (const route of routes) {
    const selected = route.id === selectedRouteId;
    const hasSelection = Boolean(selectedRouteId);
    const opacity = selected ? 1 : hasSelection ? 0.68 : 0.85;
    const weight = selected ? 6 : 4;
    const intervals = intervalsForRoute(route);

    intervals.forEach((interval, index) => {
      const path = sliceIntervalPath(route.polyline, interval);
      if (path.length < 2) {
        return;
      }
      const start = clamp(interval.start_index, 0, route.polyline.length - 2);
      const end = clamp(interval.end_index, start + 1, route.polyline.length - 1);
      drawable.push({
        key: `${route.id}-${index}-${start}-${end}`,
        routeId: route.id,
        path,
        color: trafficSegmentColor(interval.speed as TrafficSpeed, congestion, weatherSeverity),
        opacity,
        weight,
        zIndex: weight,
      });
    });
  }

  return drawable;
}
