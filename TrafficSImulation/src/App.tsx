import { useState } from "react";
import { AnalysisPanel } from "./components/AnalysisPanel";
import { Header } from "./components/Header";
import { MapConfigProvider } from "./components/MapConfigProvider";
import { RouteMap } from "./components/RouteMap";
import { RouteOptionList } from "./components/RouteOptionList";
import { RoutePlannerForm } from "./components/RoutePlannerForm";
import { Toast } from "./components/Toast";
import { useRoutePlan } from "./hooks/useRoutePlan";

export function App() {
  const [notice, setNotice] = useState("");
  const {
    origin,
    setOrigin,
    destination,
    setDestination,
    mode,
    setMode,
    scenario,
    setScenario,
    plan,
    selectedId,
    setSelectedId,
    selectedRoute,
    loading,
    message,
    setMessage,
    submit,
    resetScenario,
  } = useRoutePlan();

  const scenarioApplied = plan?.scenario_applied ?? mode === "simulated";
  const toastMessage = notice || message;

  return (
    <>
      <Header mode={mode} onModeChange={setMode} loading={loading} />
      <main>
        <aside className="planner">
          <RoutePlannerForm
            origin={origin}
            destination={destination}
            setOrigin={setOrigin}
            setDestination={setDestination}
            loading={loading}
            onSubmit={submit}
            onNotice={setNotice}
          />
          <RouteOptionList
            routes={plan?.routes ?? []}
            selectedRouteId={selectedId}
            recommendedRouteId={plan?.recommended_route_id}
            comparisonEnabled={scenarioApplied}
            onSelect={setSelectedId}
          />
        </aside>
        <MapConfigProvider>
          <RouteMap
            routes={plan?.routes ?? []}
            selectedRouteId={selectedId}
            planBounds={plan?.map_bounds}
            plan={plan}
            congestion={plan?.scenario_applied ? scenario.congestion : 0}
            weatherSeverity={plan?.scenario_applied ? (plan?.weather.severity ?? 0) : 0}
            selectedRoute={selectedRoute}
          />
        </MapConfigProvider>
        <aside className={`analysis${selectedRoute ? "" : " skeleton"}`}>
          <AnalysisPanel
            route={selectedRoute}
            origin={plan?.origin}
            destination={plan?.destination}
            weather={plan?.weather}
            notice={plan?.notice}
            recommendedRouteId={plan?.recommended_route_id}
            mode={mode}
            scenarioApplied={scenarioApplied}
            scenario={scenario}
            onScenarioChange={setScenario}
            onScenarioReset={resetScenario}
          />
        </aside>
      </main>
      <Toast
        message={toastMessage}
        onDismiss={() => {
          setNotice("");
          setMessage();
        }}
      />
    </>
  );
}
