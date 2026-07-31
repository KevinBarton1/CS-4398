import { describe, expect, it } from "vitest";
import { contrastRatio } from "./contrast";

describe("contrast", () => {
  it("keeps body and label text at or above 4.5:1 on panel surfaces", () => {
    expect(contrastRatio("#f3f8f6", "#0b1915")).toBeGreaterThanOrEqual(4.5);
    expect(contrastRatio("#d0ded9", "#0b1915")).toBeGreaterThanOrEqual(4.5);
    expect(contrastRatio("#96ada6", "#0b1915")).toBeGreaterThanOrEqual(4.5);
    expect(contrastRatio("#7a938b", "#0b1915")).toBeGreaterThanOrEqual(4.5);
  });

  it("keeps the focus indicator at or above 3:1 on panel backgrounds", () => {
    expect(contrastRatio("#54d8be", "#0b1915")).toBeGreaterThanOrEqual(3);
    expect(contrastRatio("#54d8be", "#081411")).toBeGreaterThanOrEqual(3);
  });
});
