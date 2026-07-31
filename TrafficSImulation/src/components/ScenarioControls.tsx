import { weatherLabels } from "../constants/scenario";
import type { Scenario } from "../types";
import { hourLabel } from "../utils/format";

interface ScenarioControlsProps {
  scenario: Scenario;
  setScenario: (value: Scenario) => void;
  onReset: () => void;
}

type ScenarioKey = keyof Scenario;

interface ControlDescriptor {
  key: ScenarioKey;
  id: string;
  label: string;
  min: number;
  max: number;
  format: (scenario: Scenario) => string;
}

const CONTROL_DESCRIPTORS: ControlDescriptor[] = [
  {
    key: "hour",
    id: "scenario-hour",
    label: "Time of day",
    min: 0,
    max: 23,
    format: (scenario) => hourLabel(scenario.hour),
  },
  {
    key: "weather",
    id: "scenario-weather",
    label: "Weather",
    min: 0,
    max: 3,
    format: (scenario) => weatherLabels[scenario.weather],
  },
  {
    key: "congestion",
    id: "scenario-congestion",
    label: "Congestion",
    min: 0,
    max: 100,
    format: (scenario) => `${scenario.congestion}%`,
  },
];

export function ScenarioControls({ scenario, setScenario, onReset }: ScenarioControlsProps) {
  return (
    <section className="card scenario">
      <div className="heading">
        <div>
          <span className="eyebrow">Scenario lab</span>
          <h2>Shape conditions</h2>
        </div>
        <button type="button" onClick={onReset}>
          Reset
        </button>
      </div>
      {CONTROL_DESCRIPTORS.map(({ key, id, label, min, max, format }) => (
        <label className="control" htmlFor={id} key={key}>
          <span>
            <b>{label}</b>
            <output htmlFor={id}>{format(scenario)}</output>
          </span>
          <input
            id={id}
            type="range"
            min={min}
            max={max}
            step={1}
            value={scenario[key]}
            aria-valuetext={format(scenario)}
            onChange={(event) =>
              setScenario({ ...scenario, [key]: Number(event.target.value) })
            }
          />
        </label>
      ))}
    </section>
  );
}
