import type { PlanResult, RouteOption } from "../types";

export const segmentPolyline = [
  { lat: 30.2672, lng: -97.7431 },
  { lat: 30.2500, lng: -97.7200 },
];

export const bounds = {
  north: 30.2672,
  south: 30.1975,
  east: -97.6664,
  west: -97.7431,
};

export function makeSegment(overrides: Partial<RouteOption["segments"][number]> = {}) {
  return {
    name: "Riverside Dr",
    length_miles: 3.8,
    lanes: 3,
    speed_limit_mph: 45,
    average_speed_mph: 36.2,
    volume_vehicles_hour: 970,
    congestion: 0.26,
    capacity_vehicles_hour: 1560,
    free_flow_minutes: 5,
    adjusted_minutes: 5.2,
    traffic_ratio: 1.2,
    polyline: segmentPolyline,
    ...overrides,
  };
}

export function makeRoute(overrides: Partial<RouteOption> = {}): RouteOption {
  return {
    id: "route-1",
    name: "Fastest",
    objective: "Minimum adjusted time",
    color: "#55d6be",
    distance_miles: 6.9,
    base_eta_minutes: 18,
    adjusted_eta_minutes: 21.7,
    estimated_price: 31.11,
    congestion_score: 56,
    normalized_score: 0.5,
    traffic_intervals: [{ start_index: 0, end_index: 2, speed: "NORMAL" }],
    segments: [makeSegment()],
    price_factors: {
      route_subtotal: 19.3,
      traffic_multiplier: 1.08,
      weather_multiplier: 1.03,
      time_multiplier: 1.0,
      unrounded_total: 31.11,
    },
    data_source: "Google Routes with departure-hour traffic",
    polyline: segmentPolyline,
    bounds,
    ...overrides,
  };
}

export const weather = {
  label: "Light rain",
  severity: 1,
  time_multiplier: 1.08,
  price_multiplier: 1.03,
  source: "Simulated fallback",
};

export function makePlan(overrides: Partial<PlanResult> = {}): PlanResult {
  const route1 = makeRoute();
  const route2 = makeRoute({
    id: "route-2",
    name: "Balanced",
    color: "#ffb35c",
    adjusted_eta_minutes: 24.5,
    estimated_price: 28.4,
    segments: [
      makeSegment({ name: "Congress Ave", length_miles: 2.1, congestion: 0.73 }),
    ],
    price_factors: {
      route_subtotal: 18.0,
      traffic_multiplier: 1.05,
      weather_multiplier: 1.03,
      time_multiplier: 1.0,
      unrounded_total: 28.4,
    },
  });
  const route3 = makeRoute({
    id: "route-3",
    name: "Low traffic",
    color: "#4d72e8",
  });

  return {
    origin: "Downtown Austin",
    destination: "Austin Airport",
    mode: "simulated",
    scenario_applied: true,
    scenario: { hour: 17, weather: 1, congestion: 56 },
    weather,
    recommended_route_id: "route-1",
    notice:
      "Simulated mode: Google Maps supplies route geometry and departure-hour traffic; scenario controls adjust planning estimates.",
    map_bounds: bounds,
    routes: [route1, route2, route3],
    ...overrides,
  };
}
