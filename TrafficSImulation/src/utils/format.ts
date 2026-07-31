export function formatCurrency(value: number): string {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(value);
}

export function formatMiles(value: number): string {
  return `${value.toFixed(1)} mi`;
}

export function formatMinutes(value: number): string {
  return `${value.toFixed(1)} min`;
}

export function formatFlow(value: number): string {
  return `${Math.round(value).toLocaleString("en-US")} veh/hr`;
}

export function formatMultiplier(value: number): string {
  return `x${value.toFixed(2)}`;
}

export function formatScore(value: number): string {
  return `${Math.round(value)} / 100`;
}

export function formatRatioPercent(value: number): string {
  return `${Math.round(value * 100)}%`;
}

export function formatNormalizedScore(value: number): string {
  return value.toFixed(4);
}

export function hourLabel(hour: number): string {
  return `${hour % 12 || 12}:00 ${hour >= 12 ? "PM" : "AM"}`;
}
