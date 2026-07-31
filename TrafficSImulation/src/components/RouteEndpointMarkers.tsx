import { useEffect, useRef } from "react";
import { useMap, useMapsLibrary } from "@vis.gl/react-google-maps";
import type { PlanResult, RouteOption } from "../types";

type MarkerLibrary = {
  Marker: new (options: google.maps.MarkerOptions) => google.maps.Marker;
};

interface RouteEndpointMarkersProps {
  plan: PlanResult | null;
  route?: RouteOption;
}

export function RouteEndpointMarkers({ plan, route }: RouteEndpointMarkersProps) {
  const map = useMap();
  const mapsLibrary = useMapsLibrary("maps") as MarkerLibrary | null;
  const markersRef = useRef<google.maps.Marker[]>([]);

  useEffect(() => {
    markersRef.current.forEach((marker) => marker.setMap(null));
    markersRef.current = [];

    if (!map || !mapsLibrary?.Marker || !route || !plan || route.polyline.length < 2) {
      return;
    }

    const originPoint = route.polyline[0];
    const destinationPoint = route.polyline[route.polyline.length - 1];
    const Marker = mapsLibrary.Marker;
    markersRef.current = [
      new Marker({
        map,
        position: { lat: originPoint.lat, lng: originPoint.lng },
        label: { text: "A", color: "#05241d", fontWeight: "700" },
        title: plan.origin,
      }),
      new Marker({
        map,
        position: { lat: destinationPoint.lat, lng: destinationPoint.lng },
        label: { text: "B", color: "#05241d", fontWeight: "700" },
        title: plan.destination,
      }),
    ];

    return () => {
      markersRef.current.forEach((marker) => marker.setMap(null));
      markersRef.current = [];
    };
  }, [map, mapsLibrary, route, plan]);

  return null;
}
