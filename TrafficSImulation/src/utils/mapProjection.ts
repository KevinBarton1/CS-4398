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
  height: number
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
  height: number
): string {
  if (polyline.length === 0) return "";
  return polyline
    .map((point, index) => {
      const { x, y } = projectLatLng(point, view, width, height);
      return `${index === 0 ? "M" : "L"}${x.toFixed(1)},${y.toFixed(1)}`;
    })
    .join(" ");
}

/** Highest zoom where every polyline point fits inside the viewport. */
export function computeMapViewForPolyline(
  polyline: LatLng[],
  width: number,
  height: number,
  margin = 16
): MapView | null {
  if (polyline.length === 0 || width <= 0 || height <= 0) return null;

  const lats = polyline.map((point) => point.lat);
  const lngs = polyline.map((point) => point.lng);
  const center_lat = (Math.min(...lats) + Math.max(...lats)) / 2;
  const center_lng = (Math.min(...lngs) + Math.max(...lngs)) / 2;

  if (polyline.length === 1) {
    return { center_lat, center_lng, zoom: 14 };
  }

  for (let zoom = 18; zoom >= 1; zoom -= 1) {
    const view = { center_lat, center_lng, zoom };
    const fits = polyline.every((point) => {
      const { x, y } = projectLatLng(point, view, width, height);
      return x >= margin && x <= width - margin && y >= margin && y <= height - margin;
    });
    if (fits) return view;
  }

  return { center_lat, center_lng, zoom: 1 };
}
