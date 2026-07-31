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

  constructor(options: PolylineOptions) {
    this.options = options;
    mockPolylineInstances.push(this);
  }

  setMap = mockPolylineSetMap;
}

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
const mapsLibrary = { Polyline: MockPolyline };
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
}
