import React from "react";
import { render, screen, waitFor } from "@testing-library/react";
import { vi } from "vitest";
import { App } from "./App";

const result = {
  origin: "Downtown Austin", destination: "Austin Airport", mode: "simulated",
  hour: 17, congestion: 56, demand: 68, recommended_route_id: "route-1",
  notice: "Simulated planning estimate.",
  map_embed_url: "https://www.google.com/maps/embed/v1/view?key=test&center=30.2324,-97.7048&zoom=12&maptype=roadmap",
  map_view: { center_lat: 30.2324, center_lng: -97.7048, zoom: 12 },
  weather: { label: "Light rain", severity: 1, time_multiplier: 1.08, price_multiplier: 1.03 },
  routes: [{
    id: "route-1", name: "Fastest", objective: "Minimum adjusted time", color: "#55d6be",
    distance_miles: 6.9, base_eta_minutes: 18, adjusted_eta_minutes: 21.7,
    estimated_price: 31.11, congestion_score: 56, demand_score: 68, normalized_score: 0.5,
    segments: [{ name: "Riverside Dr", length_miles: 3.8, lanes: 3, speed_limit_mph: 45,
      average_speed_mph: 36.2, volume_vehicles_hour: 970, congestion: 0.26,
      capacity_vehicles_hour: 1560, free_flow_minutes: 5, adjusted_minutes: 5.2 }],
    factors: { route_subtotal: 19.3, demand_multiplier: 1.19, traffic_multiplier: 1.08,
      weather_multiplier: 1.03, time_multiplier: 1.22, unrounded_total: 31.11 },
    data_source: "Simulated scenario",
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

result.routes.push(
  {
    ...result.routes[0],
    id: "route-2",
    name: "Balanced",
    color: "#ffb35c",
  },
  {
    ...result.routes[0],
    id: "route-3",
    name: "Low traffic",
    color: "#4d72e8",
  }
);

vi.stubGlobal("fetch", vi.fn(async (input: RequestInfo, init?: RequestInit) => {
  const url = String(input);
  if (url.includes("/api/map/embed")) {
    const body = JSON.parse(String(init?.body ?? "{}"));
    return {
      ok: true,
      json: async () => ({
        map_embed_url:
          `https://www.google.com/maps/embed/v1/view?key=test&center=${body.center_lat},${body.center_lng}&zoom=${body.zoom}&maptype=roadmap`,
      }),
    };
  }
  return { ok: true, json: async () => result };
}));

test("renders the required hierarchy and API results", async () => {
  const { container } = render(<App />);
  expect(screen.getByRole("heading", { name: "Find the better drive." })).toBeInTheDocument();
  expect(screen.getByLabelText("Starting point")).toBeInTheDocument();
  expect(screen.getByLabelText("Destination or zone")).toBeInTheDocument();
  expect(screen.getByRole("button", { name: "Simulated" })).toBeInTheDocument();
  await waitFor(() => expect(screen.getAllByText("$31.11")).toHaveLength(4));
  expect(screen.getByRole("heading", { name: "Fastest" })).toBeInTheDocument();
  expect(screen.getByText("Riverside Dr")).toBeInTheDocument();
  await waitFor(() =>
    expect(screen.getByTitle("Map from Downtown Austin to Austin Airport")).toBeInTheDocument()
  );
  expect(container.querySelector(".route-overlay")).toBeInTheDocument();
  expect(screen.getByRole("button", { name: "View all" })).toBeInTheDocument();
  expect(container.querySelector(".roads")).not.toBeInTheDocument();
  expect(container.querySelector(".water")).not.toBeInTheDocument();
});
