import type {
  ApiError,
  HealthResponse,
  MapConfig,
  PlanRequest,
  PlanResult,
} from "../types";

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
    const candidate = body as Partial<ApiError>;
    if (typeof candidate.detail === "string" && typeof candidate.code === "string") {
      return {
        detail: candidate.detail,
        code: candidate.code,
        fields: Array.isArray(candidate.fields) ? candidate.fields : null,
      };
    }
  }
  return {
    detail: "Request failed.",
    code: "unknown_error",
    fields: null,
  };
}

async function request<T>(
  path: string,
  init: RequestInit,
  signal?: AbortSignal,
): Promise<T> {
  const response = await fetch(path, { ...init, signal });
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

export function getMapConfig(signal?: AbortSignal): Promise<MapConfig> {
  return request<MapConfig>("/api/map/config", { method: "GET" }, signal);
}

export function getHealth(signal?: AbortSignal): Promise<HealthResponse> {
  return request<HealthResponse>("/api/health", { method: "GET" }, signal);
}
