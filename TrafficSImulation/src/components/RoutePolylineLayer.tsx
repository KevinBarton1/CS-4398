import { useEffect, useMemo, useRef } from "react";
import { useMap, useMapsLibrary } from "@vis.gl/react-google-maps";
import type { RouteOption } from "../types";
import { buildDrawablePolylines } from "./routePolylineSlices";

interface RoutePolylineLayerProps {
  routes: RouteOption[];
  selectedRouteId?: string;
  congestion: number;
  weatherSeverity: number;
}

export function RoutePolylineLayer({
  routes,
  selectedRouteId,
  congestion,
  weatherSeverity,
}: RoutePolylineLayerProps) {
  const map = useMap();
  const mapsLibrary = useMapsLibrary("maps");
  const polylinesRef = useRef<google.maps.Polyline[]>([]);

  const drawable = useMemo(
    () => buildDrawablePolylines(routes, selectedRouteId, congestion, weatherSeverity),
    [routes, selectedRouteId, congestion, weatherSeverity],
  );

  useEffect(() => {
    polylinesRef.current.forEach((polyline) => polyline.setMap(null));
    polylinesRef.current = [];

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
        clickable: false,
        zIndex: segment.zIndex,
      });
      polyline.setMap(map);
      return polyline;
    });

    return () => {
      polylinesRef.current.forEach((polyline) => polyline.setMap(null));
      polylinesRef.current = [];
    };
  }, [map, mapsLibrary, drawable]);

  return null;
}
