import { describe, expect, it } from "vitest";
import { computeMapViewForPolyline, polylineToPath, projectLatLng } from "./mapProjection";

describe("mapProjection", () => {
  const view = { center_lat: 30.2324, center_lng: -97.7048, zoom: 12 };
  const samplePolyline = [
    { lat: 30.2672, lng: -97.7431 },
    { lat: 30.2500, lng: -97.7200 },
    { lat: 30.2300, lng: -97.6900 },
    { lat: 30.1975, lng: -97.6664 },
  ];

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

  it("picks a tighter zoom when the viewport is larger", () => {
    const small = computeMapViewForPolyline(samplePolyline, 400, 300);
    const large = computeMapViewForPolyline(samplePolyline, 1200, 900);
    expect(small?.zoom).toBeDefined();
    expect(large?.zoom).toBeDefined();
    expect(large!.zoom).toBeGreaterThanOrEqual(small!.zoom);
  });

  it("keeps every polyline point inside the viewport", () => {
    const fitted = computeMapViewForPolyline(samplePolyline, 800, 600);
    expect(fitted).not.toBeNull();
    for (const point of samplePolyline) {
      const { x, y } = projectLatLng(point, fitted!, 800, 600);
      expect(x).toBeGreaterThanOrEqual(16);
      expect(x).toBeLessThanOrEqual(784);
      expect(y).toBeGreaterThanOrEqual(16);
      expect(y).toBeLessThanOrEqual(584);
    }
  });
});
