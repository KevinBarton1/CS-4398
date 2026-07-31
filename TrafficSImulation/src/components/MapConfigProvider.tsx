import type { ReactNode } from "react";
import { APIProvider } from "@vis.gl/react-google-maps";
import { useMapConfig } from "../hooks/useMapConfig";
import { RouteMapUnavailable } from "./RouteMap";

interface MapConfigProviderProps {
  children: ReactNode;
}

export function MapConfigProvider({ children }: MapConfigProviderProps) {
  const { config, status, error, retry } = useMapConfig();

  if (status === "loading" || status === "idle") {
    return (
      <section className="map-shell" aria-label="Google Maps route view">
        <p className="map-placeholder">Loading map configuration...</p>
      </section>
    );
  }

  if (status === "error" || !config) {
    return (
      <RouteMapUnavailable
        error={
          error ?? {
            detail: "Map configuration is unavailable.",
            code: null,
            fields: null,
          }
        }
        onRetry={retry}
      />
    );
  }

  return (
    <APIProvider apiKey={config.maps_browser_api_key} libraries={config.libraries}>
      {children}
    </APIProvider>
  );
}
