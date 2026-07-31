import React from "react";
import { render, screen } from "@testing-library/react";
import { PriceSummary } from "./PriceSummary";
import { makeRoute } from "../test/fixtures";

describe("PriceSummary", () => {
  test("T-38 renders all five factors, formatting, disclaimer, data_source, and no recomputation", () => {
    const route = makeRoute({
      estimated_price: 24.5,
      price_factors: {
        route_subtotal: 19.3,
        traffic_multiplier: 1.08,
        weather_multiplier: 1.03,
        time_multiplier: 1.0,
        unrounded_total: 21.48,
      },
      data_source: "Google Routes with departure-hour traffic",
    });

    render(<PriceSummary route={route} />);

    expect(screen.getByText("$24.50")).toBeInTheDocument();
    expect(screen.getByText("$19.30")).toBeInTheDocument();
    expect(screen.getByText("x1.08")).toBeInTheDocument();
    expect(screen.getByText("x1.03")).toBeInTheDocument();
    expect(screen.getByText("x1.00")).toBeInTheDocument();
    expect(screen.getByText("$21.48")).toBeInTheDocument();
    expect(screen.getByText("Route subtotal")).toBeInTheDocument();
    expect(screen.getByText("Traffic")).toBeInTheDocument();
    expect(screen.getByText("Weather")).toBeInTheDocument();
    expect(screen.getByText("Time of day")).toBeInTheDocument();
    expect(screen.getByText("Before rounding")).toBeInTheDocument();
    expect(
      screen.getByText("Illustrative estimate only. Not an official Uber or Lyft fare."),
    ).toBeInTheDocument();
    expect(
      screen.getByText("Google Routes with departure-hour traffic"),
    ).toBeInTheDocument();
    expect(screen.queryByText("$21.49")).not.toBeInTheDocument();
  });
});
