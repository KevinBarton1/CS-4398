import type { MapView, RouteOption } from "../types";
import { polylineToPath } from "../utils/mapProjection";
import { segmentColor } from "../utils/segmentColor";

interface RouteOverlayProps {
  routes: RouteOption[];
  selectedId?: string;
  mapView?: MapView;
  width: number;
  height: number;
  weatherSeverity?: number;
}

export function RouteOverlay({
  routes,
  selectedId,
  mapView,
  width,
  height,
  weatherSeverity = 0,
}: RouteOverlayProps) {
  if (!mapView || width === 0 || height === 0) {
    return <svg className="route-overlay" aria-hidden="true" />;
  }

  const drawable = routes.filter((route) => route.polyline.length > 1);
  if (drawable.length === 0) return null;

  return (
    <svg className="route-overlay" aria-hidden="true" viewBox={`0 0 ${width} ${height}`}>
      {drawable.map((route) => {
        const active = route.id === selectedId;
        const opacity = active ? 1 : selectedId ? 0.68 : 0.85;
        const strokeWidth = active ? 5 : 3;
        const segments = route.segments.filter((segment) => segment.polyline.length > 1);

        if (segments.length === 0) {
          const path = polylineToPath(route.polyline, mapView, width, height);
          return (
            <path
              key={route.id}
              d={path}
              fill="none"
              stroke={route.color}
              strokeWidth={strokeWidth}
              strokeLinecap="round"
              strokeLinejoin="round"
              opacity={opacity}
            />
          );
        }

        return segments.map((segment, index) => (
          <path
            key={`${route.id}-${segment.name}-${index}`}
            d={polylineToPath(segment.polyline, mapView, width, height)}
            fill="none"
            stroke={segmentColor(segment.congestion, segment.traffic_ratio, weatherSeverity)}
            strokeWidth={strokeWidth}
            strokeLinecap="round"
            strokeLinejoin="round"
            opacity={opacity}
          />
        ));
      })}
    </svg>
  );
}
