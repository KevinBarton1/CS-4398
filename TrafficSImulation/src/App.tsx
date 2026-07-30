import { Analysis } from "./components/Analysis";
import { Header } from "./components/Header";
import { RouteOptions } from "./components/RouteOptions";
import { RoutePlanner } from "./components/RoutePlanner";
import { Toast } from "./components/Toast";
import { TrafficMap } from "./components/TrafficMap";
import { useRoutePlan } from "./hooks/useRoutePlan";

export function App() {
  const {
    origin,
    setOrigin,
    destination,
    setDestination,
    mode,
    setMode,
    scenario,
    setScenario,
    data,
    selectedId,
    setSelectedId,
    selectedRoute,
    loading,
    message,
    setMessage,
    handleSubmit,
    handleLocation,
    resetScenario,
  } = useRoutePlan();

  return (
    <>
      <Header mode={mode} onModeChange={setMode} loading={loading} />
      <main>
        <aside className="planner">
          <RoutePlanner
            origin={origin}
            destination={destination}
            setOrigin={setOrigin}
            setDestination={setDestination}
            loading={loading}
            onSubmit={handleSubmit}
            onLocation={handleLocation}
          />
          <RouteOptions
            routes={data?.routes ?? []}
            selected={selectedId}
            recommended={data?.recommended_route_id}
            mode={mode}
            onSelect={setSelectedId}
          />
        </aside>
        <TrafficMap data={data} routes={data?.routes} selectedId={selectedId} />
        <Analysis
          route={selectedRoute}
          recommended={data?.recommended_route_id}
          mode={mode}
          scenario={scenario}
          setScenario={setScenario}
          onReset={resetScenario}
        />
      </main>
      <Toast message={message} onDismiss={() => setMessage("")} />
    </>
  );
}
