import { useEffect, useRef } from "react";
import { useMap, useMapsLibrary } from "@vis.gl/react-google-maps";
import type { HeatmapResult } from "../types";
import { heatmapFillColor, heatmapFillOpacity } from "../utils/heatmapColor";

type MapsLibrary = {
  Rectangle: new (options: google.maps.RectangleOptions) => google.maps.Rectangle;
};

interface HeatmapLayerProps {
  heatmap: HeatmapResult | null;
  visible: boolean;
}

export function HeatmapLayer({ heatmap, visible }: HeatmapLayerProps) {
  const map = useMap();
  const mapsLibrary = useMapsLibrary("maps") as MapsLibrary | null;
  const rectanglesRef = useRef<google.maps.Rectangle[]>([]);

  useEffect(() => {
    rectanglesRef.current.forEach((rectangle) => rectangle.setMap(null));
    rectanglesRef.current = [];

    if (!visible || !map || !mapsLibrary?.Rectangle || !heatmap) {
      return;
    }

    const Rectangle = mapsLibrary.Rectangle;
    rectanglesRef.current = heatmap.cells.map((cell) => {
      const rectangle = new Rectangle({
        map,
        bounds: {
          north: cell.bounds.north,
          south: cell.bounds.south,
          east: cell.bounds.east,
          west: cell.bounds.west,
        },
        fillColor: heatmapFillColor(cell.value),
        fillOpacity: heatmapFillOpacity(cell.value),
        strokeWeight: 0,
        clickable: false,
        zIndex: 1,
      });
      return rectangle;
    });

    return () => {
      rectanglesRef.current.forEach((rectangle) => rectangle.setMap(null));
      rectanglesRef.current = [];
    };
  }, [map, mapsLibrary, heatmap, visible]);

  return null;
}
