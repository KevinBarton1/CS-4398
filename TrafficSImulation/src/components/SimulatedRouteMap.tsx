import { useEffect, useState } from "react";
import { APIProvider, Map } from "@vis.gl/react-google-maps";
import type { RouteOption } from "../types";
import { defaultMapCenter, MapBoundsFitter, RoutePolylines } from "./RoutePolylines";

interface SimulatedRouteMapProps {
  routes: RouteOption[];
  selectedId?: string;
  congestion: number;
  weatherSeverity: number;
  viewAll: boolean;
  onViewAll: () => void;
  notice?: string;
}

async function fetchMapsApiKey(): Promise<string | null> {
  const response = await fetch("/api/map/config");
  if (!response.ok) return null;
  const body = await response.json();
  return body.maps_api_key ?? null;
}

export function SimulatedRouteMap({
  routes,
  selectedId,
  congestion,
  weatherSeverity,
  viewAll,
  onViewAll,
  notice,
}: SimulatedRouteMapProps) {
  const [apiKey, setApiKey] = useState<string | null>(null);
  const [loadError, setLoadError] = useState(false);

  useEffect(() => {
    let cancelled = false;
    void fetchMapsApiKey()
      .then((key) => {
        if (!cancelled) {
          setApiKey(key);
          setLoadError(!key);
        }
      })
      .catch(() => {
        if (!cancelled) setLoadError(true);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  if (loadError || !apiKey) {
    return (
      <p className="map-placeholder">
        {notice ?? "Configure GOOGLE_MAPS_API_KEY to load the interactive map."}
      </p>
    );
  }

  const center = defaultMapCenter(routes);

  return (
    <APIProvider apiKey={apiKey}>
      <Map
        className="simulated-map"
        aria-label="Simulated route map"
        defaultCenter={center}
        defaultZoom={12}
        gestureHandling="greedy"
        disableDefaultUI={false}
        clickableIcons={false}
        colorScheme="DARK"
      >
        <RoutePolylines
          routes={routes}
          selectedId={selectedId}
          congestion={congestion}
          weatherSeverity={weatherSeverity}
        />
        <MapBoundsFitter routes={routes} selectedId={selectedId} viewAll={viewAll} />
      </Map>
      {routes.length > 1 && (
        <button
          type="button"
          className={`map-view-all${viewAll ? " active" : ""}`}
          onClick={onViewAll}
          aria-pressed={viewAll}
        >
          View all
        </button>
      )}
    </APIProvider>
  );
}
