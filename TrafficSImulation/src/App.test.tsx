import React from "react";
import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { App } from "./App";
import { makePlan } from "./test/fixtures";
import type { PlanResult } from "./types";

vi.mock("@vis.gl/react-google-maps", () => import("./test/googleMapsMock.tsx"));

const simulatedResult = makePlan();

const realtimeResult: PlanResult = {
  ...simulatedResult,
  mode: "realtime",
  scenario_applied: false,
  scenario: { hour: 17, weather: 0, congestion: 0 },
  routes: [simulatedResult.routes[0]],
  notice:
    "Real-Time mode: route, distance, and travel time come from Google Maps traffic-aware routing for the current departure time.",
};

const fetchMock = vi.fn();

beforeEach(() => {
  fetchMock.mockReset();
  vi.stubGlobal("fetch", fetchMock);
  fetchMock.mockImplementation(async (input: RequestInfo, init?: RequestInit) => {
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
  });
});

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("App composition", () => {
  it("T-25: initial load renders the default plan, notice, and route list", async () => {
    render(<App />);

    expect(screen.getByLabelText("Starting point")).toHaveValue("Downtown Austin");
    expect(screen.getByLabelText("Destination")).toHaveValue("Austin Airport");
    expect(screen.getByRole("button", { name: "Simulated" })).toHaveAttribute("aria-pressed", "true");
    expect(screen.getByRole("button", { name: "Real-Time" })).toHaveAttribute("aria-pressed", "false");

    await waitFor(() => {
      expect(screen.getByText(simulatedResult.notice)).toBeInTheDocument();
    });

    expect(screen.getByRole("heading", { name: "Fastest" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Balanced/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Low traffic/i })).toBeInTheDocument();
    expect(screen.getByText("Recommended")).toBeInTheDocument();
    expect(screen.getByRole("region", { name: "Route map" })).toBeInTheDocument();
    await waitFor(() => expect(screen.getByTestId("google-map")).toHaveClass("route-map"));
    expect(screen.getByText(/Fastest route, 21\.7 min, 6\.9 mi/)).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Shape conditions" })).toBeInTheDocument();
    expect(screen.getByText("Riverside Dr")).toBeInTheDocument();
  });

  it("T-28: Real-Time switch hides scenario controls and renders one route", async () => {
    render(<App />);
    await waitFor(() => expect(screen.getByRole("heading", { name: "Fastest" })).toBeInTheDocument());

    fireEvent.click(screen.getByRole("button", { name: "Real-Time" }));

    await waitFor(() => expect(screen.getByRole("button", { name: "Real-Time" })).toHaveClass("active"));
    await waitFor(() => expect(screen.queryByRole("button", { name: /Balanced/i })).not.toBeInTheDocument(), {
      timeout: 3000,
    });
    await waitFor(() => expect(screen.queryByRole("heading", { name: "Shape conditions" })).not.toBeInTheDocument(), {
      timeout: 3000,
    });
    expect(screen.queryByRole("slider")).not.toBeInTheDocument();
    expect(
      screen.getByText(
        "Real-Time mode plans for the current departure time using live Google Maps traffic. Scenario controls apply in Simulated mode.",
      ),
    ).toBeInTheDocument();
    expect(screen.getByTestId("google-map")).toBeInTheDocument();
  });

  it("T-29: selection updates analysis and reconciles across a re-plan", async () => {
    const balancedPlan = makePlan();
    const replanWithoutBalanced = makePlan({
      routes: [balancedPlan.routes[0], balancedPlan.routes[2]],
      recommended_route_id: "route-3",
    });

    fetchMock.mockImplementation(async (input: RequestInfo, init?: RequestInit) => {
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
      if (body.congestion === 70) {
        return { ok: true, json: async () => replanWithoutBalanced };
      }
      return { ok: true, json: async () => balancedPlan };
    });

    render(<App />);
    await waitFor(() => expect(screen.getByRole("button", { name: /Balanced/i })).toBeInTheDocument());

    fireEvent.click(screen.getByRole("button", { name: /Balanced/i }));
    const analysis = () => screen.getByRole("complementary", { name: "Route analysis" });
    await waitFor(() => {
      expect(within(analysis()).getByRole("heading", { name: "Balanced" })).toBeInTheDocument();
    });
    expect(screen.getByText("Congress Ave")).toBeInTheDocument();
    expect(screen.getAllByText("$28.40").length).toBeGreaterThanOrEqual(1);

    fireEvent.change(screen.getByRole("slider", { name: /Congestion/i }), { target: { value: "60" } });
    await waitFor(
      () => {
        expect(within(analysis()).getByRole("heading", { name: "Balanced" })).toBeInTheDocument();
      },
      { timeout: 3000 },
    );

    fireEvent.change(screen.getByRole("slider", { name: /Congestion/i }), { target: { value: "70" } });
    await waitFor(
      () => {
        expect(within(analysis()).getByRole("heading", { name: "Low traffic" })).toBeInTheDocument();
      },
      { timeout: 3000 },
    );
  });

  it("T-36: keyboard traversal of the mode switch and route cards", async () => {
    render(<App />);

    expect(screen.getByRole("link", { name: "Skip to main content" })).toHaveAttribute(
      "href",
      "#main-content",
    );
    expect(screen.getByRole("banner")).toBeInTheDocument();
    expect(screen.getByRole("main")).toBeInTheDocument();
    expect(screen.getAllByRole("complementary")).toHaveLength(2);
    expect(screen.getByRole("complementary", { name: "Trip planning" })).toBeInTheDocument();
    expect(screen.getByRole("complementary", { name: "Route analysis" })).toBeInTheDocument();
    expect(screen.getByRole("group", { name: "Planning mode" })).toBeInTheDocument();

    await waitFor(() => expect(screen.getByRole("heading", { name: "Fastest" })).toBeInTheDocument());

    const fastestCard = screen.getByRole("button", { name: /Fastest/i });
    expect(fastestCard).toHaveAccessibleName(/21\.7 min/i);
    expect(fastestCard).toHaveAccessibleName(/6\.9 mi/i);
    expect(fastestCard).toHaveAccessibleName(/\$31\.11/i);

    const realtimeButton = screen.getByRole("button", { name: "Real-Time" });
    realtimeButton.focus();
    fireEvent.keyDown(realtimeButton, { key: "Enter", code: "Enter" });
    fireEvent.click(realtimeButton);
    await waitFor(() => expect(realtimeButton).toHaveAttribute("aria-pressed", "true"));
    expect(document.activeElement).toBe(realtimeButton);
    await waitFor(() => expect(screen.queryByRole("button", { name: /Fastest/i })).not.toBeInTheDocument(), {
      timeout: 3000,
    });

    fireEvent.click(screen.getByRole("button", { name: "Simulated" }));
    await waitFor(() => expect(screen.getByRole("button", { name: /Balanced/i })).toBeInTheDocument(), {
      timeout: 3000,
    });

    const balancedCard = screen.getByRole("button", { name: /Balanced/i });
    balancedCard.focus();
    fireEvent.keyDown(balancedCard, { key: " ", code: "Space" });
    fireEvent.click(balancedCard);
    await waitFor(() => {
      expect(balancedCard).toHaveAttribute("aria-pressed", "true");
    });
    expect(document.activeElement).toBe(balancedCard);
  });

  it("T-37: live-region announcements for loading and error", async () => {
    fetchMock.mockImplementation(async (input: RequestInfo) => {
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
      return {
        ok: false,
        status: 400,
        json: async () => ({
          detail: "Could not resolve the starting location.",
          code: "invalid_location",
        }),
      };
    });

    render(<App />);

    const statusRegion = screen.getByLabelText("Request status");
    expect(statusRegion).toHaveAttribute("aria-live", "polite");
    expect(statusRegion).toHaveAttribute("aria-atomic", "true");
    await waitFor(() => expect(statusRegion).toHaveTextContent("Planning"));
    await waitFor(() => expect(statusRegion).toHaveTextContent("Problem"));
    expect(screen.getByRole("alert")).toHaveTextContent("Could not resolve the starting location.");
  });

  it("T-37: announces plan ready after a successful request", async () => {
    render(<App />);

    const statusRegion = screen.getByLabelText("Request status");
    await waitFor(() => expect(statusRegion).toHaveTextContent("Planning"));
    await waitFor(() => expect(statusRegion).toHaveTextContent("Plan ready"));
  });
});
