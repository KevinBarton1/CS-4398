import type { Mode, RouteOption } from "../types";

interface AnalysisProps {
  route?: RouteOption;
  recommended?: string;
  mode: Mode;
}

export function Analysis({ route, recommended, mode }: AnalysisProps) {
  if (!route) return null;

  const factors = route.price_factors;

  return (
    <>
      <section className="card selected-summary">
        <div className="heading">
          <div>
            <span className="eyebrow">Selected route</span>
            <h2>{route.name}</h2>
          </div>
          <span className="source">
            {mode === "realtime" ? "Real-Time" : "Simulated"}
          </span>
        </div>
        {route.id === recommended && <span className="recommend-line">Recommended route</span>}
        <div className="eta">
          <b>{route.adjusted_eta_minutes}</b>
          <span>min adjusted ETA</span>
        </div>
        <div className="metrics">
          <div>
            <span>Distance</span>
            <b>{route.distance_miles} mi</b>
          </div>
          <div>
            <span>Base ETA</span>
            <b>{route.base_eta_minutes} min</b>
          </div>
        </div>
      </section>

      <section className="card pricing">
        <div>
          <span className="eyebrow">Planning estimate</span>
          <h2>Expected fare</h2>
        </div>
        <strong>${route.estimated_price.toFixed(2)}</strong>
        <div className="factors">
          <span>Route ${factors.route_subtotal.toFixed(2)}</span>
        </div>
        <p>Illustrative estimate only. Not an official Uber or Lyft fare.</p>
      </section>

      <section className="card road-detail">
        <span className="eyebrow">Road detail</span>
        <h2>Segment statistics</h2>
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Road</th>
                <th>Length</th>
                <th>Speed</th>
                <th>Flow</th>
              </tr>
            </thead>
            <tbody>
              {route.segments.map((segment) => (
                <tr key={segment.name}>
                  <td>
                    <b>{segment.name}</b>
                    <small>
                      {segment.lanes} lanes · {Math.round(segment.congestion * 100)}%
                    </small>
                  </td>
                  <td>{segment.length_miles} mi</td>
                  <td>
                    {segment.average_speed_mph} mph
                    <small>limit {segment.speed_limit_mph}</small>
                  </td>
                  <td>
                    {segment.volume_vehicles_hour.toLocaleString()}
                    <small>veh/hr</small>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </>
  );
}
