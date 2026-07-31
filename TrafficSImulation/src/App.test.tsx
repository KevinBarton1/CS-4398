import React from "react";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { vi } from "vitest";
import { App } from "./App";
import type { PlanResult, RouteOption } from "./types";

vi.mock("@vis.gl/react-google-maps", () => import("./test/googleMapsMock.tsx"));

const segmentPolyline = [
  { lat: 30.2672, lng: -97.7431 },
  { lat: 30.2500, lng: -97.7200 },
];

const bounds = {
  north: 30.2672,
  south: 30.1975,
  east: -97.6664,
  west: -97.7431,
};

const baseRoute: RouteOption = {
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
  traffic_intervals: [
    { start_index: 0, end_index: 2, speed: "NORMAL" },
    { start_index: 2, end_index: 4, speed: "SLOW" },
  ],
  segments: [{
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
  }],
  price_factors: {
    route_subtotal: 19.3,
    traffic_multiplier: 1.08,
    weather_multiplier: 1.03,
    time_multiplier: 1.0,
    unrounded_total: 31.11,
  },
  data_source: "Google Routes with departure-hour traffic",
  polyline: [
    { lat: 30.2672, lng: -97.7431 },
    { lat: 30.2500, lng: -97.7200 },
    { lat: 30.2300, lng: -97.6900 },
    { lat: 30.1975, lng: -97.6664 },
  ],
  bounds,
};

const simulatedResult: PlanResult = {
  origin: "Downtown Austin",
  destination: "Austin Airport",
  mode: "simulated",
  scenario_applied: true,
  scenario: { hour: 17, weather: 1, congestion: 56 },
  weather: {
    label: "Light rain",
    severity: 1,
    time_multiplier: 1.08,
    price_multiplier: 1.03,
    source: "Simulated fallback",
  },
  recommended_route_id: "route-1",
  notice:
    "Simulated mode: Google Maps supplies route geometry and departure-hour traffic; scenario controls adjust planning estimates.",
  map_bounds: bounds,
  routes: [
    baseRoute,
    { ...baseRoute, id: "route-2", name: "Balanced", color: "#ffb35c" },
    { ...baseRoute, id: "route-3", name: "Low traffic", color: "#4d72e8" },
  ],
};

const realtimeResult: PlanResult = {
  ...simulatedResult,
  mode: "realtime",
  scenario_applied: false,
  scenario: { hour: 17, weather: 0, congestion: 0 },
  routes: [baseRoute],
  notice:
    "Real-Time mode: route, distance, and travel time come from Google Maps traffic-aware routing for the current departure time.",
};

vi.stubGlobal("fetch", vi.fn(async (input: RequestInfo, init?: RequestInit) => {
  const url = String(input);
  if (url.includes("/api/map/config")) {
    return {
      ok: true,
      json: async () => ({
        maps_browser_api_key: "test-key",
        map_id: null,
        default_center: { lat: 30.2672, lng: -97.7431 },
        default_zoom: 12,
        color_scheme: "DARK",
        libraries: ["core", "maps"],
      }),
    };
  }
  const body = init?.body ? JSON.parse(String(init.body)) : {};
  if (body.mode === "realtime") {
    return { ok: true, json: async () => realtimeResult };
  }
  return { ok: true, json: async () => simulatedResult };
}));

test("renders the required hierarchy and API results", async () => {
  const { container } = render(<App />);
  expect(screen.getByRole("heading", { name: "Find the better drive." })).toBeInTheDocument();
  expect(screen.getByLabelText("Starting point")).toBeInTheDocument();
  expect(screen.getByLabelText("Destination or zone")).toBeInTheDocument();
  expect(screen.getByRole("button", { name: "Simulated" })).toBeInTheDocument();
  expect(screen.getByRole("button", { name: "Real-Time" })).toBeInTheDocument();
  await waitFor(() => expect(screen.getAllByText("$31.11")).toHaveLength(4));
  expect(screen.getByRole("button", { name: /Plan Route/ })).toBeInTheDocument();
  expect(screen.getByRole("heading", { name: "Fastest" })).toBeInTheDocument();
  expect(screen.getByText("Riverside Dr")).toBeInTheDocument();
  await waitFor(() => expect(screen.getByTestId("google-map")).toHaveClass("route-map"));
  expect(container.querySelector(".route-overlay")).not.toBeInTheDocument();
  expect(screen.getByRole("heading", { name: "Shape conditions" })).toBeInTheDocument();
});

test("realtime mode hides simulation controls", async () => {
  const { container } = render(<App />);
  await waitFor(() => expect(screen.getByRole("heading", { name: "Fastest" })).toBeInTheDocument());

  fireEvent.click(screen.getByRole("button", { name: "Real-Time" }));

  await waitFor(() => expect(screen.getByTestId("google-map")).toBeInTheDocument(), {
    timeout: 3000,
  });
  expect(screen.getByRole("button", { name: "Real-Time" })).toHaveClass("active");
  expect(container.querySelector(".source")).toHaveTextContent("Real-Time");
  expect(screen.getByText("Route comparison is available in Simulated mode.")).toBeInTheDocument();
  expect(screen.queryByRole("heading", { name: "Shape conditions" })).not.toBeInTheDocument();
});
