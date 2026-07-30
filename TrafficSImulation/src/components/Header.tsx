import type { Mode } from "../types";

interface HeaderProps {
  mode: Mode;
  onModeChange: (mode: Mode) => void;
  loading: boolean;
}

export function Header({ mode, onModeChange, loading }: HeaderProps) {
  return (
    <header>
      <a className="brand">
        <i>▥</i>
        <b>
          Traffic<span>Scope</span>
        </b>
      </a>
      <div className="mode-switch">
        {(["realtime", "simulated"] as Mode[]).map((value) => (
          <button
            key={value}
            onClick={() => onModeChange(value)}
            className={mode === value ? "active" : ""}
          >
            {value === "realtime" ? "Real-Time" : "Simulated"}
          </button>
        ))}
      </div>
      <span className="status">
        <i />
        {loading ? "Recalculating" : "Simulation ready"}
      </span>
    </header>
  );
}
