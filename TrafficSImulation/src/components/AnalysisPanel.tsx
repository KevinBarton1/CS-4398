import { ScenarioControls } from "./ScenarioControls";
import { PriceSummary } from "./PriceSummary";
import { SegmentTable } from "./SegmentTable";
import type { Mode, RouteOption, Scenario, WeatherState } from "../types";
import {
  formatMiles,
  formatMinutes,
  formatNormalizedScore,
  formatScore,
} from "../utils/format";

interface AnalysisPanelProps {
  route?: RouteOption;
  origin?: string;
  destination?: string;
  weather?: WeatherState;
  notice?: string;
  recommendedRouteId?: string;
  mode: Mode;
  scenarioApplied: boolean;
  scenario: Scenario;
  onScenarioChange: (value: Scenario) => void;
  onScenarioReset: () => void;
}

const SCENARIO_UNAVAILABLE_NOTE =
  "Real-Time mode plans for the current departure time using live Google Maps traffic. Scenario controls apply in Simulated mode.";

export function AnalysisPanel({
  route,
  origin,
  destination,
  weather,
  notice,
  recommendedRouteId,
  mode,
  scenarioApplied,
  scenario,
  onScenarioChange,
  onScenarioReset,
}: AnalysisPanelProps) {
  if (!route) {
    return (
      <section className="card analysis-placeholder">
        <p className="panel-disabled-note">
          Route analysis appears here after a successful plan.
        </p>
      </section>
    );
  }

  const modeLabel = mode === "realtime" ? "Real-Time" : "Simulated";

  return (
    <>
      <section className="card trip-context">
        {origin && destination && (
          <p className="trip-line">{`${origin} to ${destination}`}</p>
        )}
        {notice && <p className="plan-notice">{notice}</p>}
      </section>

      <section className="card selected-summary">
        <div className="heading">
          <div>
            <span className="eyebrow">Selected route</span>
            <h2>{route.name}</h2>
          </div>
          <span className="source">{modeLabel}</span>
        </div>
        <p className="data-source">{route.data_source}</p>
        {route.id === recommendedRouteId && (
          <span className="recommend-line">Recommended route</span>
        )}
        <div className="eta">
          <b>{route.adjusted_eta_minutes.toFixed(1)}</b>
          <span>min adjusted ETA</span>
        </div>
        <div className="metrics">
          <div>
            <span>Distance</span>
            <b>{formatMiles(route.distance_miles)}</b>
          </div>
          <div>
            <span>Base ETA</span>
            <b>{formatMinutes(route.base_eta_minutes)}</b>
          </div>
          <div>
            <span>Congestion</span>
            <b>{formatScore(route.congestion_score)}</b>
          </div>
          <div>
            <span>Comparison score</span>
            <b>{formatNormalizedScore(route.normalized_score)}</b>
            <small>lower is better</small>
          </div>
          <div>
            <span>Objective</span>
            <b>{route.objective}</b>
          </div>
        </div>
        {weather && (
          <p className="weather-line">{`${weather.label}, ${weather.source}`}</p>
        )}
      </section>

      <PriceSummary route={route} />

      {scenarioApplied ? (
        <ScenarioControls
          scenario={scenario}
          setScenario={onScenarioChange}
          onReset={onScenarioReset}
        />
      ) : (
        <section className="card scenario-unavailable">
          <p className="panel-disabled-note">{SCENARIO_UNAVAILABLE_NOTE}</p>
        </section>
      )}

      <SegmentTable route={route} />
    </>
  );
}
