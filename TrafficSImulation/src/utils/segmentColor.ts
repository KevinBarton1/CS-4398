/** Map segment congestion, Google traffic ratio, and weather to a stroke color. */
export function segmentColor(
  congestion: number,
  trafficRatio: number,
  weatherSeverity: number
): string {
  const trafficDelay = Math.max(0, Math.min(1, trafficRatio - 1));
  const severity = Math.max(
    0,
    Math.min(1, 0.5 * congestion + 0.3 * trafficDelay + 0.2 * (weatherSeverity / 3))
  );

  const green = { r: 85, g: 214, b: 190 };
  const yellow = { r: 255, g: 179, b: 92 };
  const red = { r: 232, g: 93, b: 76 };

  const blend = (from: typeof green, to: typeof yellow, amount: number) => ({
    r: Math.round(from.r + (to.r - from.r) * amount),
    g: Math.round(from.g + (to.g - from.g) * amount),
    b: Math.round(from.b + (to.b - from.b) * amount),
  });

  const rgb = severity <= 0.5
    ? blend(green, yellow, severity / 0.5)
    : blend(yellow, red, (severity - 0.5) / 0.5);

  return `rgb(${rgb.r}, ${rgb.g}, ${rgb.b})`;
}
