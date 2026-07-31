export type Mode = "simulated" | "realtime";

export type TrafficSpeed = "NORMAL" | "SLOW" | "TRAFFIC_JAM" | "SPEED_UNSPECIFIED";

export type RequestState = "idle" | "loading" | "success" | "empty" | "error";

export type ApiErrorCode =
  | "validation_error"
  | "invalid_location"
  | "same_origin_destination"
  | "no_route_found"
  | "maps_not_configured"
  | "upstream_unavailable"
  | "upstream_timeout"
  | null;

export interface LatLngPoint {
  lat: number;
  lng: number;
}

export interface RouteBounds {
  north: number;
  south: number;
  east: number;
  west: number;
}

export interface TrafficInterval {
  start_index: number;
  end_index: number;
  speed: TrafficSpeed;
}

export interface Scenario {
  hour: number;
  weather: number;
  congestion: number;
}

export interface WeatherState {
  severity: number;
  label: string;
  time_multiplier: number;
  price_multiplier: number;
  source: string;
}

export interface PriceFactors {
  route_subtotal: number;
  traffic_multiplier: number;
  weather_multiplier: number;
  time_multiplier: number;
  unrounded_total: number;
}

export interface RoadSegment {
  name: string;
  length_miles: number;
  lanes: number;
  speed_limit_mph: number;
  average_speed_mph: number;
  volume_vehicles_hour: number;
  congestion: number;
  capacity_vehicles_hour: number;
  free_flow_minutes: number;
  adjusted_minutes: number;
  traffic_ratio: number;
  polyline: LatLngPoint[];
}

export interface RouteOption {
  id: string;
  name: string;
  objective: string;
  color: string;
  distance_miles: number;
  base_eta_minutes: number;
  adjusted_eta_minutes: number;
  estimated_price: number;
  congestion_score: number;
  normalized_score: number;
  data_source: string;
  polyline: LatLngPoint[];
  traffic_intervals: TrafficInterval[];
  segments: RoadSegment[];
  price_factors: PriceFactors;
  bounds: RouteBounds;
}

export interface PlanResult {
  origin: string;
  destination: string;
  mode: Mode;
  scenario_applied: boolean;
  scenario: Scenario;
  weather: WeatherState;
  routes: RouteOption[];
  recommended_route_id: string;
  map_bounds: RouteBounds;
  notice: string;
}

export interface PlanRequest {
  origin: string;
  destination: string;
  mode: Mode;
  hour: number;
  weather: number;
  congestion: number;
}

export interface MapConfig {
  maps_browser_api_key: string;
  map_id: string | null;
  default_center: LatLngPoint;
  default_zoom: number;
  color_scheme: string;
  libraries: string[];
}

export interface ProbeResult {
  ok: boolean;
  message: string;
  checked_at: string;
}

export interface HealthResponse {
  status: string;
  service: string;
  version: string;
  google_maps_configured: boolean;
  google_maps: ProbeResult;
}

export interface ValidationField {
  field: string;
  message: string;
}

export interface ApiError {
  detail: string;
  code: ApiErrorCode;
  fields: ValidationField[] | null;
}
