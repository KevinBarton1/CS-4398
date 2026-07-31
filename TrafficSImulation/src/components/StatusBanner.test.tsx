import React from "react";
import { act, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { CONNECTIVITY_DETAIL } from "../api/client";
import {
  CONNECTIVITY_GUIDANCE,
  EMPTY_MESSAGE,
  LOADING_MESSAGE,
  StatusBanner,
  getErrorGuidance,
  shouldOfferRetry,
} from "./StatusBanner";
import type { ApiError, ApiErrorCode } from "../types";
import { SCENARIO_DEBOUNCE_MS } from "../constants/scenario";
import { makePlan } from "../test/fixtures";
import { useRoutePlan } from "../hooks/useRoutePlan";
import { renderHook, waitFor } from "@testing-library/react";

const DOCUMENTED_CODES: Array<{
  code: Exclude<ApiErrorCode, null>;
  detail: string;
  guidance: string;
  retry: boolean;
}> = [
  {
    code: "validation_error",
    detail: "Request validation failed.",
    guidance: "Correct the highlighted fields and plan again.",
    retry: false,
  },
  {
    code: "invalid_location",
    detail: "Could not resolve the starting point.",
    guidance:
      "Try a nearby landmark, a full street address, or one of the suggested Austin places.",
    retry: false,
  },
  {
    code: "same_origin_destination",
    detail: "Origin and destination are the same place.",
    guidance: "Choose a destination that differs from the starting point.",
    retry: false,
  },
  {
    code: "no_route_found",
    detail: "No driving route connects these places.",
    guidance: "No driving route connects these two places. Try a different destination.",
    retry: false,
  },
  {
    code: "maps_not_configured",
    detail: "Google Maps credential is not configured.",
    guidance:
      "The server is missing its Google Maps credential. An administrator has to configure it before planning works.",
    retry: true,
  },
  {
    code: "upstream_unavailable",
    detail: "Google Maps did not answer.",
    guidance:
      "Google Maps did not answer successfully. Your inputs are unchanged; try again in a moment.",
    retry: true,
  },
  {
    code: "upstream_timeout",
    detail: "Google Maps timed out.",
    guidance:
      "Google Maps took too long to answer. Try again, and move the scenario sliders in fewer, larger steps if this repeats.",
    retry: true,
  },
];

function makeError(code: ApiErrorCode, overrides: Partial<ApiError> = {}): ApiError {
  return {
    detail: overrides.detail ?? "Request failed.",
    code,
    fields: overrides.fields ?? null,
  };
}

describe("StatusBanner", () => {
  it("renders loading and empty states with status role", () => {
    const { rerender } = render(<StatusBanner variant="loading" region="planner" />);
    expect(screen.getByRole("status")).toHaveTextContent(LOADING_MESSAGE);

    rerender(<StatusBanner variant="empty" region="planner" onRetry={vi.fn()} />);
    expect(screen.getByRole("status")).toHaveTextContent(EMPTY_MESSAGE);
    expect(screen.getByRole("button", { name: "Retry" })).toBeInTheDocument();
  });

  it.each(DOCUMENTED_CODES)(
    "T-30: renders $code with detail, guidance, and retry=$retry",
    ({ code, detail, guidance, retry }) => {
      const onRetry = vi.fn();
      render(
        <StatusBanner
          variant="error"
          error={makeError(code, { detail })}
          region="planner"
          onRetry={onRetry}
        />,
      );

      expect(screen.getByRole("alert")).toHaveTextContent(detail);
      expect(screen.getByText(guidance)).toBeInTheDocument();
      expect(getErrorGuidance(code)).toBe(guidance);
      expect(shouldOfferRetry(code)).toBe(retry);

      const retryButton = screen.queryByRole("button", { name: "Retry" });
      if (retry) {
        expect(retryButton).toBeInTheDocument();
      } else {
        expect(retryButton).not.toBeInTheDocument();
      }
    },
  );

  it("T-30: renders connectivity fallback for code null", () => {
    render(
      <StatusBanner
        variant="error"
        error={makeError(null, { detail: CONNECTIVITY_DETAIL })}
        region="planner"
        onRetry={vi.fn()}
      />,
    );

    expect(screen.getByRole("alert")).toHaveTextContent(CONNECTIVITY_DETAIL);
    expect(screen.getByRole("button", { name: "Retry" })).toBeInTheDocument();
  });

  it("T-30: lists validation_error fields", () => {
    render(
      <StatusBanner
        variant="error"
        error={{
          detail: "Validation failed.",
          code: "validation_error",
          fields: [
            { field: "origin", message: "Too short." },
            { field: "hour", message: "Out of range." },
          ],
        }}
        region="planner"
      />,
    );

    const items = screen.getAllByRole("listitem");
    expect(items[0]).toHaveTextContent("origin");
    expect(items[0]).toHaveTextContent("Too short.");
    expect(items[1]).toHaveTextContent("hour");
    expect(items[1]).toHaveTextContent("Out of range.");
    expect(screen.queryByRole("button", { name: "Retry" })).not.toBeInTheDocument();
  });

  it("T-30: shows generic guidance for an unknown code while preserving detail", () => {
    render(
      <StatusBanner
        variant="error"
        error={{
          detail: "Unexpected server failure.",
          code: "future_code" as ApiErrorCode,
          fields: null,
        }}
        region="planner"
      />,
    );

    expect(screen.getByRole("alert")).toHaveTextContent("Unexpected server failure.");
    expect(
      screen.getByText("Review the message above and try again, or change your trip details."),
    ).toBeInTheDocument();
  });
});

describe("StatusBanner plan preservation", () => {
  const fetchMock = vi.fn();

  beforeEach(() => {
    fetchMock.mockReset();
    vi.stubGlobal("fetch", fetchMock);
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    vi.useRealTimers();
  });

  it("T-30: preserves inputs and the previous plan on a failed re-plan", async () => {
    fetchMock
      .mockResolvedValueOnce({ ok: true, json: async () => makePlan() })
      .mockResolvedValueOnce({
        ok: false,
        status: 502,
        json: async () => ({
          detail: "Google Maps did not answer.",
          code: "upstream_unavailable",
        }),
      });

    const { result } = renderHook(() => useRoutePlan());
    await waitFor(() => expect(result.current.status).toBe("success"));
    const previousPlan = result.current.plan;

    act(() => {
      result.current.setScenario({ hour: 20, weather: 2, congestion: 80 });
    });

    await act(async () => {
      await new Promise((resolve) => setTimeout(resolve, SCENARIO_DEBOUNCE_MS + 50));
    });

    expect(result.current.status).toBe("error");
    expect(result.current.plan).toBe(previousPlan);
    expect(result.current.origin).toBe("Downtown Austin");
    expect(result.current.destination).toBe("Austin Airport");
    expect(result.current.mode).toBe("simulated");
    expect(result.current.scenario).toEqual({ hour: 20, weather: 2, congestion: 80 });
    expect(result.current.selectedRouteId).toBeDefined();
    expect(result.current.toastFromError?.detail).toBe("Google Maps did not answer.");
  });
});
