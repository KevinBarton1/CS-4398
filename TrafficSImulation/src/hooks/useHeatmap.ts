import { useEffect, useState } from "react";
import { ApiClientError, postHeatmap } from "../api/client";
import type { HeatmapResult, RequestState } from "../types";

function isAbortError(error: unknown): boolean {
  return error instanceof DOMException && error.name === "AbortError";
}

export function useHeatmap(hour: number, congestion: number, enabled: boolean) {
  const [data, setData] = useState<HeatmapResult | null>(null);
  const [status, setStatus] = useState<RequestState>("idle");

  useEffect(() => {
    if (!enabled) {
      setStatus("idle");
      return undefined;
    }

    const controller = new AbortController();
    setStatus("loading");

    void postHeatmap({ hour, congestion }, controller.signal)
      .then((result) => {
        if (controller.signal.aborted) {
          return;
        }
        setData(result);
        setStatus("success");
      })
      .catch((error) => {
        if (isAbortError(error) || controller.signal.aborted) {
          return;
        }
        setStatus("error");
        if (error instanceof ApiClientError) {
          console.error(error.apiError.detail);
        }
      });

    return () => {
      controller.abort();
    };
  }, [hour, congestion, enabled]);

  return { data, status };
}
