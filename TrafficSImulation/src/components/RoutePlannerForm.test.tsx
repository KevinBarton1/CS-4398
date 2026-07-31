import React from "react";
import { fireEvent, render, screen } from "@testing-library/react";
import { vi } from "vitest";
import { RoutePlannerForm } from "./RoutePlannerForm";

const defaultProps = {
  origin: "Downtown Austin",
  destination: "Austin Airport",
  setOrigin: vi.fn(),
  setDestination: vi.fn(),
  loading: false,
  onSubmit: vi.fn((event) => event.preventDefault()),
  onNotice: vi.fn(),
};

describe("RoutePlannerForm", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  test("T-35 geolocation grant fills origin with five-decimal lat, lng text", () => {
    const setOrigin = vi.fn();
    const getCurrentPosition = vi.fn((success: PositionCallback) => {
      success({
        coords: { latitude: 30.267204, longitude: -97.743057, accuracy: 0, altitude: null, altitudeAccuracy: null, heading: null, speed: null },
        timestamp: Date.now(),
      });
    });

    vi.stubGlobal("navigator", { geolocation: { getCurrentPosition } });

    render(<RoutePlannerForm {...defaultProps} setOrigin={setOrigin} />);
    fireEvent.click(screen.getByRole("button", { name: "Use my current location" }));

    expect(getCurrentPosition).toHaveBeenCalledOnce();
    expect(setOrigin).toHaveBeenCalledWith("30.26720, -97.74306");
    expect(defaultProps.onNotice).not.toHaveBeenCalled();

    vi.unstubAllGlobals();
  });

  test("T-35 geolocation denial shows a notice and leaves entry working", () => {
    const setOrigin = vi.fn();
    const onNotice = vi.fn();
    const getCurrentPosition = vi.fn((_success: PositionCallback, error: PositionErrorCallback) => {
      error({ code: 1, PERMISSION_DENIED: 1, POSITION_UNAVAILABLE: 2, TIMEOUT: 3, message: "denied" });
    });

    vi.stubGlobal("navigator", { geolocation: { getCurrentPosition } });

    render(
      <RoutePlannerForm
        {...defaultProps}
        origin="Downtown Austin"
        setOrigin={setOrigin}
        onNotice={onNotice}
      />,
    );
    fireEvent.click(screen.getByRole("button", { name: "Use my current location" }));

    expect(onNotice).toHaveBeenCalledWith(
      "Location permission was denied. Enter a starting point manually.",
    );
    expect(setOrigin).not.toHaveBeenCalled();

    const originInput = screen.getByLabelText("Starting point") as HTMLInputElement;
    expect(originInput.value).toBe("Downtown Austin");
    fireEvent.change(originInput, { target: { value: "UT Austin" } });
    expect(setOrigin).toHaveBeenCalledWith("UT Austin");

    vi.unstubAllGlobals();
  });
});
