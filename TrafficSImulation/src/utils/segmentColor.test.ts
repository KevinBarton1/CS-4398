import { segmentColor } from "./segmentColor";

describe("segmentColor", () => {
  it("returns greenish tones for low severity", () => {
    const color = segmentColor(0, 1, 0);
    expect(color).toMatch(/^rgb\(\d+, \d+, \d+\)$/);
    expect(color).toBe("rgb(85, 214, 190)");
  });

  it("returns reddish tones for high severity", () => {
    expect(segmentColor(1, 2, 3)).toBe("rgb(232, 93, 76)");
  });

  it("returns warmer tones as severity increases", () => {
    const low = segmentColor(0.1, 1, 0);
    const high = segmentColor(0.9, 1.8, 3);
    expect(low).not.toBe(high);
    expect(high.startsWith("rgb(")).toBe(true);
  });
});
