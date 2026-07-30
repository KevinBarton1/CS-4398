export type Mode = "realtime" | "simulated";

export type TrafficSpeed = "NORMAL" | "SLOW" | "TRAFFIC_JAM" | "SPEED_UNSPECIFIED";

export interface TrafficInterval {
  start_index: number;
  end_index: number;
  speed: TrafficSpeed;
}

export interface Segment {
  name: string; length_miles: number; lanes: number; speed_limit_mph: number;
  average_speed_mph: number; volume_vehicles_hour: number; congestion: number;
  capacity_vehicles_hour: number; free_flow_minutes: number; adjusted_minutes: number;
  traffic_ratio: number;
  polyline: { lat: number; lng: number }[];
}
export interface PriceFactors {
  route_subtotal: number; traffic_multiplier: number;
  weather_multiplier: number; time_multiplier?: number; unrounded_total: number;
}
export interface RouteOption {
  id: string; name: string; objective: string; color: string; distance_miles: number;
  base_eta_minutes: number; adjusted_eta_minutes: number; estimated_price: number;
  congestion_score: number; normalized_score: number;
  segments: Segment[]; factors: PriceFactors; data_source: string;
  polyline: { lat: number; lng: number }[];
  traffic_intervals?: TrafficInterval[];
  map_view?: MapView;
  map_embed_url?: string | null;
}
export interface MapView { center_lat: number; center_lng: number; zoom: number; }
export interface PlanResult {
  origin: string; destination: string; mode: Mode; hour: number; congestion: number;
  routes: RouteOption[]; recommended_route_id: string; notice: string;
  map_embed_url: string | null;
  map_view?: MapView;
  directions_embed_url?: string | null;
  weather: { label: string; severity: number; time_multiplier: number; price_multiplier: number };
}
export interface Scenario { hour: number; weather: number; congestion: number }
