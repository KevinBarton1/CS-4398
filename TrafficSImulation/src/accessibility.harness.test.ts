import { readFileSync } from "node:fs";
import { join } from "node:path";
import { describe, expect, it } from "vitest";

describe("T-55 accessibility harness", () => {
  it("includes reduced-motion overrides for animated surfaces", () => {
    const css = readFileSync(join(process.cwd(), "src", "styles.css"), "utf8");
    expect(css).toMatch(/prefers-reduced-motion:reduce/);
    expect(css).toMatch(/\.toast,.route-card/);
    expect(css).toMatch(/transition:none/);
  });

  it("T-55 contrast checks remain above documented thresholds", async () => {
    const { contrastRatio } = await import("./utils/contrast");
    expect(contrastRatio("#f3f8f6", "#0b1915")).toBeGreaterThanOrEqual(4.5);
    expect(contrastRatio("#54d8be", "#0b1915")).toBeGreaterThanOrEqual(3);
  });
});

describe("T-53 bundle budget", () => {
  it("documents the npm check:bundle script gate", () => {
    const pkg = JSON.parse(readFileSync(join(process.cwd(), "package.json"), "utf8"));
    expect(pkg.scripts["check:bundle"]).toContain("check-bundle-size.mjs");
  });
});
