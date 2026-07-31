import { test, expect } from "@playwright/test";

const planFixture = {
  origin: "Downtown Austin",
  destination: "Austin-Bergstrom International Airport",
  mode: "simulated",
  scenario_applied: true,
  scenario: { hour: 17, weather: 1, congestion: 56 },
  weather: {
    label: "Light rain",
    severity: 1,
    time_multiplier: 1.08,
    price_multiplier: 1.03,
    source: "Simulated fallback",
  },
  recommended_route_id: "route-1",
  notice: "Simulated mode notice.",
  map_bounds: {
    north: 30.27,
    south: 30.19,
    east: -97.66,
    west: -97.75,
  },
  routes: [
    {
      id: "route-1",
      name: "Fastest",
      objective: "Minimum adjusted travel time",
      color: "#55d6be",
      distance_miles: 11.4,
      base_eta_minutes: 24.4,
      adjusted_eta_minutes: 31.9,
      estimated_price: 30.56,
      congestion_score: 56,
      normalized_score: 0,
      data_source: "Google Routes with departure-hour traffic",
      polyline: [
        { lat: 30.2672, lng: -97.7431 },
        { lat: 30.1975, lng: -97.6664 },
      ],
      traffic_intervals: [{ start_index: 0, end_index: 1, speed: "NORMAL" }],
      segments: [],
      price_factors: {
        route_subtotal: 19.3,
        traffic_multiplier: 1.08,
        weather_multiplier: 1.03,
        time_multiplier: 1.0,
        unrounded_total: 30.56,
      },
      bounds: {
        north: 30.27,
        south: 30.19,
        east: -97.66,
        west: -97.75,
      },
    },
    {
      id: "route-2",
      name: "Balanced",
      objective: "Weighted time, distance, and congestion",
      color: "#ffb35c",
      distance_miles: 12.4,
      base_eta_minutes: 24.4,
      adjusted_eta_minutes: 30.8,
      estimated_price: 31.13,
      congestion_score: 47,
      normalized_score: 0.2,
      data_source: "Google Routes with departure-hour traffic",
      polyline: [
        { lat: 30.2672, lng: -97.7431 },
        { lat: 30.22, lng: -97.7 },
        { lat: 30.1975, lng: -97.6664 },
      ],
      traffic_intervals: [{ start_index: 0, end_index: 2, speed: "NORMAL" }],
      segments: [],
      price_factors: {
        route_subtotal: 19.8,
        traffic_multiplier: 1.05,
        weather_multiplier: 1.03,
        time_multiplier: 1.0,
        unrounded_total: 31.13,
      },
      bounds: {
        north: 30.27,
        south: 30.19,
        east: -97.66,
        west: -97.75,
      },
    },
  ],
};

test("T-44: plan, select route, and switch mode", async ({ page }) => {
  let mode = "simulated";

  await page.route(/\/api\/(plan|map\/config)/, async (route) => {
    const url = route.request().url();
    if (url.includes("/api/map/config")) {
      await route.fulfill({
        status: 503,
        contentType: "application/json",
        body: JSON.stringify({
          detail: "Map configuration is unavailable.",
          code: "map_config_unavailable",
          fields: null,
        }),
      });
      return;
    }

    const body = JSON.parse(route.request().postData() ?? "{}");
    mode = body.mode ?? mode;
    const payload =
      mode === "realtime"
        ? {
            ...planFixture,
            mode: "realtime",
            scenario_applied: false,
            scenario: { hour: 17, weather: 0, congestion: 0 },
            recommended_route_id: "route-1",
            routes: [planFixture.routes[0]],
            notice:
              "Real-Time mode: route, distance, and travel time come from Google Maps traffic-aware routing for the current departure time.",
          }
        : planFixture;

    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify(payload),
    });
  });

  await page.goto("/");

  await expect(page.getByRole("button", { name: /Fastest/i })).toBeVisible({
    timeout: 15_000,
  });
  await expect(page.getByRole("button", { name: /Balanced/i })).toBeVisible();

  await page.getByRole("button", { name: /Balanced/i }).click();
  await expect(page.getByRole("button", { name: /Balanced/i })).toHaveAttribute(
    "aria-pressed",
    "true",
  );

  await page.getByRole("button", { name: "Real-Time" }).click();
  await expect(page.getByRole("button", { name: "Real-Time" })).toHaveClass(/active/);
  await expect(page.getByRole("button", { name: /Balanced/i })).not.toBeVisible({
    timeout: 15_000,
  });
  await expect(
    page.getByText(/Real-Time mode plans for the current departure time/i),
  ).toBeVisible({ timeout: 15_000 });
});
