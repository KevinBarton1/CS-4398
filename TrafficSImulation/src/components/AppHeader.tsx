import type { Mode, RequestState } from "../types";

interface AppHeaderProps {
  mode: Mode;
  status: RequestState;
  hasPlan: boolean;
  onModeChange: (mode: Mode) => void;
}

function resolveStatusLabel(status: RequestState, hasPlan: boolean): string {
  switch (status) {
    case "idle":
      return "Starting";
    case "loading":
      return hasPlan ? "Recalculating" : "Planning";
    case "success":
    case "empty":
      return "Plan ready";
    case "error":
      return "Problem";
  }
}

export function AppHeader({ mode, status, hasPlan, onModeChange }: AppHeaderProps) {
  const statusLabel = resolveStatusLabel(status, hasPlan);
  const statusBusy = status === "loading";

  return (
    <header>
      <a className="brand" href="/" aria-label="TrafficScope home">
        <i aria-hidden="true">▥</i>
        <b>
          Traffic<span>Scope</span>
        </b>
      </a>
      <div className="mode-switch" role="group" aria-label="Planning mode">
        {(["simulated", "realtime"] as Mode[]).map((value) => (
          <button
            key={value}
            type="button"
            onClick={() => onModeChange(value)}
            className={mode === value ? "active" : ""}
            aria-pressed={mode === value}
          >
            {value === "realtime" ? "Real-Time" : "Simulated"}
          </button>
        ))}
      </div>
      <p
        className="status"
        aria-label="Request status"
        aria-live="polite"
        aria-atomic="true"
      >
        <i aria-hidden="true" className={statusBusy ? "status-dot--busy" : undefined} />
        {statusLabel}
      </p>
    </header>
  );
}
