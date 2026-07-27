import React from "react";
import { render, screen } from "@testing-library/react";
import { vi } from "vitest";
import { App } from "./App";

vi.stubGlobal("fetch", vi.fn(() => new Promise(() => undefined)));

test("renders the required route planning hierarchy", () => {
  render(<App />);
  expect(screen.getByRole("heading", { name: "Find the better drive." })).toBeInTheDocument();
  expect(screen.getByLabelText("Starting point")).toBeInTheDocument();
  expect(screen.getByLabelText("Destination or zone")).toBeInTheDocument();
  expect(screen.getByRole("button", { name: "Simulated" })).toBeInTheDocument();
});
