import { afterEach, describe, expect, it, vi } from "vitest";
import { defaultScenario } from "../constants/scenario";
import { ApiClientError, getHealth, getMapConfig, postPlan } from "./client";

const planRequest = {
  origin: "Downtown Austin",
  destination: "Austin Airport",
  mode: "simulated" as const,
  ...defaultScenario,
};
const fetchMock = vi.fn();

afterEach(() => {
  fetchMock.mockReset();
});

vi.stubGlobal("fetch", fetchMock);

describe("api client", () => {
  it("parses non-2xx plan responses into ApiError by code", async () => {
    fetchMock.mockResolvedValue({
      ok: false,
      status: 400,
      json: async () => ({
        detail: 'Could not resolve "Mars" to an Austin-area location.',
        code: "invalid_location",
      }),
    });

    await expect(
      postPlan({ ...planRequest, origin: "Mars" }),
    ).rejects.toMatchObject({      apiError: {
        code: "invalid_location",
        detail: 'Could not resolve "Mars" to an Austin-area location.',
      },
    });
  });

  it("includes validation fields when present", async () => {
    fetchMock.mockResolvedValue({
      ok: false,
      status: 422,
      json: async () => ({
        detail: "Request validation failed.",
        code: "validation_error",
        fields: [{ field: "weather", message: "Input should be less than or equal to 3" }],
      }),
    });

    try {
      await postPlan({
        ...planRequest,
        weather: 99,
      });      throw new Error("Expected postPlan to reject");
    } catch (error) {
      expect(error).toBeInstanceOf(ApiClientError);
      const apiError = (error as ApiClientError).apiError;
      expect(apiError.code).toBe("validation_error");
      expect(apiError.fields).toEqual([
        { field: "weather", message: "Input should be less than or equal to 3" },
      ]);
    }
  });

  it("rejects cleanly when aborted", async () => {
    fetchMock.mockImplementation((_input: RequestInfo, init?: RequestInit) => {
      return new Promise((_resolve, reject) => {
        init?.signal?.addEventListener("abort", () => {
          reject(new DOMException("Aborted", "AbortError"));
        });
      });
    });

    const controller = new AbortController();
    const pending = postPlan(planRequest, controller.signal);    controller.abort();

    await expect(pending).rejects.toMatchObject({ name: "AbortError" });
  });

  it("returns typed success bodies", async () => {
    fetchMock.mockResolvedValueOnce({
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
    fetchMock.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        status: "ok",
        service: "TrafficScope",
        version: "2.0",
        google_maps_configured: true,
        google_maps: {
          ok: true,
          message: "Places and Routes reachable.",
          checked_at: "2026-07-30T21:00:00Z",
        },
      }),
    });

    await expect(getMapConfig()).resolves.toMatchObject({
      maps_browser_api_key: "browser-key",
      color_scheme: "DARK",
    });
    await expect(getHealth()).resolves.toMatchObject({
      status: "ok",
      version: "2.0",
    });
  });
});
