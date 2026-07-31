import React from "react";
import { fireEvent, render, screen } from "@testing-library/react";
import { vi } from "vitest";
import { defaultScenario } from "../constants/scenario";
import { ScenarioControls } from "./ScenarioControls";

describe("ScenarioControls", () => {
  test("T-26 slider ranges, readouts, reset, and defaults 17 / 1 / 56", () => {
    const setScenario = vi.fn();
    const onReset = vi.fn();

    const { container } = render(
      <ScenarioControls
        scenario={defaultScenario}
        setScenario={setScenario}
        onReset={onReset}
      />,
    );

    const hourSlider = container.querySelector("#scenario-hour") as HTMLInputElement;
    const weatherSlider = container.querySelector("#scenario-weather") as HTMLInputElement;
    const congestionSlider = container.querySelector("#scenario-congestion") as HTMLInputElement;

    expect(hourSlider).toHaveAttribute("min", "0");
    expect(hourSlider).toHaveAttribute("max", "23");
    expect(hourSlider).toHaveAttribute("step", "1");
    expect(hourSlider.value).toBe("17");

    expect(weatherSlider).toHaveAttribute("min", "0");
    expect(weatherSlider).toHaveAttribute("max", "3");
    expect(weatherSlider).toHaveAttribute("step", "1");
    expect(weatherSlider.value).toBe("1");

    expect(congestionSlider).toHaveAttribute("min", "0");
    expect(congestionSlider).toHaveAttribute("max", "100");
    expect(congestionSlider).toHaveAttribute("step", "1");
    expect(congestionSlider.value).toBe("56");

    expect(screen.getByText("5:00 PM")).toBeInTheDocument();
    expect(screen.getByText("Light rain")).toBeInTheDocument();
    expect(screen.getByText("56%")).toBeInTheDocument();

    fireEvent.change(hourSlider, { target: { value: "9" } });
    expect(setScenario).toHaveBeenCalledWith({ hour: 9, weather: 1, congestion: 56 });

    fireEvent.click(screen.getByRole("button", { name: "Reset" }));
    expect(onReset).toHaveBeenCalledOnce();
  });
});
