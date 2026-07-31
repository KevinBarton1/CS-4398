import { FormEvent } from "react";
import type { RequestState } from "../types";

interface RoutePlannerFormProps {
  origin: string;
  destination: string;
  status: RequestState;
  onOriginChange: (value: string) => void;
  onDestinationChange: (value: string) => void;
  onSubmit: (event: FormEvent) => void;
  onUseCurrentLocation: () => void;
}

export function RoutePlannerForm({
  origin,
  destination,
  status,
  onOriginChange,
  onDestinationChange,
  onSubmit,
  onUseCurrentLocation,
}: RoutePlannerFormProps) {
  const loading = status === "loading";

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
            onChange={(event) => onOriginChange(event.target.value)}
            required
            maxLength={120}
            autoComplete="off"
          />
        </div>
        <button className="link-button" type="button" onClick={onUseCurrentLocation}>
          Use my current location
        </button>
        <label htmlFor="destination">Destination</label>
        <div className="input">
          <i className="destination" aria-hidden="true" />
          <input
            id="destination"
            type="text"
            value={destination}
            onChange={(event) => onDestinationChange(event.target.value)}
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
