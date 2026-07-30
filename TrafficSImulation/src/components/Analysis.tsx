import { weatherLabels } from "../constants/scenario";
import type { Mode, RouteOption, Scenario } from "../types";
import { hourLabel } from "../utils/format";

interface AnalysisProps {
  route?: RouteOption;
  recommended?: string;
  mode: Mode;
  scenario: Scenario;
  setScenario: (value: Scenario) => void;
  onReset: () => void;
}

export function Analysis({ route, recommended, mode, scenario, setScenario, onReset }: AnalysisProps) {
  if (!route) return <aside className="analysis skeleton" />;

  const factors = route.factors;
  const scenarioDisabled = mode === "realtime";

  const control = (
    key: keyof Scenario,
    label: string,
    min: number,
    max: number,
    output: string
  ) => (
    <label className="control" key={key}>
      <span>
        <b>{label}</b>
        <output>{output}</output>
      </span>
      <input
        type="range"
        min={min}
        max={max}
        value={scenario[key]}
        disabled={scenarioDisabled}
        onChange={(e) => {
          if (scenarioDisabled) return;
          setScenario({ ...scenario, [key]: Number(e.target.value) });
        }}
      />
    </label>
  );

  return (
    <aside className="analysis">
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

      <section className={`card scenario${scenarioDisabled ? " panel-disabled" : ""}`}>
        <div className="heading">
          <div>
            <span className="eyebrow">Scenario lab</span>
            <h2>Shape conditions</h2>
          </div>
          <button type="button" onClick={onReset} disabled={scenarioDisabled}>
            Reset
          </button>
        </div>
        {scenarioDisabled && (
          <p className="panel-disabled-note">Scenario controls are available in Simulated mode.</p>
        )}
        {control("hour", "Time of day", 0, 23, hourLabel(scenario.hour))}
        {control("weather", "Weather", 0, 3, weatherLabels[scenario.weather])}
        {control("congestion", "Congestion", 0, 100, `${scenario.congestion}%`)}
        {control("demand", "Customer demand", 0, 100, `${scenario.demand}%`)}
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
    </aside>
  );
}
