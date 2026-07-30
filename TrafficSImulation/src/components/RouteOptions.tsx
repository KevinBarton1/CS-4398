import type { CSSProperties } from "react";
import type { Mode, RouteOption } from "../types";

interface RouteOptionsProps {
  routes: RouteOption[];
  selected?: string;
  recommended?: string;
  mode: Mode;
  onSelect: (id: string) => void;
}

export function RouteOptions({ routes, selected, recommended, mode, onSelect }: RouteOptionsProps) {
  const disabled = mode === "realtime";

  return (
    <section className={`block route-options${disabled ? " panel-disabled" : ""}`}>
      <div className="heading">
        <div>
          <span className="eyebrow">Route options</span>
          <h2>Compare your drive</h2>
        </div>
        <span className="count">{routes.length}</span>
      </div>
      {disabled && (
        <p className="panel-disabled-note">Route comparison is available in Simulated mode.</p>
      )}
      <div className="route-list">
        {routes.map((route) => (
          <button
            key={route.id}
            type="button"
            onClick={() => onSelect(route.id)}
            disabled={disabled}
            aria-disabled={disabled}
            className={`route-card ${selected === route.id ? "active" : ""}`}
            style={{ "--route": route.color } as CSSProperties}
          >
            <span className="route-name">
              {route.name}
              {recommended === route.id && <em>Recommended</em>}
            </span>
            <span className="route-objective">{route.objective}</span>
            <span className="stats">
              <b>{route.adjusted_eta_minutes} min</b>
              <b>{route.distance_miles} mi</b>
              <b>${route.estimated_price.toFixed(2)}</b>
            </span>
          </button>
        ))}
      </div>
    </section>
  );
}
