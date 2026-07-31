import { useState } from "react";
import { Analysis } from "./components/Analysis";
import { Header } from "./components/Header";
import { MapConfigProvider } from "./components/MapConfigProvider";
import { RouteMap } from "./components/RouteMap";
import { RouteOptions } from "./components/RouteOptions";
import { RoutePlannerForm } from "./components/RoutePlannerForm";
import { ScenarioControls } from "./components/ScenarioControls";
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

  const showScenarioControls = mode === "simulated" && (plan?.scenario_applied ?? true);
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
          <RouteOptions
            routes={plan?.routes ?? []}
            selected={selectedId}
            recommended={plan?.recommended_route_id}
            mode={mode}
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
          {selectedRoute ? (
            <Analysis route={selectedRoute} recommended={plan?.recommended_route_id} mode={mode} />
          ) : null}
          {showScenarioControls ? (
            <ScenarioControls
              scenario={scenario}
              setScenario={setScenario}
              onReset={resetScenario}
            />
          ) : (
            <section className="card scenario-unavailable">
              <p className="panel-disabled-note">
                Real-Time mode plans for the current departure time using live Google Maps traffic.
                Scenario controls apply in Simulated mode.
              </p>
            </section>
          )}
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
