export type TrafficSpeed = "NORMAL" | "SLOW" | "TRAFFIC_JAM" | "SPEED_UNSPECIFIED";

/** Google traffic speed category colors (NORMAL = free-flow blue). */
export const GOOGLE_TRAFFIC_COLORS: Record<TrafficSpeed, string> = {
  NORMAL: "#4285F4",
  SLOW: "#FBBC04",
  TRAFFIC_JAM: "#EA4335",
  SPEED_UNSPECIFIED: "#4285F4",
};

function parseHex(hex: string) {
  const normalized = hex.replace("#", "");
  return {
    r: parseInt(normalized.slice(0, 2), 16),
    g: parseInt(normalized.slice(2, 4), 16),
    b: parseInt(normalized.slice(4, 6), 16),
  };
}

function toHex(r: number, g: number, b: number) {
  const clamp = (value: number) => Math.max(0, Math.min(255, Math.round(value)));
  return `#${[clamp(r), clamp(g), clamp(b)].map((v) => v.toString(16).padStart(2, "0")).join("")}`;
}

function mix(from: string, to: string, amount: number) {
  const start = parseHex(from);
  const end = parseHex(to);
  const t = Math.max(0, Math.min(1, amount));
  return toHex(
    start.r + (end.r - start.r) * t,
    start.g + (end.g - start.g) * t,
    start.b + (end.b - start.b) * t
  );
}

/** Nudge Google traffic colors toward a warmer tint using scenario sliders. */
export function applySliderCorrection(
  baseColor: string,
  congestion: number,
  weatherSeverity: number
): string {
  const congestionFactor = Math.max(0, Math.min(1, congestion / 100));
  const weatherFactor = Math.max(0, Math.min(1, weatherSeverity / 3));
  const strength = congestionFactor * 0.55 + weatherFactor * 0.45;
  if (strength <= 0) return baseColor;
  const corrected = mix(baseColor, "#E8554C", strength * 0.4);
  return mix(corrected, "#1A1A1A", weatherFactor * 0.12);
}

/**
 * NORMAL segments stay Google blue; SLOW/JAM segments keep Google's hue with slider correction.
 */
export function trafficSegmentColor(
  speed: TrafficSpeed,
  congestion: number,
  weatherSeverity: number
): string {
  const base = GOOGLE_TRAFFIC_COLORS[speed] ?? GOOGLE_TRAFFIC_COLORS.NORMAL;
  if (speed === "NORMAL") return base;
  return applySliderCorrection(base, congestion, weatherSeverity);
}
