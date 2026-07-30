import type { MapView, RouteOption } from "../types";
import { polylineToPath } from "../utils/mapProjection";

interface RouteOverlayProps {
  routes: RouteOption[];
  selectedId?: string;
  mapView?: MapView;
  width: number;
  height: number;
}

export function RouteOverlay({ routes, selectedId, mapView, width, height }: RouteOverlayProps) {
  if (!mapView || width === 0 || height === 0) {
    return <svg className="route-overlay" aria-hidden="true" />;
  }

  const drawable = routes.filter((route) => route.polyline.length > 1);
  if (drawable.length === 0) return null;

  return (
    <svg className="route-overlay" aria-hidden="true" viewBox={`0 0 ${width} ${height}`}>
      {drawable.map((route) => {
        const active = route.id === selectedId;
        const path = polylineToPath(route.polyline, mapView, width, height);
        return (
          <path
            key={route.id}
            d={path}
            fill="none"
            stroke={route.color}
            strokeWidth={active ? 5 : 3}
            strokeLinecap="round"
            strokeLinejoin="round"
            opacity={active ? 1 : selectedId ? 0.68 : 0.85}
          />
        );
      })}
    </svg>
  );
}
