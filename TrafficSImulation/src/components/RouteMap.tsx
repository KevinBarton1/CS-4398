import { useId, useState } from "react";
import {
  APILoadingStatus,
  ColorScheme,
  Map,
  useApiLoadingStatus,
} from "@vis.gl/react-google-maps";
import { useMapConfig } from "../hooks/useMapConfig";
import type { PlanResult, RouteOption, RouteBounds } from "../types";
import { MapBoundsController } from "./MapBoundsController";
import { RouteEndpointMarkers } from "./RouteEndpointMarkers";
import { RoutePolylineLayer } from "./RoutePolylineLayer";
import type { ApiError } from "../types";
import { StatusBanner } from "./StatusBanner";

interface RouteMapProps {
  routes: RouteOption[];
  selectedRouteId?: string;
  planBounds?: RouteBounds;
  plan: PlanResult | null;
  congestion: number;
  weatherSeverity: number;
  selectedRoute?: RouteOption;
  viewAll: boolean;
  onToggleViewAll: () => void;
  onSelectRoute?: (routeId: string) => void;
}

function countTrafficIntervals(route: RouteOption, speed: string): number {
  return route.traffic_intervals.filter((interval) => interval.speed === speed).length;
}

function formatStretchCount(count: number, label: string): string {
  return `${count} ${label} stretch${count === 1 ? "" : "es"}`;
}

export function formatMapDescription(route?: RouteOption): string {
  if (!route) {
    return "No route selected.";
  }

  const slow = countTrafficIntervals(route, "SLOW");
  const heavy = countTrafficIntervals(route, "TRAFFIC_JAM");
  const stretchParts: string[] = [];
  if (slow > 0) {
    stretchParts.push(formatStretchCount(slow, "slow"));
  }
  if (heavy > 0) {
    stretchParts.push(formatStretchCount(heavy, "heavy"));
  }
  const stretchSummary = stretchParts.length > 0 ? `, ${stretchParts.join(" and ")}` : "";

  return `${route.name} route, ${route.adjusted_eta_minutes.toFixed(1)} min, ${route.distance_miles.toFixed(1)} mi${stretchSummary}`;
}

export function RouteMap({
  routes,
  selectedRouteId,
  planBounds,
  plan,
  congestion,
  weatherSeverity,
  selectedRoute,
  viewAll,
  onToggleViewAll,
  onSelectRoute,
}: RouteMapProps) {
  const { config } = useMapConfig();
  const apiStatus = useApiLoadingStatus();
  const [apiRetryKey, setApiRetryKey] = useState(0);
  const descriptionId = useId();

  if (!config) {
    return null;
  }

  if (apiStatus === APILoadingStatus.FAILED) {
    return (
      <div className="map-shell">
        <StatusBanner
          variant="error"
          detail="The Google Maps script could not be loaded."
          guidance="Try again in a moment."
          onRetry={() => setApiRetryKey((current) => current + 1)}
          region="map"
        />
      </div>
    );
  }

  const hasDrawableRoutes = routes.some((route) => route.polyline.length > 1);
  const mapDescription = formatMapDescription(selectedRoute);
  const markerRoute = selectedRoute ?? routes[0];

  return (
    <div className="map-shell" aria-describedby={descriptionId}>
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
              onSelectRoute={onSelectRoute}
            />
            <RouteEndpointMarkers plan={plan} route={markerRoute} />
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
          onClick={onToggleViewAll}
        >
          View all
        </button>
      ) : null}
      <p id={descriptionId} className="visually-hidden">
        {mapDescription}
        {plan && markerRoute ? ` Origin marker: ${plan.origin}. Destination marker: ${plan.destination}.` : ""}
      </p>
      {!hasDrawableRoutes ? (
        <p className="map-placeholder">{plan?.notice ?? "Enter two locations to compare routes."}</p>
      ) : null}
    </div>
  );
}

export function RouteMapUnavailable({
  error,
  onRetry,
}: {
  error: ApiError;
  onRetry?: () => void;
}) {
  return (
    <div className="map-shell">
      <StatusBanner variant="error" error={error} onRetry={onRetry} region="map" />
    </div>
  );
}
