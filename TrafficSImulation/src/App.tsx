import { FormEvent, useCallback, useEffect, useMemo, useRef, useState } from "react";
import type { CSSProperties } from "react";
import type { Mode, PlanResult, RouteOption, Scenario } from "./types";

const defaults: Scenario = { hour: 17, weather: 1, congestion: 56, demand: 68 };
const weatherLabels = ["Clear", "Light rain", "Heavy rain", "Severe"];

function hourLabel(hour: number) {
  return `${hour % 12 || 12}:00 ${hour >= 12 ? "PM" : "AM"}`;
}
function path(points: RouteOption["points"]) {
  if (points.length === 3) return `M ${points[0].x} ${points[0].y} Q ${points[1].x} ${points[1].y} ${points[2].x} ${points[2].y}`;
  return points.map((p, i) => `${i ? "L" : "M"} ${p.x} ${p.y}`).join(" ");
}
function RoutePlanner({ origin, destination, setOrigin, setDestination, loading, onSubmit, onLocation }: {
  origin: string; destination: string; setOrigin: (v: string) => void; setDestination: (v: string) => void;
  loading: boolean; onSubmit: (event: FormEvent) => void; onLocation: () => void;
}) {
  return <section className="block search">
    <span className="eyebrow">Route planner</span><h1>Find the better drive.</h1>
    <p>Compare traffic, demand and earning potential before you move.</p>
    <form onSubmit={onSubmit}>
      <label htmlFor="origin">Starting point</label>
      <div className="input"><i className="origin" /><input id="origin" value={origin} onChange={e => setOrigin(e.target.value)} required /></div>
      <button className="link-button" type="button" onClick={onLocation}>◎ Use my current location</button>
      <label htmlFor="destination">Destination or zone</label>
      <div className="input"><i className="destination" /><input id="destination" value={destination} onChange={e => setDestination(e.target.value)} required /></div>
      <small>Try: The Domain, UT Austin, Zilker Park, Mueller, South Congress</small>
      <button className="primary" disabled={loading}><span>{loading ? "Calculating…" : "Plan routes"}</span><span>→</span></button>
    </form>
  </section>;
}

function RouteOptions({ routes, selected, recommended, onSelect }: {
  routes: RouteOption[]; selected?: string; recommended?: string; onSelect: (id: string) => void;
}) {
  return <section className="block route-options">
    <div className="heading"><div><span className="eyebrow">Route options</span><h2>Compare your drive</h2></div><span className="count">{routes.length}</span></div>
    <div className="route-list">{routes.map(route =>
      <button key={route.id} onClick={() => onSelect(route.id)} className={`route-card ${selected === route.id ? "active" : ""}`} style={{ "--route": route.color } as CSSProperties}>
        <span className="route-name">{route.name}{recommended === route.id && <em>Recommended</em>}</span>
        <span className="route-objective">{route.objective}</span>
        <span className="stats"><b>{route.adjusted_eta_minutes} min</b><b>{route.distance_miles} mi</b><b>${route.estimated_price.toFixed(2)}</b></span>
      </button>
    )}</div>
  </section>;
}

function TrafficMap({ data, selectedId, onSelect }: {
  data: PlanResult | null; selectedId?: string; onSelect: (id: string) => void;
}) {
  const firstRoute = data?.routes[0];
  const start = firstRoute?.points[0];
  const end = firstRoute?.points[firstRoute.points.length - 1];
  return <section className="map-shell" aria-label="Google route options">
    <svg viewBox="0 0 1000 650" role="img" aria-label="Three Google routes from point A to point B">
      <defs><filter id="glow"><feGaussianBlur stdDeviation="4" result="b" /><feMerge><feMergeNode in="b" /><feMergeNode in="SourceGraphic" /></feMerge></filter></defs>
      {data?.routes.slice().reverse().map(route =>
        <path
          key={route.id}
          d={path(route.points)}
          onClick={() => onSelect(route.id)}
          className={`route-line ${route.id === selectedId ? "selected" : ""}`}
          stroke={route.color}
          strokeWidth={route.id === selectedId ? 9 : 7}
          data-route-id={route.id}
        >
          <title>{route.name}</title>
        </path>
      )}
      {start && <g className="endpoint" transform={`translate(${start.x} ${start.y})`}><circle r="15" /><text textAnchor="middle" y="5">A</text></g>}
      {end && <g className="endpoint destination" transform={`translate(${end.x} ${end.y})`}><circle r="15" /><text textAnchor="middle" y="5">B</text></g>}
    </svg>
  </section>;
}

function Analysis({ route, recommended, scenario, setScenario, reset }: {
  route?: RouteOption; recommended?: string; scenario: Scenario; setScenario: (v: Scenario) => void; reset: () => void;
}) {
  if (!route) return <aside className="analysis skeleton" />;
  const factors = route.factors;
  const control = (key: keyof Scenario, label: string, min: number, max: number, output: string) =>
    <label className="control"><span><b>{label}</b><output>{output}</output></span><input type="range" min={min} max={max} value={scenario[key]} onChange={e => setScenario({ ...scenario, [key]: Number(e.target.value) })} /></label>;
  return <aside className="analysis">
    <section className="card selected-summary">
      <div className="heading"><div><span className="eyebrow">Selected route</span><h2>{route.name}</h2></div><span className="source">{route.data_source.toLowerCase().includes("reference") ? "Reference" : "Simulated"}</span></div>
      {route.id === recommended && <span className="recommend-line">Recommended route</span>}
      <div className="eta"><b>{route.adjusted_eta_minutes}</b><span>min adjusted ETA</span></div>
      <div className="metrics"><div><span>Distance</span><b>{route.distance_miles} mi</b></div><div><span>Base ETA</span><b>{route.base_eta_minutes} min</b></div><div><span>Congestion</span><b>{route.congestion_score}/100</b></div><div><span>Demand</span><b>{route.demand_score}/100</b></div></div>
    </section>
    <section className="card pricing">
      <div><span className="eyebrow">Planning estimate</span><h2>Expected fare</h2></div><strong>${route.estimated_price.toFixed(2)}</strong>
      <div className="factors"><span>Route ${factors.route_subtotal.toFixed(2)}</span><span>Demand ×{factors.demand_multiplier.toFixed(2)}</span><span>Traffic ×{factors.traffic_multiplier.toFixed(2)}</span><span>Weather ×{factors.weather_multiplier.toFixed(2)}</span><span>Time ×{factors.time_multiplier.toFixed(2)}</span></div>
      <p>Illustrative estimate only. Not an official Uber or Lyft fare.</p>
    </section>
    <section className="card scenario">
      <div className="heading"><div><span className="eyebrow">Scenario lab</span><h2>Shape conditions</h2></div><button onClick={reset}>Reset</button></div>
      {control("hour", "Time of day", 0, 23, hourLabel(scenario.hour))}
      {control("weather", "Weather", 0, 3, weatherLabels[scenario.weather])}
      {control("congestion", "Congestion", 0, 100, `${scenario.congestion}%`)}
      {control("demand", "Customer demand", 0, 100, `${scenario.demand}%`)}
    </section>
    <section className="card road-detail">
      <span className="eyebrow">Road detail</span><h2>Segment statistics</h2>
      <div className="table-wrap"><table><thead><tr><th>Road</th><th>Length</th><th>Speed</th><th>Flow</th></tr></thead><tbody>
        {route.segments.map(segment => <tr key={segment.name}><td><b>{segment.name}</b><small>{segment.lanes} lanes · {Math.round(segment.congestion * 100)}%</small></td><td>{segment.length_miles} mi</td><td>{segment.average_speed_mph} mph<small>limit {segment.speed_limit_mph}</small></td><td>{segment.volume_vehicles_hour.toLocaleString()}<small>veh/hr</small></td></tr>)}
      </tbody></table></div>
    </section>
  </aside>;
}

export function App() {
  const [origin, setOrigin] = useState("Downtown Austin");
  const [destination, setDestination] = useState("Austin Airport");
  const [mode, setMode] = useState<Mode>("simulated");
  const [scenario, setScenario] = useState(defaults);
  const [data, setData] = useState<PlanResult | null>(null);
  const [selectedId, setSelectedId] = useState<string>();
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");
  const debounce = useRef<number | undefined>(undefined);

  const calculate = useCallback(async (keepSelection = true) => {
    setLoading(true); setMessage("");
    try {
      const response = await fetch("/api/plan", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ origin, destination, mode, heatmap: "off", ...scenario }) });
      const result = await response.json();
      if (!response.ok) throw new Error(result.detail || "Route calculation failed.");
      setData(result);
      setSelectedId(current => keepSelection && result.routes.some((r: RouteOption) => r.id === current) ? current : result.recommended_route_id);
    } catch (error) { setMessage(error instanceof Error ? error.message : "Unable to calculate routes."); }
    finally { setLoading(false); }
  }, [origin, destination, mode, scenario]);

  useEffect(() => { void calculate(false); }, []); // initial route
  useEffect(() => {
    if (!data) return;
    window.clearTimeout(debounce.current);
    debounce.current = window.setTimeout(() => void calculate(), 180);
    return () => window.clearTimeout(debounce.current);
  }, [mode, scenario]);

  const selected = useMemo(() => data?.routes.find(route => route.id === selectedId) ?? data?.routes[0], [data, selectedId]);
  const submit = (event: FormEvent) => { event.preventDefault(); void calculate(false); };
  const locate = () => navigator.geolocation?.getCurrentPosition(() => setOrigin("Current location"), () => setMessage("Location permission was denied. Enter a starting point manually."));

  return <>
    <header><a className="brand"><i>▥</i><b>Traffic<span>Scope</span></b></a>
      <div className="mode-switch">{(["realtime", "simulated"] as Mode[]).map(value => <button key={value} onClick={() => setMode(value)} className={mode === value ? "active" : ""}>{value === "realtime" ? "Reference" : "Simulated"}</button>)}</div>
      <span className="status"><i />{loading ? "Recalculating" : "Simulation ready"}</span>
    </header>
    <main>
      <aside className="planner"><RoutePlanner {...{ origin, destination, setOrigin, setDestination, loading, onSubmit: submit, onLocation: locate }} />
        <RouteOptions routes={data?.routes ?? []} selected={selectedId} recommended={data?.recommended_route_id} onSelect={setSelectedId} /></aside>
      <TrafficMap data={data} selectedId={selectedId} onSelect={setSelectedId} />
      <Analysis route={selected} recommended={data?.recommended_route_id} scenario={scenario} setScenario={setScenario} reset={() => setScenario(defaults)} />
    </main>
    {message && <div className="toast" role="alert">{message}<button onClick={() => setMessage("")}>×</button></div>}
  </>;
}
