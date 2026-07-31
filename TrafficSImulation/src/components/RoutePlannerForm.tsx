import { FormEvent, useCallback } from "react";

interface RoutePlannerFormProps {
  origin: string;
  destination: string;
  setOrigin: (value: string) => void;
  setDestination: (value: string) => void;
  loading: boolean;
  onSubmit: (event: FormEvent) => void;
  onNotice: (message: string) => void;
}

const GEOLOCATION_OPTIONS: PositionOptions = {
  enableHighAccuracy: false,
  timeout: 8000,
};

function formatCoordinates(latitude: number, longitude: number): string {
  return `${latitude.toFixed(5)}, ${longitude.toFixed(5)}`;
}

export function RoutePlannerForm({
  origin,
  destination,
  setOrigin,
  setDestination,
  loading,
  onSubmit,
  onNotice,
}: RoutePlannerFormProps) {
  const handleGeolocation = useCallback(() => {
    if (!navigator.geolocation) {
      onNotice("This browser does not provide location access. Enter a starting point manually.");
      return;
    }

    navigator.geolocation.getCurrentPosition(
      (position) => {
        setOrigin(formatCoordinates(position.coords.latitude, position.coords.longitude));
      },
      (error) => {
        if (error.code === error.PERMISSION_DENIED) {
          onNotice("Location permission was denied. Enter a starting point manually.");
          return;
        }
        onNotice("Could not read your location. Enter a starting point manually.");
      },
      GEOLOCATION_OPTIONS,
    );
  }, [onNotice, setOrigin]);

  return (
    <section className="block search">
      <span className="eyebrow">Route planner</span>
      <h1>Find the better drive.</h1>
      <p>Compare traffic, demand and earning potential before you move.</p>
      <form onSubmit={onSubmit}>
        <label htmlFor="origin">Starting point</label>
        <div className="input">
          <i className="origin" aria-hidden="true" />
          <input
            id="origin"
            type="text"
            value={origin}
            onChange={(event) => setOrigin(event.target.value)}
            required
            maxLength={120}
            autoComplete="off"
          />
        </div>
        <button className="link-button" type="button" onClick={handleGeolocation}>
          Use my current location
        </button>
        <label htmlFor="destination">Destination</label>
        <div className="input">
          <i className="destination" aria-hidden="true" />
          <input
            id="destination"
            type="text"
            value={destination}
            onChange={(event) => setDestination(event.target.value)}
            required
            maxLength={120}
            autoComplete="off"
          />
        </div>
        <small>Try: The Domain, UT Austin, Zilker Park, Mueller, South Congress</small>
        <button className="primary" type="submit" disabled={loading}>
          <span>{loading ? "Planning..." : "Plan routes"}</span>
          <span aria-hidden="true">→</span>
        </button>
      </form>
    </section>
  );
}
