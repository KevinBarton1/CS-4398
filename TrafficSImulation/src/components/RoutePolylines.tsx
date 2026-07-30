import { useEffect, useMemo, useRef } from "react";
import { useMap, useMapsLibrary } from "@vis.gl/react-google-maps";
import type { RouteOption, TrafficInterval } from "../types";
import { trafficSegmentColor } from "../utils/trafficSegmentColor";

interface RoutePolylinesProps {
  routes: RouteOption[];
  selectedId?: string;
  congestion: number;
  weatherSeverity: number;
}

interface DrawableSegment {
  key: string;
  path: RouteOption["polyline"];
  color: string;
  opacity: number;
  weight: number;
}

function slicePolyline(
  polyline: RouteOption["polyline"],
  startIndex: number,
  endIndex: number
) {
  if (polyline.length < 2) return polyline;
  const start = Math.max(0, Math.min(startIndex, polyline.length - 1));
  const end = Math.max(start + 1, Math.min(endIndex, polyline.length));
  return polyline.slice(start, end);
}

function intervalsForRoute(route: RouteOption): TrafficInterval[] {
  if (route.traffic_intervals?.length) return route.traffic_intervals;
  if (route.polyline.length < 2) return [];
  return [{ start_index: 0, end_index: route.polyline.length, speed: "NORMAL" }];
}

function buildDrawableSegments(
  routes: RouteOption[],
  selectedId: string | undefined,
  congestion: number,
  weatherSeverity: number
): DrawableSegment[] {
  const segments: DrawableSegment[] = [];
  for (const route of routes) {
    const active = route.id === selectedId;
    const opacity = active ? 1 : selectedId ? 0.68 : 0.85;
    const weight = active ? 6 : 4;
    const intervals = intervalsForRoute(route);
    for (let index = 0; index < intervals.length; index += 1) {
      const interval = intervals[index];
      const path = slicePolyline(route.polyline, interval.start_index, interval.end_index);
      if (path.length < 2) continue;
      segments.push({
        key: `${route.id}-${interval.start_index}-${interval.end_index}-${index}`,
        path,
        color: trafficSegmentColor(interval.speed, congestion, weatherSeverity),
        opacity,
        weight,
      });
    }
  }
  return segments;
}

export function RoutePolylines({
  routes,
  selectedId,
  congestion,
  weatherSeverity,
}: RoutePolylinesProps) {
  const map = useMap();
  const mapsLibrary = useMapsLibrary("maps");
  const polylinesRef = useRef<google.maps.Polyline[]>([]);

  const drawable = useMemo(
    () => buildDrawableSegments(routes, selectedId, congestion, weatherSeverity),
    [routes, selectedId, congestion, weatherSeverity]
  );

  useEffect(() => {
    polylinesRef.current.forEach((line) => line.setMap(null));
    polylinesRef.current = [];

    if (!map || !mapsLibrary || drawable.length === 0) return;

    polylinesRef.current = drawable.map((segment) => {
      const polyline = new mapsLibrary.Polyline({
        path: segment.path.map((point) => ({ lat: point.lat, lng: point.lng })),
        strokeColor: segment.color,
        strokeOpacity: segment.opacity,
        strokeWeight: segment.weight,
        geodesic: true,
        clickable: false,
        zIndex: segment.weight,
      });
      polyline.setMap(map);
      return polyline;
    });

    return () => {
      polylinesRef.current.forEach((line) => line.setMap(null));
      polylinesRef.current = [];
    };
  }, [map, mapsLibrary, drawable]);

  return null;
}

interface MapBoundsProps {
  routes: RouteOption[];
  selectedId?: string;
  viewAll: boolean;
}

export function MapBoundsFitter({ routes, selectedId, viewAll }: MapBoundsProps) {
  const map = useMap();
  const mapsLibrary = useMapsLibrary("core");

  useEffect(() => {
    if (!map || !mapsLibrary) return;

    const selectedRoute = routes.find((route) => route.id === selectedId) ?? routes[0];
    const targets = viewAll ? routes : selectedRoute ? [selectedRoute] : routes;

    const bounds = new mapsLibrary.LatLngBounds();
    let hasPoints = false;
    for (const route of targets) {
      for (const point of route.polyline) {
        bounds.extend({ lat: point.lat, lng: point.lng });
        hasPoints = true;
      }
    }
    if (!hasPoints) return;
    map.fitBounds(bounds, 48);
  }, [map, mapsLibrary, routes, selectedId, viewAll]);

  return null;
}

export function defaultMapCenter(routes: RouteOption[]) {
  const points: RouteOption["polyline"] = [];
  for (const route of routes) {
    for (const point of route.polyline) {
      points.push(point);
    }
  }
  if (points.length === 0) {
    return { lat: 30.2672, lng: -97.7431 };
  }
  const lat = points.reduce((sum, point) => sum + point.lat, 0) / points.length;
  const lng = points.reduce((sum, point) => sum + point.lng, 0) / points.length;
  return { lat, lng };
}
