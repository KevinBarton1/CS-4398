import React from "react";
import { render, screen, waitFor } from "@testing-library/react";
import { vi } from "vitest";
import { App } from "./App";

const result = {
  origin: "Downtown Austin", destination: "Austin Airport", mode: "simulated",
  hour: 17, congestion: 56, demand: 68, recommended_route_id: "route-1",
  notice: "Simulated planning estimate.",
  weather: { label: "Light rain", severity: 1, time_multiplier: 1.08, price_multiplier: 1.03 },
  heatmap: { mode: "congestion", cells: [{ row: 0, column: 0, value: 50 }] },
  routes: [{
    id: "route-1", name: "Fastest", objective: "Minimum adjusted time", color: "#55d6be",
    distance_miles: 6.9, base_eta_minutes: 18, adjusted_eta_minutes: 21.7,
    estimated_price: 31.11, congestion_score: 56, demand_score: 68, normalized_score: 0.5,
    points: [{ x: 500, y: 330 }, { x: 620, y: 400 }, { x: 795, y: 495 }],
    segments: [{ name: "Riverside Dr", length_miles: 3.8, lanes: 3, speed_limit_mph: 45,
      average_speed_mph: 36.2, volume_vehicles_hour: 970, congestion: 0.26,
      capacity_vehicles_hour: 1560, free_flow_minutes: 5, adjusted_minutes: 5.2 }],
    factors: { route_subtotal: 19.3, demand_multiplier: 1.19, traffic_multiplier: 1.08,
      weather_multiplier: 1.03, time_multiplier: 1.22, unrounded_total: 31.11 },
    data_source: "Simulated scenario"
  }]
};

vi.stubGlobal("fetch", vi.fn(async () => ({
  ok: true,
  json: async () => result
})));

test("renders the required hierarchy and API results", async () => {
  render(<App />);
  expect(screen.getByRole("heading", { name: "Find the better drive." })).toBeInTheDocument();
  expect(screen.getByLabelText("Starting point")).toBeInTheDocument();
  expect(screen.getByLabelText("Destination or zone")).toBeInTheDocument();
  expect(screen.getByRole("button", { name: "Simulated" })).toBeInTheDocument();
  await waitFor(() => expect(screen.getAllByText("$31.11")).toHaveLength(2));
  expect(screen.getByRole("heading", { name: "Fastest" })).toBeInTheDocument();
  expect(screen.getByText("Riverside Dr")).toBeInTheDocument();
});
