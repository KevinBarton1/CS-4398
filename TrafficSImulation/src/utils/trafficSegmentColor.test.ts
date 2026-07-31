import { describe, expect, it } from "vitest";
import {
  GOOGLE_TRAFFIC_COLORS,
  applySliderCorrection,
  trafficSegmentColor,
} from "./trafficSegmentColor";

describe("trafficSegmentColor", () => {
  it("T-33: keeps NORMAL on Google blue at every scenario setting", () => {
    expect(trafficSegmentColor("NORMAL", 0, 0)).toBe("#4285F4");
    expect(trafficSegmentColor("NORMAL", 100, 3)).toBe("#4285F4");
  });

  it("T-33: returns exact Google base colors when scenario inputs are zero", () => {
    expect(trafficSegmentColor("NORMAL", 0, 0)).toBe(GOOGLE_TRAFFIC_COLORS.NORMAL);
    expect(trafficSegmentColor("SLOW", 0, 0)).toBe(GOOGLE_TRAFFIC_COLORS.SLOW);
    expect(trafficSegmentColor("TRAFFIC_JAM", 0, 0)).toBe(GOOGLE_TRAFFIC_COLORS.TRAFFIC_JAM);
    expect(trafficSegmentColor("SPEED_UNSPECIFIED", 0, 0)).toBe(
      GOOGLE_TRAFFIC_COLORS.SPEED_UNSPECIFIED,
    );
  });

  it("T-33: tints non-NORMAL categories when scenario inputs are non-zero", () => {
    const slowBase = trafficSegmentColor("SLOW", 0, 0);
    const slowTinted = trafficSegmentColor("SLOW", 90, 3);
    expect(slowTinted).not.toBe(slowBase);

    const jamCalm = applySliderCorrection(GOOGLE_TRAFFIC_COLORS.TRAFFIC_JAM, 10, 0);
    const jamStressed = applySliderCorrection(GOOGLE_TRAFFIC_COLORS.TRAFFIC_JAM, 90, 3);
    expect(jamStressed).not.toBe(jamCalm);
  });
});
