import { useEffect, useMemo, useRef } from "react";
import { useMap, useMapsLibrary } from "@vis.gl/react-google-maps";
import type { RouteOption } from "../types";
import { buildDrawablePolylines } from "./routePolylineSlices";

interface RoutePolylineLayerProps {
  routes: RouteOption[];
  selectedRouteId?: string;
  congestion: number;
  weatherSeverity: number;
  onSelectRoute?: (routeId: string) => void;
}

export function RoutePolylineLayer({
  routes,
  selectedRouteId,
  congestion,
  weatherSeverity,
  onSelectRoute,
}: RoutePolylineLayerProps) {
  const map = useMap();
  const mapsLibrary = useMapsLibrary("maps");
  const polylinesRef = useRef<google.maps.Polyline[]>([]);
  const listenersRef = useRef<Array<{ remove: () => void }>>([]);

  const drawable = useMemo(
    () => buildDrawablePolylines(routes, selectedRouteId, congestion, weatherSeverity),
    [routes, selectedRouteId, congestion, weatherSeverity],
  );

  useEffect(() => {
    polylinesRef.current.forEach((polyline) => polyline.setMap(null));
    listenersRef.current.forEach((listener) => listener.remove());
    polylinesRef.current = [];
    listenersRef.current = [];

    if (!map || !mapsLibrary || drawable.length === 0) {
      return;
    }

    polylinesRef.current = drawable.map((segment) => {
      const polyline = new mapsLibrary.Polyline({
        path: segment.path.map((point) => ({ lat: point.lat, lng: point.lng })),
        strokeColor: segment.color,
        strokeOpacity: segment.opacity,
        strokeWeight: segment.weight,
        geodesic: true,
        clickable: Boolean(onSelectRoute),
        zIndex: segment.zIndex,
      });
      polyline.setMap(map);
      if (onSelectRoute) {
        const listener = polyline.addListener("click", () => {
          onSelectRoute(segment.routeId);
        });
        listenersRef.current.push(listener);
      }
      return polyline;
    });

    return () => {
      listenersRef.current.forEach((listener) => listener.remove());
      listenersRef.current = [];
      polylinesRef.current.forEach((polyline) => polyline.setMap(null));
      polylinesRef.current = [];
    };
  }, [map, mapsLibrary, drawable, onSelectRoute]);

  return null;
}
