import React from "react";
import { render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { resetMapConfigCache } from "../hooks/useMapConfig";
import type { PlanResult, RouteOption } from "../types";

vi.mock("@vis.gl/react-google-maps", () => import("../test/googleMapsMock.tsx"));

const fetchMock = vi.fn();

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
  bounds,
};

const plan: PlanResult = {
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
  notice: "Simulated mode notice.",
  map_bounds: bounds,
  routes: [baseRoute],
};

beforeEach(() => {
  resetMapConfigCache();
  fetchMock.mockReset();
  vi.stubGlobal("fetch", fetchMock);
});

afterEach(() => {
  resetMapConfigCache();
  vi.unstubAllGlobals();
});

describe("RouteMap and MapConfigProvider", () => {
  it("T-31: mounts APIProvider with fetched credentials on success", async () => {
    fetchMock.mockResolvedValue({
      ok: true,
      json: async () => ({
        maps_browser_api_key: "browser-key",
        map_id: null,
        default_center: { lat: 30.2672, lng: -97.7431 },
        default_zoom: 12,
        color_scheme: "DARK",
        libraries: ["core", "maps"],
      }),
    });

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
          selectedRoute={baseRoute}
          viewAll={false}
          onToggleViewAll={() => undefined}
        />
      </MapConfigProvider>,
    );

    await waitFor(() => expect(screen.getByTestId("api-provider")).toBeInTheDocument());
    expect(screen.getByTestId("api-provider")).toHaveAttribute("data-api-key", "browser-key");
    expect(screen.getByTestId("api-provider")).toHaveAttribute(
      "data-libraries",
      JSON.stringify(["core", "maps"]),
    );
    expect(screen.getByTestId("google-map")).toHaveClass("route-map");
  });

  it("T-31: contains config failures to the map region", async () => {
    fetchMock.mockResolvedValue({
      ok: false,
      status: 503,
      json: async () => ({
        detail: "Google Maps browser credential is not configured.",
        code: "maps_not_configured",
      }),
    });

    const { MapConfigProvider } = await import("./MapConfigProvider");
    const { RouteMap } = await import("./RouteMap");

    render(
      <MapConfigProvider>
        <RouteMap
          routes={plan.routes}
          selectedRouteId="route-1"
          planBounds={plan.map_bounds}
          plan={plan}
          congestion={0}
          weatherSeverity={0}
          selectedRoute={baseRoute}
          viewAll={false}
          onToggleViewAll={() => undefined}
        />
      </MapConfigProvider>,
    );

    await waitFor(() =>
      expect(
        screen.getByText("Google Maps browser credential is not configured."),
      ).toBeInTheDocument(),
    );
    expect(screen.queryByTestId("api-provider")).not.toBeInTheDocument();
    expect(screen.queryByTestId("google-map")).not.toBeInTheDocument();
  });
});
