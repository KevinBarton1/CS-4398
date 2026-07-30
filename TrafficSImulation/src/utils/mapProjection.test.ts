import { describe, expect, it } from "vitest";
import { polylineToPath, projectLatLng } from "./mapProjection";

describe("mapProjection", () => {
  const view = { center_lat: 30.2324, center_lng: -97.7048, zoom: 12 };

  it("projects center point to middle of viewport", () => {
    const point = projectLatLng({ lat: 30.2324, lng: -97.7048 }, view, 800, 600);
    expect(point.x).toBeCloseTo(400, 0);
    expect(point.y).toBeCloseTo(300, 0);
  });

  it("builds an SVG path from polyline points", () => {
    const path = polylineToPath(
      [
        { lat: 30.2672, lng: -97.7431 },
        { lat: 30.1975, lng: -97.6664 },
      ],
      view,
      800,
      600
    );
    expect(path.startsWith("M")).toBe(true);
    expect(path).toContain("L");
  });
});
