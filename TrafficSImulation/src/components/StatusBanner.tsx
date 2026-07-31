import type { ApiError, ApiErrorCode } from "../types";

export type StatusBannerVariant = "loading" | "empty" | "error";

export const LOADING_MESSAGE = "Planning your route...";
export const EMPTY_MESSAGE = "No route alternatives came back for this trip.";
export const CONNECTIVITY_GUIDANCE =
  "Could not reach TrafficScope. Check your connection and try again.";
export const GENERIC_ERROR_GUIDANCE =
  "Review the message above and try again, or change your trip details.";

const ERROR_GUIDANCE: Record<Exclude<ApiErrorCode, null>, string> = {
  validation_error: "Correct the highlighted fields and plan again.",
  invalid_location:
    "Try a nearby landmark, a full street address, or one of the suggested Austin places.",
  same_origin_destination: "Choose a destination that differs from the starting point.",
  no_route_found: "No driving route connects these two places. Try a different destination.",
  maps_not_configured:
    "The server is missing its Google Maps credential. An administrator has to configure it before planning works.",
  upstream_unavailable:
    "Google Maps did not answer successfully. Your inputs are unchanged; try again in a moment.",
  upstream_timeout:
    "Google Maps took too long to answer. Try again, and move the scenario sliders in fewer, larger steps if this repeats.",
};

const RETRY_CODES = new Set<ApiErrorCode | "empty">([
  null,
  "maps_not_configured",
  "upstream_unavailable",
  "upstream_timeout",
  "empty",
]);

export function getErrorGuidance(code: ApiErrorCode): string {
  if (code === null) {
    return CONNECTIVITY_GUIDANCE;
  }
  return ERROR_GUIDANCE[code] ?? GENERIC_ERROR_GUIDANCE;
}

export function shouldOfferRetry(code: ApiErrorCode | "empty"): boolean {
  return RETRY_CODES.has(code);
}

export function shouldShowPlanErrorAsToast(error: ApiError, hasPriorPlan: boolean): boolean {
  if (!hasPriorPlan) {
    return false;
  }
  return (
    error.code === null ||
    error.code === "upstream_unavailable" ||
    error.code === "upstream_timeout"
  );
}

interface StatusBannerProps {
  variant: StatusBannerVariant;
  error?: ApiError | null;
  onRetry?: () => void;
  region?: "planner" | "map" | "analysis";
  /** When set, overrides the default detail for error variant (e.g. map script load failure). */
  detail?: string;
  /** When set, overrides the default guidance sentence. */
  guidance?: string;
}

function resolveDetail(variant: StatusBannerVariant, error: ApiError | null | undefined, detail?: string): string {
  if (detail) {
    return detail;
  }
  if (variant === "loading") {
    return LOADING_MESSAGE;
  }
  if (variant === "empty") {
    return EMPTY_MESSAGE;
  }
  return error?.detail ?? "Request failed.";
}

function resolveGuidance(
  variant: StatusBannerVariant,
  error: ApiError | null | undefined,
): string | null {
  if (variant === "loading") {
    return null;
  }
  if (variant === "empty") {
    return "Try planning again, or adjust your starting point and destination.";
  }
  if (variant === "error") {
    return getErrorGuidance(error?.code ?? null);
  }
  return null;
}

function resolveRetry(
  variant: StatusBannerVariant,
  error: ApiError | null | undefined,
  onRetry?: () => void,
): (() => void) | undefined {
  if (!onRetry) {
    return undefined;
  }
  if (variant === "empty") {
    return onRetry;
  }
  if (variant === "error") {
    return shouldOfferRetry(error?.code ?? null) ? onRetry : undefined;
  }
  return undefined;
}

export function StatusBanner({
  variant,
  error = null,
  onRetry,
  region = "planner",
  detail: detailOverride,
  guidance: guidanceOverride,
}: StatusBannerProps) {
  const detail = resolveDetail(variant, error, detailOverride);
  const guidance = guidanceOverride ?? resolveGuidance(variant, error);
  const visibleGuidance = guidance && guidance !== detail ? guidance : null;
  const retryAction = resolveRetry(variant, error, onRetry);
  const isError = variant === "error";
  const role = isError ? "alert" : "status";
  const regionClass = region === "map" ? "status-banner" : "status-banner status-banner--inline";

  return (
    <div
      className={regionClass}
      role={role}
      aria-live="polite"
      aria-atomic="true"
      aria-label={`${region} status`}
    >
      <p className="status-banner__detail">{detail}</p>
      {visibleGuidance ? <p className="status-banner__guidance">{visibleGuidance}</p> : null}
      {variant === "error" && error?.code === "validation_error" && error.fields?.length ? (
        <ul className="status-banner__fields">
          {error.fields.map((entry) => (
            <li key={`${entry.field}-${entry.message}`}>
              <strong>{entry.field}</strong>: {entry.message}
            </li>
          ))}
        </ul>
      ) : null}
      {retryAction ? (
        <button type="button" className="link-button status-banner__retry" onClick={retryAction}>
          Retry
        </button>
      ) : null}
    </div>
  );
}
