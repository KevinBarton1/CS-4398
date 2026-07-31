import React from "react";
import { render, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import type { RouteOption } from "../types";
import {
  mockPolylineInstances,
  mockPolylineSetMap,
  resetGoogleMapsMock,
} from "../test/googleMapsMock";
import { buildDrawablePolylines, intervalsForRoute, sliceIntervalPath } from "./routePolylineSlices";

vi.mock("@vis.gl/react-google-maps", () => import("../test/googleMapsMock.tsx"));

const polyline = [
  { lat: 30.27, lng: -97.74 },
  { lat: 30.26, lng: -97.73 },
  { lat: 30.25, lng: -97.72 },
  { lat: 30.24, lng: -97.71 },
];

const bounds = {
  north: 30.27,
  south: 30.24,
  east: -97.71,
  west: -97.74,
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
  polyline,
  traffic_intervals: [
    { start_index: 0, end_index: 1, speed: "NORMAL" },
    { start_index: 1, end_index: 3, speed: "SLOW" },
  ],
  segments: [],
  price_factors: {
    route_subtotal: 19.3,
    traffic_multiplier: 1.08,
    weather_multiplier: 1.03,
    time_multiplier: 1.0,
    unrounded_total: 31.11,
  },
  bounds,
};

describe("routePolylineSlices", () => {
  it("includes the end_index vertex in each slice", () => {
    const intervals = intervalsForRoute(baseRoute);
    const first = sliceIntervalPath(polyline, intervals[0]);
    const second = sliceIntervalPath(polyline, intervals[1]);
    expect(first).toEqual(polyline.slice(0, 2));
    expect(second).toEqual(polyline.slice(1, 4));
  });

  it("creates one NORMAL interval when traffic_intervals is empty", () => {
    const route = { ...baseRoute, traffic_intervals: [] };
    expect(intervalsForRoute(route)).toEqual([
      { start_index: 0, end_index: polyline.length - 1, speed: "NORMAL" },
    ]);
    expect(buildDrawablePolylines([route], "route-1", 0, 0)).toHaveLength(1);
  });

  it("clamps out-of-range indices without throwing", () => {
    const path = sliceIntervalPath(polyline, {
      start_index: -5,
      end_index: 99,
      speed: "SLOW",
    });
    expect(path.length).toBeGreaterThan(1);
  });
});

describe("RoutePolylineLayer", () => {
  beforeEach(() => {
    resetGoogleMapsMock();
  });

  it("T-32: creates one polyline per interval with selected-route emphasis", async () => {
    const { RoutePolylineLayer } = await import("./RoutePolylineLayer");

    const { rerender, unmount } = render(
      <RoutePolylineLayer
        routes={[baseRoute]}
        selectedRouteId="route-1"
        congestion={56}
        weatherSeverity={1}
      />,
    );

    await waitFor(() => expect(mockPolylineInstances).toHaveLength(2));
    expect(mockPolylineInstances.every((line) => line.options.strokeWeight === 6)).toBe(true);
    expect(mockPolylineInstances.every((line) => line.options.strokeOpacity === 1)).toBe(true);

    const createdBeforeRerender = mockPolylineInstances.length;
    rerender(
      <RoutePolylineLayer
        routes={[baseRoute, { ...baseRoute, id: "route-2" }]}
        selectedRouteId="route-1"
        congestion={56}
        weatherSeverity={1}
      />,
    );

    await waitFor(() => expect(mockPolylineInstances.length).toBe(createdBeforeRerender + 4));
    expect(mockPolylineSetMap.mock.calls.some(([mapValue]) => mapValue === null)).toBe(true);

    const disposeCallsBeforeUnmount = mockPolylineSetMap.mock.calls.filter(
      ([mapValue]) => mapValue === null,
    ).length;
    unmount();
    expect(
      mockPolylineSetMap.mock.calls.filter(([mapValue]) => mapValue === null).length,
    ).toBeGreaterThan(disposeCallsBeforeUnmount);
  });
});
