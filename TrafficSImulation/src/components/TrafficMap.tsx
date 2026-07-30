import { useEffect, useMemo, useRef, useState } from "react";
import type { MapView, PlanResult, RouteOption } from "../types";
import { computeMapViewForPolylines, computeMapViewForPolyline } from "../utils/mapProjection";
import { RouteOverlay } from "./RouteOverlay";

interface TrafficMapProps {
  data: PlanResult | null;
  routes?: RouteOption[];
  selectedId?: string;
}

async function fetchMapEmbedUrl(view: MapView): Promise<string | null> {
  const response = await fetch("/api/map/embed", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(view),
  });
  const result = await response.json();
  if (!response.ok) {
    throw new Error(result.detail || "Unable to load map embed.");
  }
  return result.map_embed_url ?? null;
}

export function TrafficMap({ data, routes = [], selectedId }: TrafficMapProps) {
  const shellRef = useRef<HTMLElement>(null);
  const [size, setSize] = useState({ width: 0, height: 0 });
  const [embedUrl, setEmbedUrl] = useState<string | null>(data?.map_embed_url ?? null);
  const [mapView, setMapView] = useState<MapView | undefined>(data?.map_view);
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

  const computedView = useMemo(() => {
    if (isRealtime || size.width === 0 || size.height === 0) return undefined;

    if (viewAll) {
      const polylines = routes.map((route) => route.polyline).filter((line) => line.length > 1);
      return computeMapViewForPolylines(polylines, size.width, size.height) ?? undefined;
    }

    if (!selectedRoute?.polyline.length) return undefined;
    return computeMapViewForPolyline(selectedRoute.polyline, size.width, size.height) ?? undefined;
  }, [isRealtime, viewAll, selectedRoute, routes, size]);

  useEffect(() => {
    const node = shellRef.current;
    if (!node) return;

    const observer = new ResizeObserver(([entry]) => {
      const { width, height } = entry.contentRect;
      setSize({ width, height });
    });
    observer.observe(node);
    return () => observer.disconnect();
  }, []);

  useEffect(() => {
    if (isRealtime || !computedView) return;

    let cancelled = false;
    setMapView(computedView);

    void fetchMapEmbedUrl(computedView)
      .then((url) => {
        if (!cancelled) setEmbedUrl(url);
      })
      .catch(() => {
        if (!cancelled) setEmbedUrl(null);
      });

    return () => {
      cancelled = true;
    };
  }, [computedView, isRealtime]);

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

  const showMap = embedUrl && mapView;

  return (
    <section ref={shellRef} className="map-shell" aria-label="Google Maps route view">
      {showMap ? (
        <>
          <iframe
            key={embedUrl}
            title={`Map from ${data?.origin ?? "origin"} to ${data?.destination ?? "destination"}`}
            src={embedUrl}
            referrerPolicy="strict-origin-when-cross-origin"
            allowFullScreen
            tabIndex={-1}
            aria-hidden="true"
          />
          <RouteOverlay
            routes={routes}
            selectedId={selectedId}
            mapView={mapView}
            width={size.width}
            height={size.height}
          />
          {routes.length > 1 && (
            <button
              type="button"
              className={`map-view-all${viewAll ? " active" : ""}`}
              onClick={() => setViewAll(true)}
              aria-pressed={viewAll}
            >
              View all
            </button>
          )}
        </>
      ) : (
        <p className="map-placeholder">{data?.notice ?? "Enter two locations to compare routes."}</p>
      )}
    </section>
  );
}
