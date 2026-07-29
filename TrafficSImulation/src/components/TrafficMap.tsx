import type { PlanResult } from "../types";
import { routePath } from "../utils/routePath";

interface TrafficMapProps {
  data: PlanResult | null;
  selectedId?: string;
  onSelect: (id: string) => void;
}

export function TrafficMap({ data, selectedId, onSelect }: TrafficMapProps) {
  const firstRoute = data?.routes[0];
  const start = firstRoute?.points[0];
  const end = firstRoute?.points[firstRoute.points.length - 1];

  return (
    <section className="map-shell" aria-label="Google route options">
      <svg viewBox="0 0 1000 650" role="img" aria-label="Three Google routes from point A to point B">
        <defs>
          <filter id="glow">
            <feGaussianBlur stdDeviation="4" result="b" />
            <feMerge>
              <feMergeNode in="b" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
        </defs>
        {data?.routes
          .slice()
          .reverse()
          .map((route) => (
            <path
              key={route.id}
              d={routePath(route.points)}
              onClick={() => onSelect(route.id)}
              className={`route-line ${route.id === selectedId ? "selected" : ""}`}
              stroke={route.color}
              strokeWidth={route.id === selectedId ? 9 : 7}
              data-route-id={route.id}
            >
              <title>{route.name}</title>
            </path>
          ))}
        {start && (
          <g className="endpoint" transform={`translate(${start.x} ${start.y})`}>
            <circle r="15" />
            <text textAnchor="middle" y="5">
              A
            </text>
          </g>
        )}
        {end && (
          <g className="endpoint destination" transform={`translate(${end.x} ${end.y})`}>
            <circle r="15" />
            <text textAnchor="middle" y="5">
              B
            </text>
          </g>
        )}
      </svg>
    </section>
  );
}
