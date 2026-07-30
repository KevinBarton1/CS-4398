import { FormEvent, useCallback, useEffect, useMemo, useRef, useState } from "react";
import { defaultScenario } from "../constants/scenario";
import type { Mode, PlanResult, RouteOption, Scenario } from "../types";

export function useRoutePlan() {
  const [origin, setOrigin] = useState("Downtown Austin");
  const [destination, setDestination] = useState("Austin Airport");
  const [mode, setMode] = useState<Mode>("simulated");
  const [scenario, setScenario] = useState<Scenario>(defaultScenario);
  const [data, setData] = useState<PlanResult | null>(null);
  const [selectedId, setSelectedId] = useState<string>();
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");
  const debounce = useRef<number | undefined>(undefined);

  const calculate = useCallback(async (keepSelection = true) => {
    setLoading(true);
    setMessage("");
    try {
      const response = await fetch("/api/plan", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ origin, destination, mode, ...scenario }),
      });
      const result = await response.json();
      if (!response.ok) throw new Error(result.detail || "Route calculation failed.");
      setData(result);
      setSelectedId((current) =>
        keepSelection && result.routes.some((r: RouteOption) => r.id === current)
          ? current
          : result.recommended_route_id
      );
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Unable to calculate routes.");
    } finally {
      setLoading(false);
    }
  }, [origin, destination, mode, scenario]);

  useEffect(() => {
    void calculate(false);
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    if (!data) return;
    window.clearTimeout(debounce.current);
    debounce.current = window.setTimeout(() => void calculate(), 180);
    return () => window.clearTimeout(debounce.current);
  }, [mode]); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    if (!data || mode === "realtime") return;
    window.clearTimeout(debounce.current);
    debounce.current = window.setTimeout(() => void calculate(), 180);
    return () => window.clearTimeout(debounce.current);
  }, [scenario]); // eslint-disable-line react-hooks/exhaustive-deps

  const selectedRoute = useMemo(
    () => data?.routes.find((route) => route.id === selectedId) ?? data?.routes[0],
    [data, selectedId]
  );

  const handleSubmit = (event: FormEvent) => {
    event.preventDefault();
    void calculate(false);
  };

  const handleLocation = () => {
    navigator.geolocation?.getCurrentPosition(
      () => setOrigin("Current location"),
      () => setMessage("Location permission was denied. Enter a starting point manually.")
    );
  };

  const resetScenario = () => setScenario(defaultScenario);

  return {
    origin,
    setOrigin,
    destination,
    setDestination,
    mode,
    setMode,
    scenario,
    setScenario,
    data,
    selectedId,
    setSelectedId,
    selectedRoute,
    loading,
    message,
    setMessage,
    handleSubmit,
    handleLocation,
    resetScenario,
  };
}
