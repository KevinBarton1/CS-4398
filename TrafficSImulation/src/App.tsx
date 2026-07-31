import { AnalysisPanel } from "./components/AnalysisPanel";
import { AppHeader } from "./components/AppHeader";
import { MapConfigProvider } from "./components/MapConfigProvider";
import { RouteMap } from "./components/RouteMap";
import { RouteOptionList } from "./components/RouteOptionList";
import { RoutePlannerForm } from "./components/RoutePlannerForm";
import { shouldShowPlanErrorAsToast, StatusBanner } from "./components/StatusBanner";
import { Toast } from "./components/Toast";
import { useRoutePlan } from "./hooks/useRoutePlan";

export function App() {
  const {
    origin,
    destination,
    mode,
    scenario,
    plan,
    routes,
    selectedRouteId,
    selectedRoute,
    scenarioApplied,
    effectiveScenario,
    status,
    error,
    toast,
    viewAll,
    setOrigin,
    setDestination,
    setMode,
    setScenario,
    resetScenario,
    selectRoute,
    toggleViewAll,
    submit,
    retry,
    useCurrentLocation,
    dismissToast,
  } = useRoutePlan();

  const showLoadingBanner = status === "loading" && !plan;
  const showEmptyBanner = status === "empty";
  const showErrorBanner =
    status === "error" && error !== null && !shouldShowPlanErrorAsToast(error, plan !== null);
  const planStale = status === "error" && plan !== null;

  return (
    <>
      <a href="#main-content" className="skip-link">
        Skip to main content
      </a>
      <AppHeader
        mode={mode}
        status={status}
        hasPlan={plan !== null}
        onModeChange={setMode}
      />
      <main id="main-content">
        <aside className="planner" aria-label="Trip planning">
          <RoutePlannerForm
            origin={origin}
            destination={destination}
            status={status}
            onOriginChange={setOrigin}
            onDestinationChange={setDestination}
            onSubmit={submit}
            onUseCurrentLocation={useCurrentLocation}
          />
          {showLoadingBanner ? (
            <StatusBanner variant="loading" region="planner" />
          ) : null}
          {showEmptyBanner ? (
            <StatusBanner variant="empty" region="planner" onRetry={retry} />
          ) : null}
          {showErrorBanner ? (
            <StatusBanner variant="error" error={error} region="planner" onRetry={retry} />
          ) : null}
          {planStale ? (
            <p className="stale-marker" role="status">
              Showing the last successful plan. The most recent update did not complete.
            </p>
          ) : null}
          <RouteOptionList
            routes={routes}
            selectedRouteId={selectedRouteId}
            recommendedRouteId={plan?.recommended_route_id}
            comparisonEnabled={scenarioApplied}
            onSelect={selectRoute}
          />
        </aside>
        <section className="map" aria-label="Route map">
          <MapConfigProvider>
            <RouteMap
              routes={routes}
              selectedRouteId={selectedRouteId}
              planBounds={plan?.map_bounds}
              plan={plan}
              congestion={scenarioApplied ? effectiveScenario.congestion : 0}
              weatherSeverity={scenarioApplied ? (plan?.weather.severity ?? 0) : 0}
              heatmapHour={effectiveScenario.hour}
              heatmapCongestion={effectiveScenario.congestion}
              viewAll={viewAll}
              onToggleViewAll={toggleViewAll}
              selectedRoute={selectedRoute}
              onSelectRoute={selectRoute}
            />
          </MapConfigProvider>
        </section>
        <aside className="analysis" aria-label="Route analysis">
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
      <Toast message={toast} onDismiss={dismissToast} />
    </>
  );
}
