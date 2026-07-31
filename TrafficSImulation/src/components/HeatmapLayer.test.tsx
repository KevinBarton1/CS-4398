import React from "react";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import type { HeatmapResult } from "../types";
import {
  mockPolylineInstances,
  mockRectangleInstances,
  resetGoogleMapsMock,
} from "../test/googleMapsMock";

vi.mock("@vis.gl/react-google-maps", () => import("../test/googleMapsMock.tsx"));

const heatmapFixture: HeatmapResult = {
  metric: "congestion",
  rows: 2,
  columns: 2,
  scenario: { hour: 17, weather: 0, congestion: 56 },
  bounds: {
    north: 30.58,
    south: 29.95,
    east: -97.38,
    west: -98.11,
  },
  cells: [
    {
      row: 0,
      column: 0,
      value: 41,
      bounds: { north: 30.58, south: 30.315, east: -97.745, west: -98.11 },
    },
    {
      row: 0,
      column: 1,
      value: 52,
      bounds: { north: 30.58, south: 30.315, east: -97.38, west: -97.745 },
    },
  ],
  notice:
    "Simulated congestion field for the selected departure hour. Planning estimate, not observed traffic.",
};

beforeEach(() => {
  resetGoogleMapsMock();
});

afterEach(() => {
  vi.resetModules();
});

describe("HeatmapLayer", () => {
  it("T-51: draws one rectangle per cell and toggling off removes overlay", async () => {
    const { HeatmapLayer } = await import("./HeatmapLayer");
    const { RoutePolylineLayer } = await import("./RoutePolylineLayer");
    const { Map } = await import("@vis.gl/react-google-maps");

    const routes = [{
      id: "route-1",
      name: "Fastest",
      objective: "Minimum adjusted travel time",
      color: "#55d6be",
      distance_miles: 6.9,
      base_eta_minutes: 18,
      adjusted_eta_minutes: 21.7,
      estimated_price: 31.11,
      congestion_score: 56,
      normalized_score: 0,
      data_source: "Google Routes",
      polyline: [
        { lat: 30.2672, lng: -97.7431 },
        { lat: 30.1975, lng: -97.6664 },
      ],
      traffic_intervals: [{ start_index: 0, end_index: 1, speed: "NORMAL" }],
      segments: [],
      price_factors: {
        route_subtotal: 19.3,
        traffic_multiplier: 1.08,
        weather_multiplier: 1.03,
        time_multiplier: 1.0,
        unrounded_total: 31.11,
      },
      bounds: {
        north: 30.27,
        south: 30.19,
        east: -97.66,
        west: -97.75,
      },
    }];

    const { rerender } = render(
      <Map className="route-map">
        <HeatmapLayer heatmap={heatmapFixture} visible />
        <RoutePolylineLayer routes={routes} selectedRouteId="route-1" congestion={56} weatherSeverity={1} />
      </Map>,
    );

    await waitFor(() => expect(mockRectangleInstances).toHaveLength(2));
    expect(mockRectangleInstances[0]?.options.bounds?.north).toBe(30.58);
    await waitFor(() => expect(mockPolylineInstances.length).toBeGreaterThan(0));
    const polylineCount = mockPolylineInstances.length;

    rerender(
      <Map className="route-map">
        <HeatmapLayer heatmap={heatmapFixture} visible={false} />
        <RoutePolylineLayer routes={routes} selectedRouteId="route-1" congestion={56} weatherSeverity={1} />
      </Map>,
    );

    await waitFor(() => {
      mockRectangleInstances.forEach((rectangle) => {
        expect(rectangle.setMap).toHaveBeenCalledWith(null);
      });
    });
    expect(mockPolylineInstances.length).toBeGreaterThanOrEqual(polylineCount);
  });

  it("T-51: RouteMap toggle shows legend without disturbing route controls", async () => {
    const fetchMock = vi.fn();
    vi.stubGlobal("fetch", fetchMock);
    fetchMock.mockImplementation(async (input: RequestInfo | URL) => {
      const url = String(input);
      if (url.includes("/api/map/config")) {
        return {
          ok: true,
          json: async () => ({
            maps_browser_api_key: "browser-key",
            map_id: null,
            default_center: { lat: 30.2672, lng: -97.7431 },
            default_zoom: 12,
            color_scheme: "DARK",
            libraries: ["core", "maps"],
          }),
        };
      }
      if (url.includes("/api/heatmap")) {
        return {
          ok: true,
          json: async () => heatmapFixture,
        };
      }
      throw new Error(`Unexpected fetch: ${url}`);
    });

    const plan = {
      origin: "Downtown Austin",
      destination: "Austin Airport",
      mode: "simulated" as const,
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
      notice: "Simulated mode notice.",
      map_bounds: {
        north: 30.27,
        south: 30.19,
        east: -97.66,
        west: -97.75,
      },
      routes: [{
        id: "route-1",
        name: "Fastest",
        objective: "Minimum adjusted travel time",
        color: "#55d6be",
        distance_miles: 6.9,
        base_eta_minutes: 18,
        adjusted_eta_minutes: 21.7,
        estimated_price: 31.11,
        congestion_score: 56,
        normalized_score: 0,
        data_source: "Google Routes",
        polyline: [
          { lat: 30.2672, lng: -97.7431 },
          { lat: 30.1975, lng: -97.6664 },
        ],
        traffic_intervals: [{ start_index: 0, end_index: 1, speed: "NORMAL" }],
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
          polyline: [
            { lat: 30.2672, lng: -97.7431 },
            { lat: 30.1975, lng: -97.6664 },
          ],
        }],
        price_factors: {
          route_subtotal: 19.3,
          traffic_multiplier: 1.08,
          weather_multiplier: 1.03,
          time_multiplier: 1.0,
          unrounded_total: 31.11,
        },
        bounds: {
          north: 30.27,
          south: 30.19,
          east: -97.66,
          west: -97.75,
        },
      }],
    };

    const { MapConfigProvider } = await import("./MapConfigProvider");
    const { RouteMap } = await import("./RouteMap");

    render(
      <MapConfigProvider>
        <RouteMap
          routes={plan.routes}
          selectedRouteId="route-1"
          planBounds={plan.map_bounds}
          plan={plan}
          congestion={56}
          weatherSeverity={1}
          heatmapHour={17}
          heatmapCongestion={56}
          selectedRoute={plan.routes[0]}
          viewAll={false}
          onToggleViewAll={() => undefined}
        />
      </MapConfigProvider>,
    );

    await waitFor(() => expect(screen.getByRole("button", { name: "Congestion map" })).toBeInTheDocument());
    fireEvent.click(screen.getByRole("button", { name: "Congestion map" }));

    await waitFor(() =>
      expect(screen.getByLabelText("Congestion heatmap legend")).toBeInTheDocument(),
    );
    expect(screen.getByText(/Simulated congestion field/i)).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Congestion map" }));
    await waitFor(() =>
      expect(screen.queryByLabelText("Congestion heatmap legend")).not.toBeInTheDocument(),
    );
    expect(screen.getByTestId("google-map")).toBeInTheDocument();

    vi.unstubAllGlobals();
  });
});
