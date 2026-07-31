import { useEffect, useState } from "react";
import { ApiClientError, getMapConfig } from "../api/client";
import type { ApiError, MapConfig, RequestState } from "../types";

let cachedConfig: MapConfig | null = null;
let cachedError: ApiError | null = null;
let inflight: Promise<void> | null = null;

/** Clears the session cache. Test-only helper. */
export function resetMapConfigCache(): void {
  cachedConfig = null;
  cachedError = null;
  inflight = null;
}

function fetchMapConfigOnce(): Promise<void> {
  if (cachedConfig || cachedError) {
    return Promise.resolve();
  }
  if (inflight) {
    return inflight;
  }

  inflight = getMapConfig()
    .then((config) => {
      cachedConfig = config;
      cachedError = null;
    })
    .catch((caught) => {
      cachedError =
        caught instanceof ApiClientError
          ? caught.apiError
          : {
              detail: caught instanceof Error ? caught.message : "Map configuration unavailable.",
              code: "unknown_error",
              fields: null,
            };
      cachedConfig = null;
    })
    .finally(() => {
      inflight = null;
    });

  return inflight;
}

export function useMapConfig() {
  const [config, setConfig] = useState<MapConfig | null>(cachedConfig);
  const [error, setError] = useState<ApiError | null>(cachedError);
  const [status, setStatus] = useState<RequestState>(() => {
    if (cachedConfig) return "success";
    if (cachedError) return "error";
    return "idle";
  });

  useEffect(() => {
    if (cachedConfig) {
      setConfig(cachedConfig);
      setError(null);
      setStatus("success");
      return;
    }
    if (cachedError) {
      setConfig(null);
      setError(cachedError);
      setStatus("error");
      return;
    }

    setStatus("loading");
    void fetchMapConfigOnce().then(() => {
      if (cachedConfig) {
        setConfig(cachedConfig);
        setError(null);
        setStatus("success");
      } else if (cachedError) {
        setConfig(null);
        setError(cachedError);
        setStatus("error");
      }
    });
  }, []);

  return { config, status, error };
}
