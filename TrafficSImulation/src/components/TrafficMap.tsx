import { useEffect, useRef, useState } from "react";
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

  useEffect(() => {
    setViewAll(false);
  }, [selectedId]);

  if (isRealtime) {
    return (
      <section
        ref={shellRef}
        className="map-shell realtime"
        aria-label="Google Maps real-time directions"
      >
        <p className="map-placeholder">{data?.notice ?? "Real-Time route view loading."}</p>
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
          congestion={data?.scenario.congestion ?? 56}
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
