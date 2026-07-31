import { useMemo, useState } from "react";
import { AnalysisPanel } from "./components/AnalysisPanel";
import { Header } from "./components/Header";
import { MapConfigProvider } from "./components/MapConfigProvider";
import { RouteMap } from "./components/RouteMap";
import { RouteOptionList } from "./components/RouteOptionList";
import { RoutePlannerForm } from "./components/RoutePlannerForm";
import { StatusBanner } from "./components/StatusBanner";
import { Toast, type ToastMessage } from "./components/Toast";
import { useRoutePlan } from "./hooks/useRoutePlan";

export function App() {
  const [notice, setNotice] = useState<ToastMessage | null>(null);
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
    status,
    bannerError,
    toastFromError,
    planStale,
    submit,
    retry,
    resetScenario,
    dismissError,
  } = useRoutePlan();

  const scenarioApplied = plan?.scenario_applied ?? mode === "simulated";
  const toastMessage = useMemo<ToastMessage | null>(() => {
    if (notice) {
      return notice;
    }
    return toastFromError;
  }, [notice, toastFromError]);

  const showLoadingBanner = status === "loading" && !plan;
  const showEmptyBanner = status === "empty";
  const showErrorBanner = status === "error" && bannerError !== null;

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
            onNotice={(message) =>
              setNotice({ detail: message, variant: "info" })
            }
          />
          {showLoadingBanner ? <StatusBanner variant="loading" region="planner" /> : null}
          {showEmptyBanner ? (
            <StatusBanner variant="empty" region="planner" onRetry={retry} />
          ) : null}
          {showErrorBanner ? (
            <StatusBanner variant="error" error={bannerError} region="planner" onRetry={retry} />
          ) : null}
          {planStale ? (
            <p className="stale-marker" role="status">
              Showing the last successful plan. The most recent update did not complete.
            </p>
          ) : null}
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
          setNotice(null);
          dismissError();
        }}
      />
    </>
  );
}
