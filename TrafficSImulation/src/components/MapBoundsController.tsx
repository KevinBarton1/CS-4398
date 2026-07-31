import { useEffect } from "react";
import { useMap, useMapsLibrary } from "@vis.gl/react-google-maps";
import type { PlanResult, RouteBounds, RouteOption } from "../types";

interface MapBoundsControllerProps {
  routes: RouteOption[];
  selectedRouteId?: string;
  planBounds?: RouteBounds;
  viewAll: boolean;
  plan: PlanResult | null;
}

function toLatLngBounds(
  coreLibrary: {
    LatLngBounds: new (
      sw: google.maps.LatLngLiteral,
      ne: google.maps.LatLngLiteral,
    ) => google.maps.LatLngBounds;
  },
  bounds: RouteBounds,
): google.maps.LatLngBounds {
  return new coreLibrary.LatLngBounds(
    { lat: bounds.south, lng: bounds.west },
    { lat: bounds.north, lng: bounds.east },
  );
}

export function MapBoundsController({
  routes,
  selectedRouteId,
  planBounds,
  viewAll,
  plan,
}: MapBoundsControllerProps) {
  const map = useMap();
  const coreLibrary = useMapsLibrary("core");

  useEffect(() => {
    if (!map || !coreLibrary) {
      return;
    }

    const selectedRoute = routes.find((route) => route.id === selectedRouteId) ?? routes[0];
    const targetBounds = viewAll ? planBounds : selectedRoute?.bounds;
    if (!targetBounds) {
      return;
    }

    map.fitBounds(toLatLngBounds(coreLibrary, targetBounds), 48);
  }, [map, coreLibrary, selectedRouteId, viewAll, plan]); // eslint-disable-line react-hooks/exhaustive-deps

  return null;
}
