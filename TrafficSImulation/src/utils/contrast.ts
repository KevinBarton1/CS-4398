function parseHex(hex: string): [number, number, number] {
  const normalized = hex.replace("#", "");
  const value = Number.parseInt(normalized, 16);
  return [(value >> 16) & 255, (value >> 8) & 255, value & 255];
}

function relativeLuminance([red, green, blue]: [number, number, number]): number {
  const channel = (value: number) => {
    const scaled = value / 255;
    return scaled <= 0.03928 ? scaled / 12.92 : ((scaled + 0.055) / 1.055) ** 2.4;
  };
  return 0.2126 * channel(red) + 0.7152 * channel(green) + 0.0722 * channel(blue);
}

export function contrastRatio(foreground: string, background: string): number {
  const lighter = Math.max(relativeLuminance(parseHex(foreground)), relativeLuminance(parseHex(background)));
  const darker = Math.min(relativeLuminance(parseHex(foreground)), relativeLuminance(parseHex(background)));
  return (lighter + 0.05) / (darker + 0.05);
}
