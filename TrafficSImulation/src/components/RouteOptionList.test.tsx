import React, { useState } from "react";
import { fireEvent, render, screen } from "@testing-library/react";
import { vi } from "vitest";
import { AnalysisPanel } from "./AnalysisPanel";
import { RouteOptionList } from "./RouteOptionList";
import { defaultScenario } from "../constants/scenario";
import { makePlan } from "../test/fixtures";

function SelectionHarness() {
  const plan = makePlan();
  const [selectedRouteId, setSelectedRouteId] = useState(plan.recommended_route_id);
  const selectedRoute = plan.routes.find((route) => route.id === selectedRouteId);

  return (
    <>
      <RouteOptionList
        routes={plan.routes}
        selectedRouteId={selectedRouteId}
        recommendedRouteId={plan.recommended_route_id}
        comparisonEnabled={plan.scenario_applied}
        onSelect={setSelectedRouteId}
      />
      <AnalysisPanel
        route={selectedRoute}
        origin={plan.origin}
        destination={plan.destination}
        weather={plan.weather}
        notice={plan.notice}
        recommendedRouteId={plan.recommended_route_id}
        mode={plan.mode}
        scenarioApplied={plan.scenario_applied}
        scenario={plan.scenario}
        onScenarioChange={vi.fn()}
        onScenarioReset={vi.fn()}
      />
    </>
  );
}

describe("RouteOptionList", () => {
  test("marks the recommended route by id and supports keyboard selection", () => {
    const plan = makePlan();
    const onSelect = vi.fn();

    render(
      <RouteOptionList
        routes={plan.routes}
        selectedRouteId="route-1"
        recommendedRouteId="route-1"
        comparisonEnabled
        onSelect={onSelect}
      />,
    );

    expect(screen.getAllByText("Recommended")).toHaveLength(1);
    expect(screen.getByRole("button", { name: /Fastest/i })).toHaveAttribute(
      "aria-pressed",
      "true",
    );

    const balancedCard = screen.getByRole("button", { name: /Balanced/i });
    fireEvent.click(balancedCard);
    expect(onSelect).toHaveBeenCalledWith("route-2");
  });

  test("selection wiring updates the analysis panel inputs", () => {
    render(<SelectionHarness />);

    expect(screen.getByRole("heading", { name: "Fastest" })).toBeInTheDocument();
    expect(screen.getAllByText("$31.11").length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText("Riverside Dr")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: /Balanced/i }));

    expect(screen.getByRole("heading", { name: "Balanced" })).toBeInTheDocument();
    expect(screen.getAllByText("$28.40").length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText("Congress Ave")).toBeInTheDocument();
    expect(screen.queryByText("Riverside Dr")).not.toBeInTheDocument();
  });

  test("real-time mode renders one static card without a recommended badge", () => {
    const plan = makePlan({
      scenario_applied: false,
      mode: "realtime",
      routes: [makePlan().routes[0]],
    });

    render(
      <RouteOptionList
        routes={plan.routes}
        selectedRouteId={plan.routes[0].id}
        recommendedRouteId={plan.recommended_route_id}
        comparisonEnabled={false}
        onSelect={vi.fn()}
      />,
    );

    expect(screen.queryByText("Recommended")).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /Fastest/i })).not.toBeInTheDocument();
    expect(
      screen.getByText(
        "Real-Time mode returns the single route Google recommends for the current departure time. Switch to Simulated mode to compare up to three alternatives.",
      ),
    ).toBeInTheDocument();
  });
});
