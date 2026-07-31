import type {
  ApiError,
  HealthResponse,
  HeatmapRequest,
  HeatmapResult,
  MapConfig,
  PlanRequest,
  PlanResult,
} from "../types";

export const CONNECTIVITY_DETAIL =
  "Could not reach TrafficScope. Check your connection and try again.";

export class ApiClientError extends Error {
  readonly apiError: ApiError;

  constructor(apiError: ApiError) {
    super(apiError.detail);
    this.name = "ApiClientError";
    this.apiError = apiError;
  }
}

async function readJson(response: Response): Promise<unknown> {
  try {
    return await response.json();
  } catch {
    return null;
  }
}

function parseApiError(body: unknown): ApiError {
  if (typeof body === "object" && body !== null) {
    const candidate = body as Partial<ApiError & { code?: string | null }>;
    if (typeof candidate.detail === "string" && typeof candidate.code === "string") {
      return {
        detail: candidate.detail,
        code: candidate.code as ApiError["code"],
        fields: Array.isArray(candidate.fields) ? candidate.fields : null,
      };
    }
  }
  return {
    detail: "Request failed.",
    code: null,
    fields: null,
  };
}

async function request<T>(
  path: string,
  init: RequestInit,
  signal?: AbortSignal,
): Promise<T> {
  let response: Response;
  try {
    response = await fetch(path, { ...init, signal });
  } catch (error) {
    if (error instanceof DOMException && error.name === "AbortError") {
      throw error;
    }
    throw new ApiClientError({
      detail: CONNECTIVITY_DETAIL,
      code: null,
      fields: null,
    });
  }

  const body = await readJson(response);

  if (!response.ok) {
    throw new ApiClientError(parseApiError(body));
  }

  return body as T;
}

export function postPlan(
  body: PlanRequest,
  signal?: AbortSignal,
): Promise<PlanResult> {
  return request<PlanResult>(
    "/api/plan",
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    },
    signal,
  );
}

export function postHeatmap(
  body: HeatmapRequest,
  signal?: AbortSignal,
): Promise<HeatmapResult> {
  return request<HeatmapResult>(
    "/api/heatmap",
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    },
    signal,
  );
}

export function getMapConfig(signal?: AbortSignal): Promise<MapConfig> {
  return request<MapConfig>("/api/map/config", { method: "GET" }, signal);
}

export function getHealth(signal?: AbortSignal): Promise<HealthResponse> {
  return request<HealthResponse>("/api/health", { method: "GET" }, signal);
}
