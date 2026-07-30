import { useEffect, useRef, useState } from "react";
import type { MapView, RouteOption } from "../types";
import { polylineToPath } from "../utils/mapProjection";

interface RouteOverlayProps {
  routes: RouteOption[];
  selectedId?: string;
  mapView?: MapView;
}

export function RouteOverlay({ routes, selectedId, mapView }: RouteOverlayProps) {
  const shellRef = useRef<SVGSVGElement>(null);
  const [size, setSize] = useState({ width: 0, height: 0 });

  useEffect(() => {
    const element = shellRef.current?.parentElement;
    if (!element) return;

    const observer = new ResizeObserver(([entry]) => {
      const { width, height } = entry.contentRect;
      setSize({ width, height });
    });
    observer.observe(element);
    return () => observer.disconnect();
  }, []);

  if (!mapView || size.width === 0 || size.height === 0) {
    return null;
  }

  const drawable = routes.filter((route) => route.polyline.length > 1);
  if (drawable.length === 0) {
    return null;
  }

  return (
    <svg
      ref={shellRef}
      className="route-overlay"
      viewBox={`0 0 ${size.width} ${size.height}`}
      aria-hidden="true"
    >
      {drawable.map((route) => {
        const selected = route.id === selectedId;
        const path = polylineToPath(route.polyline, mapView, size.width, size.height);
        return (
          <path
            key={route.id}
            d={path}
            fill="none"
            stroke={route.color}
            strokeWidth={selected ? 5 : 3}
            strokeLinecap="round"
            strokeLinejoin="round"
            opacity={selected ? 1 : selectedId ? 0.35 : 0.75}
          />
        );
      })}
    </svg>
  );
}
