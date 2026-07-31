export function formatCurrency(value: number): string {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(value);
}

export function formatDistanceMiles(value: number): string {
  return `${value.toFixed(1)} mi`;
}

export function formatMinutes(value: number): string {
  return `${value.toFixed(1)} min`;
}

export function hourLabel(hour: number): string {
  return `${hour % 12 || 12}:00 ${hour >= 12 ? "PM" : "AM"}`;
}
