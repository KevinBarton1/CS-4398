import { useEffect, useMemo, useRef, useState } from "react";
import type { PlanResult, RouteOption } from "../types";
import { SimulatedRouteMap } from "./SimulatedRouteMap";

interface TrafficMapProps {
  data: PlanResult | null;
  routes?: RouteOption[];
  selectedId?: string;
}

export function TrafficMap({ data, routes = [], selectedId }: TrafficMapProps) {
  const shellRef = useRef<HTMLElement>(null);
  const [viewAll, setViewAll] = useState(false);

  const isRealtime = data?.mode === "realtime";
  const directionsUrl = data?.directions_embed_url ?? null;

  const selectedRoute = useMemo(
    () => routes.find((route) => route.id === selectedId) ?? routes[0],
    [routes, selectedId]
  );

  useEffect(() => {
    setViewAll(false);
  }, [selectedId]);

  if (isRealtime && directionsUrl) {
    return (
      <section
        ref={shellRef}
        className="map-shell realtime"
        aria-label="Google Maps real-time directions"
      >
        <iframe
          key={directionsUrl}
          title={`Real-time directions from ${data?.origin ?? "origin"} to ${data?.destination ?? "destination"}`}
          src={directionsUrl}
          referrerPolicy="strict-origin-when-cross-origin"
          allowFullScreen
        />
      </section>
    );
  }

  const hasRoutes = routes.some((route) => route.polyline.length > 1);

  return (
    <section ref={shellRef} className="map-shell simulated" aria-label="Google Maps route view">
      {hasRoutes ? (
        <SimulatedRouteMap
          routes={routes}
          selectedId={selectedId}
          congestion={data?.congestion ?? 56}
          weatherSeverity={data?.weather.severity ?? 0}
          viewAll={viewAll}
          onViewAll={() => setViewAll(true)}
          notice={data?.notice}
        />
      ) : (
        <p className="map-placeholder">{data?.notice ?? "Enter two locations to compare routes."}</p>
      )}
    </section>
  );
}
