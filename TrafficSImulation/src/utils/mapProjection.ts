export interface LatLng {
  lat: number;
  lng: number;
}

export interface MapView {
  center_lat: number;
  center_lng: number;
  zoom: number;
}

function worldCoordinate(lat: number, lng: number, scale: number) {
  const x = ((lng + 180) / 360) * scale;
  const sinLat = Math.sin((lat * Math.PI) / 180);
  const y = (0.5 - Math.log((1 + sinLat) / (1 - sinLat)) / (4 * Math.PI)) * scale;
  return { x, y };
}

export function projectLatLng(
  point: LatLng,
  view: MapView,
  width: number,
  height: number,
): { x: number; y: number } {
  const scale = 256 * 2 ** view.zoom;
  const world = worldCoordinate(point.lat, point.lng, scale);
  const center = worldCoordinate(view.center_lat, view.center_lng, scale);
  return {
    x: world.x - center.x + width / 2,
    y: world.y - center.y + height / 2,
  };
}

export function polylineToPath(
  polyline: LatLng[],
  view: MapView,
  width: number,
  height: number,
): string {
  if (polyline.length === 0) return "";
  return polyline
    .map((point, index) => {
      const { x, y } = projectLatLng(point, view, width, height);
      return `${index === 0 ? "M" : "L"}${x.toFixed(2)},${y.toFixed(2)}`;
    })
    .join(" ");
}
