import { renderHook, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { resetMapConfigCache, useMapConfig } from "./useMapConfig";

const fetchMock = vi.fn();

const mapConfigBody = {
  maps_browser_api_key: "browser-key",
  map_id: null,
  default_center: { lat: 30.2672, lng: -97.7431 },
  default_zoom: 12,
  color_scheme: "DARK",
  libraries: ["core", "maps"],
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

describe("useMapConfig", () => {
  it("loads map configuration successfully", async () => {
    fetchMock.mockResolvedValue({
      ok: true,
      json: async () => mapConfigBody,
    });

    const { result } = renderHook(() => useMapConfig());

    await waitFor(() => expect(result.current.status).toBe("success"));
    expect(result.current.config).toMatchObject({
      maps_browser_api_key: "browser-key",
      color_scheme: "DARK",
    });
    expect(result.current.error).toBeNull();
    expect(fetchMock).toHaveBeenCalledTimes(1);
    expect(String(fetchMock.mock.calls[0][0])).toContain("/api/map/config");
  });

  it("contains maps_not_configured failures locally", async () => {
    fetchMock.mockResolvedValue({
      ok: false,
      status: 503,
      json: async () => ({
        detail: "Google Maps browser credential is not configured.",
        code: "maps_not_configured",
      }),
    });

    const { result } = renderHook(() => useMapConfig());

    await waitFor(() => expect(result.current.status).toBe("error"));
    expect(result.current.config).toBeNull();
    expect(result.current.error?.code).toBe("maps_not_configured");
  });

  it("reuses the session cache on subsequent hook mounts", async () => {
    fetchMock.mockResolvedValue({
      ok: true,
      json: async () => mapConfigBody,
    });

    const first = renderHook(() => useMapConfig());
    await waitFor(() => expect(first.result.current.status).toBe("success"));
    first.unmount();

    const second = renderHook(() => useMapConfig());
    await waitFor(() => expect(second.result.current.status).toBe("success"));
    expect(second.result.current.config?.maps_browser_api_key).toBe("browser-key");
    expect(fetchMock).toHaveBeenCalledTimes(1);
  });
});
