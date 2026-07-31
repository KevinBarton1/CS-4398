import { useEffect, useState } from "react";
import {
  APILoadingStatus,
  ColorScheme,
  Map,
  useApiLoadingStatus,
} from "@vis.gl/react-google-maps";
import { useMapConfig } from "../hooks/useMapConfig";
import type { PlanResult, RouteOption, RouteBounds } from "../types";
import { MapBoundsController } from "./MapBoundsController";
import { RoutePolylineLayer } from "./RoutePolylineLayer";
import { StatusBanner } from "./StatusBanner";

interface RouteMapProps {
  routes: RouteOption[];
  selectedRouteId?: string;
  planBounds?: RouteBounds;
  plan: PlanResult | null;
  congestion: number;
  weatherSeverity: number;
  selectedRoute?: RouteOption;
}

function formatMapSummary(route?: RouteOption): string {
  if (!route) {
    return "No route selected.";
  }
  return `${route.name}: ${route.adjusted_eta_minutes} minutes, ${route.distance_miles} miles, estimated fare $${route.estimated_price.toFixed(2)}.`;
}

export function RouteMap({
  routes,
  selectedRouteId,
  planBounds,
  plan,
  congestion,
  weatherSeverity,
  selectedRoute,
}: RouteMapProps) {
  const { config } = useMapConfig();
  const apiStatus = useApiLoadingStatus();
  const [viewAll, setViewAll] = useState(false);
  const [apiRetryKey, setApiRetryKey] = useState(0);

  useEffect(() => {
    setViewAll(false);
  }, [selectedRouteId]);

  if (!config) {
    return null;
  }

  if (apiStatus === APILoadingStatus.FAILED) {
    return (
      <section className="map-shell" aria-label="Google Maps route view">
        <StatusBanner
          detail="The Google Maps script could not be loaded."
          onRetry={() => setApiRetryKey((current) => current + 1)}
          region="map"
        />
      </section>
    );
  }

  const hasDrawableRoutes = routes.some((route) => route.polyline.length > 1);

  return (
    <section className="map-shell" aria-label="Google Maps route view">
      <Map
        key={apiRetryKey}
        className="route-map"
        defaultCenter={config.default_center}
        defaultZoom={config.default_zoom}
        colorScheme={
          config.color_scheme === "LIGHT" ? ColorScheme.LIGHT : ColorScheme.DARK
        }
        mapId={config.map_id ?? undefined}
        gestureHandling="greedy"
        clickableIcons={false}
        disableDefaultUI={false}
      >
        {hasDrawableRoutes ? (
          <>
            <RoutePolylineLayer
              routes={routes}
              selectedRouteId={selectedRouteId}
              congestion={congestion}
              weatherSeverity={weatherSeverity}
            />
            <MapBoundsController
              routes={routes}
              selectedRouteId={selectedRouteId}
              planBounds={planBounds}
              viewAll={viewAll}
              plan={plan}
            />
          </>
        ) : null}
      </Map>
      {routes.length > 1 ? (
        <button
          type="button"
          className={`map-view-all${viewAll ? " active" : ""}`}
          aria-pressed={viewAll}
          onClick={() => setViewAll((current) => !current)}
        >
          View all
        </button>
      ) : null}
      <p className="visually-hidden">{formatMapSummary(selectedRoute)}</p>
      {!hasDrawableRoutes ? (
        <p className="map-placeholder">{plan?.notice ?? "Enter two locations to compare routes."}</p>
      ) : null}
    </section>
  );
}

export function RouteMapUnavailable({ detail, onRetry }: { detail: string; onRetry?: () => void }) {
  return (
    <section className="map-shell" aria-label="Google Maps route view">
      <StatusBanner detail={detail} onRetry={onRetry} region="map" />
    </section>
  );
}
