import { FormEvent } from "react";

interface RoutePlannerProps {
  origin: string;
  destination: string;
  setOrigin: (value: string) => void;
  setDestination: (value: string) => void;
  loading: boolean;
  onSubmit: (event: FormEvent) => void;
  onLocation: () => void;
}

export function RoutePlanner({
  origin,
  destination,
  setOrigin,
  setDestination,
  loading,
  onSubmit,
  onLocation,
}: RoutePlannerProps) {
  return (
    <section className="block search">
      <span className="eyebrow">Route planner</span>
      <h1>Find the better drive.</h1>
      <p>Compare traffic, demand and earning potential before you move.</p>
      <form onSubmit={onSubmit}>
        <label htmlFor="origin">Starting point</label>
        <div className="input">
          <i className="origin" />
          <input
            id="origin"
            value={origin}
            onChange={(e) => setOrigin(e.target.value)}
            required
          />
        </div>
        <button className="link-button" type="button" onClick={onLocation}>
          ◎ Use my current location
        </button>
        <label htmlFor="destination">Destination or zone</label>
        <div className="input">
          <i className="destination" />
          <input
            id="destination"
            value={destination}
            onChange={(e) => setDestination(e.target.value)}
            required
          />
        </div>
        <small>Try: The Domain, UT Austin, Zilker Park, Mueller, South Congress</small>
        <button className="primary" disabled={loading}>
          <span>{loading ? "Calculating…" : "Plan Route(s)"}</span>
          <span>→</span>
        </button>
      </form>
    </section>
  );
}
