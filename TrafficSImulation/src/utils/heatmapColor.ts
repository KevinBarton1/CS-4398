export const HEATMAP_FILL_OPACITY_MAX = 0.55;

export function heatmapFillOpacity(value: number): number {
  const clamped = Math.max(0, Math.min(100, value));
  return (clamped / 100) * HEATMAP_FILL_OPACITY_MAX;
}

export function heatmapFillColor(value: number): string {
  if (value >= 70) {
    return "#ff5c45";
  }
  if (value >= 40) {
    return "#ffb35c";
  }
  return "#55d6be";
}
