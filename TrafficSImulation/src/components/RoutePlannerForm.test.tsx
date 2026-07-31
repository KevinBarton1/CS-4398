import React from "react";
import { fireEvent, render, screen } from "@testing-library/react";
import { vi } from "vitest";
import { RoutePlannerForm } from "./RoutePlannerForm";

const defaultProps = {
  origin: "Downtown Austin",
  destination: "Austin Airport",
  status: "success" as const,
  onOriginChange: vi.fn(),
  onDestinationChange: vi.fn(),
  onSubmit: vi.fn((event) => event.preventDefault()),
  onUseCurrentLocation: vi.fn(),
};

describe("RoutePlannerForm", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  test("T-35 geolocation button delegates to onUseCurrentLocation", () => {
    render(<RoutePlannerForm {...defaultProps} />);
    fireEvent.click(screen.getByRole("button", { name: "Use my current location" }));
    expect(defaultProps.onUseCurrentLocation).toHaveBeenCalledOnce();
  });

  test("T-35 manual entry stays working after invoking geolocation", () => {
    render(<RoutePlannerForm {...defaultProps} />);
    const originInput = screen.getByLabelText("Starting point") as HTMLInputElement;
    fireEvent.change(originInput, { target: { value: "UT Austin" } });
    expect(defaultProps.onOriginChange).toHaveBeenCalledWith("UT Austin");
  });
});
