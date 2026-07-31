import type { Scenario } from "../types";

export const DEFAULT_HOUR = 17;
export const DEFAULT_WEATHER = 1;
export const DEFAULT_CONGESTION = 56;

export const defaultScenario: Scenario = {
  hour: DEFAULT_HOUR,
  weather: DEFAULT_WEATHER,
  congestion: DEFAULT_CONGESTION,
};

export const weatherLabels = ["Clear", "Light rain", "Heavy rain", "Severe"];
