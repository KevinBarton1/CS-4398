import type { PlanResult } from "../types";

interface TrafficMapProps {
  data: PlanResult | null;
}

export function TrafficMap({ data }: TrafficMapProps) {
  const embedUrl = data?.map_embed_url;

  return (
    <section className="map-shell" aria-label="Google Maps route view">
      {embedUrl ? (
        <iframe
          title={`Map from ${data?.origin ?? "origin"} to ${data?.destination ?? "destination"}`}
          src={embedUrl}
          referrerPolicy="strict-origin-when-cross-origin"
          allowFullScreen
        />
      ) : (
        <p className="map-placeholder">{data?.notice ?? "Enter two locations to compare routes."}</p>
      )}
    </section>
  );
}
