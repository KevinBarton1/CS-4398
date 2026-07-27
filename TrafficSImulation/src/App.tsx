import { FormEvent, useCallback, useEffect, useMemo, useRef, useState } from "react";
import type { CSSProperties } from "react";
import type { HeatmapMode, Mode, PlanResult, RouteOption, Scenario } from "./types";

const defaults: Scenario = { hour: 17, weather: 1, congestion: 56, demand: 68 };
const weatherLabels = ["Clear", "Light rain", "Heavy rain", "Severe"];

function hourLabel(hour: number) {
  return `${hour % 12 || 12}:00 ${hour >= 12 ? "PM" : "AM"}`;
}
function path(points: RouteOption["points"]) {
  if (points.length === 3) return `M ${points[0].x} ${points[0].y} Q ${points[1].x} ${points[1].y} ${points[2].x} ${points[2].y}`;
  return points.map((p, i) => `${i ? "L" : "M"} ${p.x} ${p.y}`).join(" ");
}
function heatColor(value: number) {
  return value < 45 ? "#36d1b7" : value < 72 ? "#f6c85f" : "#ff7668";
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

function TrafficMap({ data, selected, heatmap, setHeatmap, onSelect }: {
  data: PlanResult | null; selected?: RouteOption; heatmap: HeatmapMode;
  setHeatmap: (v: HeatmapMode) => void; onSelect: (id: string) => void;
}) {
  const start = selected?.points[0];
  const end = selected?.points[selected.points.length - 1];
  return <section className="map-shell" aria-label="Interactive traffic simulation map">
    <div className="map-toolbar">
      <div className="tabs">{(["congestion", "demand", "profitability", "off"] as HeatmapMode[]).map(mode =>
        <button key={mode} className={heatmap === mode ? "active" : ""} onClick={() => setHeatmap(mode)}>
          {mode === "congestion" ? "Traffic" : mode === "profitability" ? "Earnings" : mode[0].toUpperCase() + mode.slice(1)}
        </button>)}
      </div><button className="map-action" aria-label="Reset map view">⌖</button>
    </div>
    <svg viewBox="0 0 1000 650" role="img" aria-label="Austin road network with candidate routes and heatmap">
      <defs><pattern id="grid" width="42" height="42" patternUnits="userSpaceOnUse" patternTransform="rotate(13)"><path d="M42 0H0V42" fill="none" stroke="#1a2b27" /></pattern>
      <filter id="glow"><feGaussianBlur stdDeviation="4" result="b" /><feMerge><feMergeNode in="b" /><feMergeNode in="SourceGraphic" /></feMerge></filter></defs>
      <rect width="1000" height="650" fill="#0d1c18" /><rect width="1000" height="650" fill="url(#grid)" />
      <path className="water" d="M-20 490C180 430 215 540 420 485S760 430 1030 520V690H-20Z" />
      <g className="roads minor"><path d="M30 125L970 545M0 250L1000 180M45 575L920 80M178 0L285 650M760 0L645 650M0 390L1000 350M85 35L925 615M100 640L890 20" /></g>
      <g className="roads major"><path d="M495-20C450 130 550 210 505 340S470 510 540 680M15 320C230 280 330 360 520 315S770 280 1010 335M290-20C350 120 335 235 380 345S385 525 410 680" /></g>
      {data?.heatmap.cells.map(cell => <rect key={`${cell.row}-${cell.column}`} x={cell.column * 125} y={cell.row * 130} width="126" height="131" rx="18" fill={heatColor(cell.value)} opacity={0.05 + cell.value / 650}><title>{data.heatmap.mode}: {cell.value}/100</title></rect>)}
      {data?.routes.slice().reverse().map(route => <path key={route.id} d={path(route.points)} onClick={() => onSelect(route.id)} className={`route-line ${route.id === selected?.id ? "selected" : ""}`} stroke={route.color} strokeWidth={route.id === selected?.id ? 9 : 7} />)}
      {start && <g transform={`translate(${start.x} ${start.y})`}><circle r="11" fill="#55d6be" stroke="#e8fffa" strokeWidth="3" /><text x="17" y="4">{data?.origin}</text></g>}
      {end && <g transform={`translate(${end.x} ${end.y})`}><path d="M0 15C-3 8-11 1-11-7a11 11 0 1122 0C11 1 3 8 0 15Z" fill="#ffb35c" stroke="#fff2df" strokeWidth="2" /><text x="17">{data?.destination}</text></g>}
      <g className="labels"><text x="460" y="315">DOWNTOWN</text><text x="463" y="190">UT AUSTIN</text><text x="746" y="470">AIRPORT</text><text x="450" y="58">THE DOMAIN</text><text x="148" y="365">ZILKER</text></g>
    </svg>
    {heatmap !== "off" && <div className="legend"><span>{heatmap} intensity</span><i /><small><span>Low</span><span>High</span></small></div>}
    <div className="map-note">{data?.notice ?? "Enter two locations to compare routes."}</div>
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
  const [heatmap, setHeatmap] = useState<HeatmapMode>("congestion");
  const [scenario, setScenario] = useState(defaults);
  const [data, setData] = useState<PlanResult | null>(null);
  const [selectedId, setSelectedId] = useState<string>();
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");
  const debounce = useRef<number | undefined>(undefined);

  const calculate = useCallback(async (keepSelection = true) => {
    setLoading(true); setMessage("");
    try {
      const response = await fetch("/api/plan", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ origin, destination, mode, heatmap, ...scenario }) });
      const result = await response.json();
      if (!response.ok) throw new Error(result.detail || "Route calculation failed.");
      setData(result);
      setSelectedId(current => keepSelection && result.routes.some((r: RouteOption) => r.id === current) ? current : result.recommended_route_id);
    } catch (error) { setMessage(error instanceof Error ? error.message : "Unable to calculate routes."); }
    finally { setLoading(false); }
  }, [origin, destination, mode, heatmap, scenario]);

  useEffect(() => { void calculate(false); }, []); // initial route
  useEffect(() => {
    if (!data) return;
    window.clearTimeout(debounce.current);
    debounce.current = window.setTimeout(() => void calculate(), 180);
    return () => window.clearTimeout(debounce.current);
  }, [mode, heatmap, scenario]);

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
      <TrafficMap {...{ data, selected, heatmap, setHeatmap, onSelect: setSelectedId }} />
      <Analysis route={selected} recommended={data?.recommended_route_id} scenario={scenario} setScenario={setScenario} reset={() => setScenario(defaults)} />
    </main>
    {message && <div className="toast" role="alert">{message}<button onClick={() => setMessage("")}>×</button></div>}
  </>;
}
