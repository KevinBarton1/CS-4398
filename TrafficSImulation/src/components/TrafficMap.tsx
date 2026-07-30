import type { PlanResult, RouteOption } from "../types";
import { RouteOverlay } from "./RouteOverlay";

interface TrafficMapProps {
  data: PlanResult | null;
  routes?: RouteOption[];
  selectedId?: string;
}

export function TrafficMap({ data, routes = [], selectedId }: TrafficMapProps) {
  const embedUrl = data?.map_embed_url;
  const mapView = data?.map_view;

  return (
    <section className="map-shell" aria-label="Google Maps route view">
      {embedUrl ? (
        <>
          <iframe
            title={`Map from ${data?.origin ?? "origin"} to ${data?.destination ?? "destination"}`}
            src={embedUrl}
            referrerPolicy="strict-origin-when-cross-origin"
            allowFullScreen
            tabIndex={-1}
            aria-hidden="true"
          />
          <RouteOverlay routes={routes} selectedId={selectedId} mapView={mapView} />
        </>
      ) : (
        <p className="map-placeholder">{data?.notice ?? "Enter two locations to compare routes."}</p>
      )}
    </section>
  );
}
