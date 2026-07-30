import { trafficSegmentColor, GOOGLE_TRAFFIC_COLORS, applySliderCorrection } from "./trafficSegmentColor";

describe("trafficSegmentColor", () => {
  it("keeps NORMAL segments on Google blue", () => {
    expect(trafficSegmentColor("NORMAL", 90, 3)).toBe(GOOGLE_TRAFFIC_COLORS.NORMAL);
  });

  it("corrects SLOW segments with sliders", () => {
    const base = trafficSegmentColor("SLOW", 0, 0);
    const stressed = trafficSegmentColor("SLOW", 90, 3);
    expect(base).toBe(GOOGLE_TRAFFIC_COLORS.SLOW);
    expect(stressed).not.toBe(base);
  });

  it("corrects TRAFFIC_JAM segments with sliders", () => {
    const calm = applySliderCorrection(GOOGLE_TRAFFIC_COLORS.TRAFFIC_JAM, 10, 0);
    const stressed = applySliderCorrection(GOOGLE_TRAFFIC_COLORS.TRAFFIC_JAM, 90, 3);
    expect(stressed).not.toBe(calm);
  });
});
