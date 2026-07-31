import { act, renderHook, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { SCENARIO_DEBOUNCE_MS } from "../constants/scenario";
import type { PlanResult, RouteOption } from "../types";
import { useRoutePlan } from "./useRoutePlan";

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
  data_source: "Google Routes with departure-hour traffic",
  polyline: [
    { lat: 30.2672, lng: -97.7431 },
    { lat: 30.1975, lng: -97.6664 },
  ],
  traffic_intervals: [{ start_index: 0, end_index: 2, speed: "NORMAL" }],
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

function makePlan(overrides: Partial<PlanResult> = {}): PlanResult {
  return {
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
    routes: [
      baseRoute,
      { ...baseRoute, id: "route-2", name: "Balanced" },
      { ...baseRoute, id: "route-3", name: "Low traffic" },
    ],
    ...overrides,
  };
}

const fetchMock = vi.fn();

beforeEach(() => {
  fetchMock.mockReset();
  vi.stubGlobal("fetch", fetchMock);
});

afterEach(() => {
  vi.unstubAllGlobals();
  vi.useRealTimers();
});

function mockPlanResponse(plan: PlanResult) {
  return {
    ok: true,
    json: async () => plan,
  };
}

function mockPlanError(detail: string, code: string, status = 400) {
  return {
    ok: false,
    status,
    json: async () => ({ detail, code }),
  };
}

async function waitForSuccess(result: { current: ReturnType<typeof useRoutePlan> }) {
  await waitFor(() => expect(result.current.status).toBe("success"));
}

describe("useRoutePlan", () => {
  it("T-27: coalesces rapid scenario changes into one debounced request", async () => {
    vi.useFakeTimers();
    fetchMock.mockResolvedValue(mockPlanResponse(makePlan()));

    const { result } = renderHook(() => useRoutePlan());

    await act(async () => {
      await Promise.resolve();
    });
    expect(result.current.status).toBe("success");
    expect(fetchMock).toHaveBeenCalledTimes(1);

    act(() => {
      result.current.setScenario({ hour: 8, weather: 1, congestion: 56 });
      result.current.setScenario({ hour: 9, weather: 2, congestion: 60 });
      result.current.setScenario({ hour: 10, weather: 2, congestion: 70 });
    });

    expect(fetchMock).toHaveBeenCalledTimes(1);

    await act(async () => {
      await vi.advanceTimersByTimeAsync(SCENARIO_DEBOUNCE_MS);
      await Promise.resolve();
    });

    expect(fetchMock).toHaveBeenCalledTimes(2);

    const lastBody = JSON.parse(String(fetchMock.mock.calls[1][1]?.body));
    expect(lastBody.hour).toBe(10);
    expect(lastBody.weather).toBe(2);
    expect(lastBody.congestion).toBe(70);
  });

  it("T-27: aborts superseded requests and discards late responses", async () => {
    vi.useFakeTimers();

    let resolveSlow: ((value: unknown) => void) | undefined;

    fetchMock
      .mockResolvedValueOnce(mockPlanResponse(makePlan()))
      .mockImplementationOnce((_input: RequestInfo, init?: RequestInit) => {
        return new Promise((resolve, reject) => {
          init?.signal?.addEventListener("abort", () => {
            reject(new DOMException("Aborted", "AbortError"));
          });
          resolveSlow = resolve;
        });
      })
      .mockResolvedValueOnce(mockPlanResponse(makePlan({ recommended_route_id: "route-3" })));

    const { result } = renderHook(() => useRoutePlan());

    await act(async () => {
      await Promise.resolve();
    });
    expect(result.current.plan?.recommended_route_id).toBe("route-1");

    act(() => {
      result.current.setScenario({ hour: 12, weather: 1, congestion: 56 });
    });

    await act(async () => {
      await vi.advanceTimersByTimeAsync(SCENARIO_DEBOUNCE_MS);
      await Promise.resolve();
    });

    act(() => {
      result.current.setScenario({ hour: 13, weather: 1, congestion: 56 });
    });

    await act(async () => {
      await vi.advanceTimersByTimeAsync(SCENARIO_DEBOUNCE_MS);
      await Promise.resolve();
    });

    expect(fetchMock).toHaveBeenCalledTimes(3);
    expect(result.current.plan?.recommended_route_id).toBe("route-3");
    expect(result.current.error).toBeNull();
    expect(result.current.status).toBe("success");

    await act(async () => {
      resolveSlow?.(mockPlanResponse(makePlan({ recommended_route_id: "route-stale" })));
      await Promise.resolve();
    });
    expect(result.current.plan?.recommended_route_id).toBe("route-3");
  });

  it("preserves selection when the route id remains after re-plan", async () => {
    fetchMock
      .mockResolvedValueOnce(mockPlanResponse(makePlan()))
      .mockResolvedValueOnce(mockPlanResponse(makePlan()));

    const { result } = renderHook(() => useRoutePlan());
    await waitForSuccess(result);

    act(() => {
      result.current.selectRoute("route-2");
    });
    expect(result.current.selectedRouteId).toBe("route-2");

    vi.useFakeTimers();
    act(() => {
      result.current.setScenario({ hour: 18, weather: 1, congestion: 56 });
    });

    await act(async () => {
      await vi.advanceTimersByTimeAsync(SCENARIO_DEBOUNCE_MS);
      await Promise.resolve();
    });

    expect(fetchMock).toHaveBeenCalledTimes(2);
    expect(result.current.selectedRouteId).toBe("route-2");
  });

  it("falls back to recommended_route_id when the selection is absent", async () => {
    fetchMock
      .mockResolvedValueOnce(mockPlanResponse(makePlan()))
      .mockResolvedValueOnce(
        mockPlanResponse(
          makePlan({
            recommended_route_id: "route-9",
            routes: [{ ...baseRoute, id: "route-9" }],
          }),
        ),
      );

    const { result } = renderHook(() => useRoutePlan());
    await waitForSuccess(result);

    act(() => {
      result.current.selectRoute("route-2");
    });

    vi.useFakeTimers();
    act(() => {
      result.current.setScenario({ hour: 18, weather: 1, congestion: 56 });
    });

    await act(async () => {
      await vi.advanceTimersByTimeAsync(SCENARIO_DEBOUNCE_MS);
      await Promise.resolve();
    });

    expect(result.current.selectedRouteId).toBe("route-9");
  });

  it("preserves inputs and the previous plan on error", async () => {
    fetchMock
      .mockResolvedValueOnce(mockPlanResponse(makePlan()))
      .mockResolvedValueOnce(
        mockPlanError("Google Maps did not answer.", "upstream_unavailable", 502),
      );

    const { result } = renderHook(() => useRoutePlan());
    await waitForSuccess(result);
    const previousPlan = result.current.plan;

    vi.useFakeTimers();
    act(() => {
      result.current.setScenario({ hour: 20, weather: 2, congestion: 80 });
    });

    await act(async () => {
      await vi.advanceTimersByTimeAsync(SCENARIO_DEBOUNCE_MS);
      await Promise.resolve();
    });

    expect(result.current.status).toBe("error");
    expect(result.current.plan).toBe(previousPlan);
    expect(result.current.origin).toBe("Downtown Austin");
    expect(result.current.destination).toBe("Austin Airport");
    expect(result.current.error?.code).toBe("upstream_unavailable");
  });

  it("does not auto-plan when origin or destination change", async () => {
    fetchMock.mockResolvedValue(mockPlanResponse(makePlan()));

    const { result } = renderHook(() => useRoutePlan());
    await waitForSuccess(result);
    expect(fetchMock).toHaveBeenCalledTimes(1);

    act(() => {
      result.current.setOrigin("UT Austin");
    });

    await act(async () => {
      await new Promise((resolve) => setTimeout(resolve, SCENARIO_DEBOUNCE_MS * 2));
    });

    expect(fetchMock).toHaveBeenCalledTimes(1);

    act(() => {
      result.current.submit();
    });

    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(2));
  });
});
