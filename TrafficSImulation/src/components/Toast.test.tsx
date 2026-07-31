import React from "react";
import { fireEvent, render, screen, act } from "@testing-library/react";
import { describe, expect, it, vi, beforeEach, afterEach } from "vitest";
import { Toast } from "./Toast";

describe("Toast", () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it("keeps the live region mounted and announces informational messages with status role", () => {
    render(
      <Toast
        message={{ detail: "Location permission was denied.", variant: "info" }}
        onDismiss={vi.fn()}
      />,
    );

    expect(screen.getByLabelText("Notifications")).toHaveAttribute("aria-live", "polite");
    expect(screen.getByRole("status")).toHaveTextContent("Location permission was denied.");
  });

  it("uses alert role for failure toasts", () => {
    render(
      <Toast
        message={{
          detail: "Google Maps timed out.",
          guidance: "Try again in a moment.",
          variant: "error",
        }}
        onDismiss={vi.fn()}
      />,
    );

    expect(screen.getByRole("alert")).toHaveTextContent("Google Maps timed out.");
    expect(screen.getByText("Try again in a moment.")).toBeInTheDocument();
  });

  it("dismisses when the close button is clicked", () => {
    const onDismiss = vi.fn();
    render(
      <Toast
        message={{ detail: "Could not read your location.", variant: "info" }}
        onDismiss={onDismiss}
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: "Dismiss notification" }));
    expect(onDismiss).toHaveBeenCalledTimes(1);
  });

  it("auto-dismisses after six seconds", () => {
    const onDismiss = vi.fn();
    render(
      <Toast
        message={{ detail: "Transient notice.", variant: "info" }}
        onDismiss={onDismiss}
      />,
    );

    act(() => {
      vi.advanceTimersByTime(5999);
    });
    expect(onDismiss).not.toHaveBeenCalled();

    act(() => {
      vi.advanceTimersByTime(1);
    });
    expect(onDismiss).toHaveBeenCalledTimes(1);
  });

  it("pauses auto-dismiss while hovered", () => {
    const onDismiss = vi.fn();
    render(
      <Toast
        message={{ detail: "Hover to read.", variant: "info" }}
        onDismiss={onDismiss}
      />,
    );

    fireEvent.mouseEnter(screen.getByRole("status"));

    act(() => {
      vi.advanceTimersByTime(7000);
    });
    expect(onDismiss).not.toHaveBeenCalled();

    fireEvent.mouseLeave(screen.getByRole("status"));

    act(() => {
      vi.advanceTimersByTime(6000);
    });
    expect(onDismiss).toHaveBeenCalledTimes(1);
  });

  it("renders a retry action when provided", () => {
    const onRetry = vi.fn();
    render(
      <Toast
        message={{
          detail: "Google Maps did not answer.",
          guidance: "Try again.",
          variant: "error",
          onRetry,
        }}
        onDismiss={vi.fn()}
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: "Retry" }));
    expect(onRetry).toHaveBeenCalledTimes(1);
  });

  it("leaves an empty live region when there is no message", () => {
    render(<Toast message={null} onDismiss={vi.fn()} />);

    expect(screen.getByLabelText("Notifications")).toBeInTheDocument();
    expect(screen.queryByRole("alert")).not.toBeInTheDocument();
    expect(screen.queryByRole("status")).not.toBeInTheDocument();
  });
});
