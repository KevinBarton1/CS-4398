export type Mode = "realtime" | "simulated";
export type HeatmapMode = "congestion" | "demand" | "profitability" | "off";

export interface Point { x: number; y: number }
export interface Segment {
  name: string; length_miles: number; lanes: number; speed_limit_mph: number;
  average_speed_mph: number; volume_vehicles_hour: number; congestion: number;
  capacity_vehicles_hour: number; free_flow_minutes: number; adjusted_minutes: number;
}
export interface PriceFactors {
  route_subtotal: number; demand_multiplier: number; traffic_multiplier: number;
  weather_multiplier: number; time_multiplier: number; unrounded_total: number;
}
export interface RouteOption {
  id: string; name: string; objective: string; color: string; distance_miles: number;
  base_eta_minutes: number; adjusted_eta_minutes: number; estimated_price: number;
  congestion_score: number; demand_score: number; normalized_score: number;
  points: Point[]; segments: Segment[]; factors: PriceFactors; data_source: string;
}
export interface PlanResult {
  origin: string; destination: string; mode: Mode; hour: number; congestion: number;
  demand: number; routes: RouteOption[]; recommended_route_id: string; notice: string;
  weather: { label: string; severity: number; time_multiplier: number; price_multiplier: number };
  heatmap: { mode: HeatmapMode; cells: { row: number; column: number; value: number }[] };
}
export interface Scenario { hour: number; weather: number; congestion: number; demand: number }
