import type { CSSProperties } from "react";
import type { RouteOption } from "../types";

interface RouteOptionsProps {
  routes: RouteOption[];
  selected?: string;
  recommended?: string;
  onSelect: (id: string) => void;
}

export function RouteOptions({ routes, selected, recommended, onSelect }: RouteOptionsProps) {
  return (
    <section className="block route-options">
      <div className="heading">
        <div>
          <span className="eyebrow">Route options</span>
          <h2>Compare your drive</h2>
        </div>
        <span className="count">{routes.length}</span>
      </div>
      <div className="route-list">
        {routes.map((route) => (
          <button
            key={route.id}
            onClick={() => onSelect(route.id)}
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
