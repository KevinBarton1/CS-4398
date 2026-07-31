import React from "react";
import { render, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import type { PlanResult, RouteOption } from "../types";
import { mockFitBounds, resetGoogleMapsMock } from "../test/googleMapsMock";

vi.mock("@vis.gl/react-google-maps", () => import("../test/googleMapsMock.tsx"));

const bounds = {
  north: 30.27,
  south: 30.24,
  east: -97.71,
  west: -97.74,
};

const routeA: RouteOption = {
  id: "route-a",
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
    { lat: 30.27, lng: -97.74 },
    { lat: 30.24, lng: -97.71 },
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
  bounds: { ...bounds, west: -97.75 },
};

const routeB: RouteOption = {
  ...routeA,
  id: "route-b",
  bounds: { ...bounds, east: -97.7 },
};

const planOne: PlanResult = {
  origin: "A",
  destination: "B",
  mode: "simulated",
  scenario_applied: true,
  scenario: { hour: 17, weather: 1, congestion: 56 },
  weather: {
    severity: 1,
    label: "Light rain",
    time_multiplier: 1,
    price_multiplier: 1,
    source: "Simulated fallback",
  },
  recommended_route_id: "route-a",
  notice: "Notice",
  map_bounds: bounds,
  routes: [routeA, routeB],
};

const planTwo: PlanResult = {
  ...planOne,
  notice: "Updated notice",
};

describe("MapBoundsController", () => {
  beforeEach(() => {
    resetGoogleMapsMock();
  });

  it("T-34: fits selected bounds, plan bounds, and skips identical plan rerenders", async () => {
    const { MapBoundsController } = await import("./MapBoundsController");
    const { MockLatLngBounds } = await import("../test/googleMapsMock");

    const { rerender } = render(
      <MapBoundsController
        routes={planOne.routes}
        selectedRouteId="route-a"
        planBounds={planOne.map_bounds}
        viewAll={false}
        plan={planOne}
      />,
    );

    await waitFor(() => expect(mockFitBounds).toHaveBeenCalledTimes(1));
    expect(mockFitBounds.mock.calls[0][0]).toBeInstanceOf(MockLatLngBounds);

    rerender(
      <MapBoundsController
        routes={planOne.routes}
        selectedRouteId="route-b"
        planBounds={planOne.map_bounds}
        viewAll={false}
        plan={planOne}
      />,
    );
    await waitFor(() => expect(mockFitBounds).toHaveBeenCalledTimes(2));

    rerender(
      <MapBoundsController
        routes={planOne.routes}
        selectedRouteId="route-b"
        planBounds={planOne.map_bounds}
        viewAll={true}
        plan={planOne}
      />,
    );
    await waitFor(() => expect(mockFitBounds).toHaveBeenCalledTimes(3));

    rerender(
      <MapBoundsController
        routes={planTwo.routes}
        selectedRouteId="route-b"
        planBounds={planTwo.map_bounds}
        viewAll={true}
        plan={planTwo}
      />,
    );
    await waitFor(() => expect(mockFitBounds).toHaveBeenCalledTimes(4));

    rerender(
      <MapBoundsController
        routes={planTwo.routes}
        selectedRouteId="route-b"
        planBounds={planTwo.map_bounds}
        viewAll={true}
        plan={planTwo}
      />,
    );

    expect(mockFitBounds).toHaveBeenCalledTimes(4);
  });
});
