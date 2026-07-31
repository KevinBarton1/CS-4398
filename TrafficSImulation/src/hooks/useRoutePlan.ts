import { FormEvent, useCallback, useEffect, useMemo, useRef, useState } from "react";
import { ApiClientError, postPlan } from "../api/client";
import { defaultScenario, SCENARIO_DEBOUNCE_MS } from "../constants/scenario";
import type { ApiError, Mode, PlanResult, RequestState, Scenario } from "../types";

function isAbortError(error: unknown): boolean {
  return error instanceof DOMException && error.name === "AbortError";
}

function reconcileSelection(
  routes: PlanResult["routes"],
  recommendedRouteId: string,
  previousId: string | undefined,
  preserveSelection: boolean,
): string {
  if (preserveSelection && previousId && routes.some((route) => route.id === previousId)) {
    return previousId;
  }
  return recommendedRouteId;
}

export function useRoutePlan() {
  const [origin, setOrigin] = useState("Downtown Austin");
  const [destination, setDestination] = useState("Austin Airport");
  const [mode, setModeState] = useState<Mode>("simulated");
  const [scenario, setScenarioState] = useState<Scenario>(defaultScenario);
  const [plan, setPlan] = useState<PlanResult | null>(null);
  const [selectedRouteId, setSelectedRouteId] = useState<string | undefined>();
  const [status, setStatus] = useState<RequestState>("idle");
  const [error, setError] = useState<ApiError | null>(null);

  const abortRef = useRef<AbortController | null>(null);
  const debounceRef = useRef<number | undefined>(undefined);
  const requestIdRef = useRef(0);
  const planRef = useRef<PlanResult | null>(null);
  const originRef = useRef(origin);
  const destinationRef = useRef(destination);
  const modeRef = useRef(mode);
  const scenarioRef = useRef(scenario);
  planRef.current = plan;
  originRef.current = origin;
  destinationRef.current = destination;
  modeRef.current = mode;
  scenarioRef.current = scenario;

  const executePlan = useCallback(async (preserveSelection: boolean) => {
    abortRef.current?.abort();
    const controller = new AbortController();
    abortRef.current = controller;
    const requestId = ++requestIdRef.current;

    setStatus("loading");
    setError(null);

    const currentScenario = scenarioRef.current;

    try {
      const result = await postPlan(
        {
          origin: originRef.current,
          destination: destinationRef.current,
          mode: modeRef.current,
          hour: currentScenario.hour,
          weather: currentScenario.weather,
          congestion: currentScenario.congestion,
        },
        controller.signal,
      );

        if (requestId !== requestIdRef.current) {
          return;
        }

        setPlan(result);
        setSelectedRouteId((current) =>
          reconcileSelection(result.routes, result.recommended_route_id, current, preserveSelection),
        );
        setStatus("success");
      } catch (caught) {
        if (isAbortError(caught) || requestId !== requestIdRef.current) {
          return;
        }

        const apiError =
          caught instanceof ApiClientError
            ? caught.apiError
            : {
                detail: caught instanceof Error ? caught.message : "Unable to calculate routes.",
                code: "unknown_error",
                fields: null,
              };

        setError(apiError);
        setStatus("error");

        const retainedPlan = planRef.current;
        if (retainedPlan) {
          setModeState(retainedPlan.mode);
        }
      }
    },
  []);

  const scheduleReplan = useCallback(
    (preserveSelection: boolean) => {
      window.clearTimeout(debounceRef.current);
      debounceRef.current = window.setTimeout(() => {
        void executePlan(preserveSelection);
      }, SCENARIO_DEBOUNCE_MS);
    },
    [executePlan],
  );

  useEffect(() => {
    void executePlan(false);
    return () => {
      abortRef.current?.abort();
      window.clearTimeout(debounceRef.current);
    };
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const setMode = useCallback(
    (nextMode: Mode) => {
      setModeState(nextMode);
      modeRef.current = nextMode;
      scheduleReplan(true);
    },
    [scheduleReplan],
  );

  const setScenario = useCallback(
    (nextScenario: Scenario) => {
      setScenarioState(nextScenario);
      scenarioRef.current = nextScenario;
      if (modeRef.current === "realtime") {
        return;
      }
      scheduleReplan(true);
    },
    [scheduleReplan],
  );

  const resetScenario = useCallback(() => {
    setScenarioState(defaultScenario);
    scenarioRef.current = defaultScenario;
    if (modeRef.current === "realtime") {
      return;
    }
    scheduleReplan(true);
  }, [scheduleReplan]);

  const submit = useCallback(
    (event?: FormEvent) => {
      event?.preventDefault();
      window.clearTimeout(debounceRef.current);
      void executePlan(false);
    },
    [executePlan],
  );

  const selectRoute = useCallback((id: string) => {
    setSelectedRouteId(id);
  }, []);

  const selectedRoute = useMemo(
    () => plan?.routes.find((route) => route.id === selectedRouteId) ?? plan?.routes[0],
    [plan, selectedRouteId],
  );

  const handleLocation = useCallback(() => {
    navigator.geolocation?.getCurrentPosition(
      () => setOrigin("Current location"),
      () =>
        setError({
          detail: "Location permission was denied. Enter a starting point manually.",
          code: "unknown_error",
          fields: null,
        }),
    );
  }, []);

  const loading = status === "loading";

  return {
    origin,
    setOrigin,
    destination,
    setDestination,
    mode,
    scenario,
    plan,
    selectedRouteId,
    selectedRoute,
    status,
    error,
    loading,
    submit,
    setMode,
    setScenario,
    resetScenario,
    selectRoute,
    handleSubmit: submit,
    handleLocation,
    setSelectedId: selectRoute,
    selectedId: selectedRouteId,
    data: plan,
    message: error?.detail ?? "",
    setMessage: (_message?: string) => setError(null),
    setSelectedRouteId,
  };
}
