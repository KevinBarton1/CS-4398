import React from "react";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { vi } from "vitest";
import { App } from "./App";

vi.mock("./components/SimulatedRouteMap", () => ({
  SimulatedRouteMap: () => <div role="application" aria-label="Simulated route map" />,
}));

const segmentPolyline = [
  { lat: 30.2672, lng: -97.7431 },
  { lat: 30.2500, lng: -97.7200 },
];

const simulatedResult = {
  origin: "Downtown Austin", destination: "Austin Airport", mode: "simulated",
  hour: 17, congestion: 56, recommended_route_id: "route-1",
  notice: "Route geometry and distances from Google Maps with departure-hour traffic; weather adjusts planning estimates.",
  directions_embed_url:
    "https://www.google.com/maps/embed/v1/directions?key=test&origin=Downtown+Austin&destination=Austin+Airport&mode=driving",
  map_embed_url: "https://www.google.com/maps/embed/v1/view?key=test&center=30.2324,-97.7048&zoom=12&maptype=roadmap",
  map_view: { center_lat: 30.2324, center_lng: -97.7048, zoom: 12 },
  weather: { label: "Light rain", severity: 1, time_multiplier: 1.08, price_multiplier: 1.03 },
  routes: [{
    id: "route-1", name: "Fastest", objective: "Minimum adjusted time", color: "#55d6be",
    distance_miles: 6.9, base_eta_minutes: 18, adjusted_eta_minutes: 21.7,
    estimated_price: 31.11, congestion_score: 56, normalized_score: 0.5,
    traffic_intervals: [
      { start_index: 0, end_index: 2, speed: "NORMAL" },
      { start_index: 2, end_index: 4, speed: "SLOW" },
    ],
    segments: [{
      name: "Riverside Dr", length_miles: 3.8, lanes: 3, speed_limit_mph: 45,
      average_speed_mph: 36.2, volume_vehicles_hour: 970, congestion: 0.26,
      capacity_vehicles_hour: 1560, free_flow_minutes: 5, adjusted_minutes: 5.2,
      traffic_ratio: 1.2, polyline: segmentPolyline,
    }],
    factors: { route_subtotal: 19.3, traffic_multiplier: 1.08,
      weather_multiplier: 1.03, unrounded_total: 31.11 },
    data_source: "Google Maps route geometry",
    polyline: [
      { lat: 30.2672, lng: -97.7431 },
      { lat: 30.2500, lng: -97.7200 },
      { lat: 30.2300, lng: -97.6900 },
      { lat: 30.1975, lng: -97.6664 },
    ],
    map_view: { center_lat: 30.2324, center_lng: -97.7048, zoom: 12 },
    map_embed_url: "https://www.google.com/maps/embed/v1/view?key=test&center=30.2324,-97.7048&zoom=12&maptype=roadmap",
  }]
};

simulatedResult.routes.push(
  {
    ...simulatedResult.routes[0],
    id: "route-2",
    name: "Balanced",
    color: "#ffb35c",
  },
  {
    ...simulatedResult.routes[0],
    id: "route-3",
    name: "Low traffic",
    color: "#4d72e8",
  }
);

const realtimeResult = {
  ...simulatedResult,
  mode: "realtime",
  routes: [simulatedResult.routes[0]],
  notice: "Real-Time mode: route, distance, and travel time from Google Maps with traffic-aware routing.",
};

vi.stubGlobal("fetch", vi.fn(async (input: RequestInfo, init?: RequestInit) => {
  const url = String(input);
  if (url.includes("/api/map/config")) {
    return { ok: true, json: async () => ({ maps_api_key: "test-key" }) };
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
  await waitFor(() =>
    expect(screen.getByRole("application", { name: "Simulated route map" })).toBeInTheDocument()
  );
  expect(container.querySelector(".route-overlay")).not.toBeInTheDocument();
  expect(screen.getByRole("heading", { name: "Shape conditions" })).toBeInTheDocument();
});

test("realtime mode shows directions map and hides simulation controls", async () => {
  const { container } = render(<App />);
  await waitFor(() => expect(screen.getByRole("heading", { name: "Fastest" })).toBeInTheDocument());

  fireEvent.click(screen.getByRole("button", { name: "Real-Time" }));

  await waitFor(() =>
    expect(
      screen.getByTitle("Real-time directions from Downtown Austin to Austin Airport")
    ).toBeInTheDocument()
  );
  expect(container.querySelector(".map-shell.realtime")).toBeInTheDocument();
  expect(container.querySelector(".route-overlay")).not.toBeInTheDocument();
  expect(screen.queryByRole("application", { name: "Simulated route map" })).not.toBeInTheDocument();
  expect(screen.getByRole("button", { name: "Real-Time" })).toHaveClass("active");
  expect(container.querySelector(".source")).toHaveTextContent("Real-Time");
  expect(screen.getByText("Route comparison is available in Simulated mode.")).toBeInTheDocument();
  expect(screen.queryByRole("heading", { name: "Shape conditions" })).not.toBeInTheDocument();
});
