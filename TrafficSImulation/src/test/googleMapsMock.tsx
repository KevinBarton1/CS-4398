import React from "react";
import { vi } from "vitest";

interface LatLngLiteral {
  lat: number;
  lng: number;
}

interface PolylineOptions {
  path?: LatLngLiteral[];
  strokeColor?: string;
  strokeOpacity?: number;
  strokeWeight?: number;
  geodesic?: boolean;
  clickable?: boolean;
  zIndex?: number;
}

export const mockFitBounds = vi.fn();
export const mockPolylineSetMap = vi.fn();
export const mockPolylineInstances: MockPolyline[] = [];

export class MockPolyline {
  options: PolylineOptions;

  private listeners = new globalThis.Map<string, Set<() => void>>();

  constructor(options: PolylineOptions) {
    this.options = options;
    mockPolylineInstances.push(this);
  }

  setMap = mockPolylineSetMap;

  addListener(eventName: string, handler: () => void) {
    const handlers = this.listeners.get(eventName) ?? new Set<() => void>();
    handlers.add(handler);
    this.listeners.set(eventName, handlers);
    return { remove: () => handlers.delete(handler) };
  }

  emit(eventName: string) {
    this.listeners.get(eventName)?.forEach((handler: () => void) => handler());
  }
}

export class MockMarker {
  options: {
    map?: unknown;
    position?: LatLngLiteral;
    label?: { text: string };
    title?: string;
  };

  constructor(options: MockMarker["options"]) {
    this.options = options;
    mockMarkerInstances.push(this);
  }

  setMap = vi.fn();
}

export const mockMarkerInstances: MockMarker[] = [];

export class MockLatLngBounds {
  southWest: LatLngLiteral;

  northEast: LatLngLiteral;

  constructor(sw: LatLngLiteral, ne: LatLngLiteral) {
    this.southWest = sw;
    this.northEast = ne;
  }
}

export const APILoadingStatus = {
  LOADING: "LOADING",
  LOADED: "LOADED",
  FAILED: "FAILED",
} as const;

export const ColorScheme = {
  DARK: "DARK",
  LIGHT: "LIGHT",
} as const;

export function APIProvider({
  children,
  apiKey,
  libraries,
}: {
  children: React.ReactNode;
  apiKey: string;
  libraries: string[];
}) {
  return (
    <div
      data-testid="api-provider"
      data-api-key={apiKey}
      data-libraries={JSON.stringify(libraries)}
    >
      {children}
    </div>
  );
}

export function Map({
  children,
  className,
}: {
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <div data-testid="google-map" className={className}>
      {children}
    </div>
  );
}

const stableMap = { fitBounds: mockFitBounds };
const mapsLibrary = { Polyline: MockPolyline, Marker: MockMarker };
const coreLibrary = { LatLngBounds: MockLatLngBounds };

export function useMap() {
  return stableMap;
}

export function useMapsLibrary(name: string) {
  if (name === "maps") {
    return mapsLibrary;
  }
  if (name === "core") {
    return coreLibrary;
  }
  return null;
}

export function useApiLoadingStatus() {
  return APILoadingStatus.LOADED;
}

export function resetGoogleMapsMock() {
  mockFitBounds.mockReset();
  mockPolylineSetMap.mockReset();
  mockPolylineInstances.length = 0;
  mockMarkerInstances.length = 0;
}
