import type { CSSProperties } from "react";
import type { RouteOption } from "../types";
import {
  formatCurrency,
  formatMiles,
  formatMinutes,
  formatScore,
} from "../utils/format";

interface RouteOptionListProps {
  routes: RouteOption[];
  selectedRouteId?: string;
  recommendedRouteId?: string;
  comparisonEnabled: boolean;
  onSelect: (id: string) => void;
}

const REALTIME_EXPLANATION =
  "Real-Time mode returns the single route Google recommends for the current departure time. Switch to Simulated mode to compare up to three alternatives.";

function RouteCardContent({
  route,
  recommendedRouteId,
}: {
  route: RouteOption;
  recommendedRouteId?: string;
}) {
  return (
    <>
      <span className="route-name">
        {route.name}
        {recommendedRouteId === route.id && <em>Recommended</em>}
      </span>
      <span className="route-objective">{route.objective}</span>
      <span className="stats">
        <b>{formatMinutes(route.adjusted_eta_minutes)}</b>
        <b>{formatMinutes(route.base_eta_minutes)} base</b>
        <b>{formatMiles(route.distance_miles)}</b>
        <b>{formatCurrency(route.estimated_price)}</b>
        <b>{formatScore(route.congestion_score)}</b>
      </span>
    </>
  );
}

export function RouteOptionList({
  routes,
  selectedRouteId,
  recommendedRouteId,
  comparisonEnabled,
  onSelect,
}: RouteOptionListProps) {
  return (
    <section className="block route-options">
      <div className="heading">
        <div>
          <span className="eyebrow">Route options</span>
          <h2>Compare your drive</h2>
        </div>
        <span className="count">{routes.length}</span>
      </div>
      {!comparisonEnabled && (
        <p className="panel-disabled-note">{REALTIME_EXPLANATION}</p>
      )}
      <div className="route-list">
        {routes.map((route) => {
          const cardStyle = { "--route": route.color } as CSSProperties;

          if (!comparisonEnabled) {
            return (
              <div
                key={route.id}
                className="route-card route-card-static"
                style={cardStyle}
              >
                <RouteCardContent route={route} />
              </div>
            );
          }

          return (
            <button
              key={route.id}
              type="button"
              onClick={() => onSelect(route.id)}
              aria-pressed={selectedRouteId === route.id}
              className={`route-card ${selectedRouteId === route.id ? "active" : ""}`}
              style={cardStyle}
            >
              <RouteCardContent
                route={route}
                recommendedRouteId={recommendedRouteId}
              />
            </button>
          );
        })}
      </div>
    </section>
  );
}
