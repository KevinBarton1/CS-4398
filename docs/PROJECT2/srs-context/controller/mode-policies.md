# Controller Context — Mode Policies

**Layer:** Controller  
**Target modules:** `TrafficSImulation/app/api/mode_policy.py`, `TrafficSImulation/app/api/planning.py`, `TrafficSImulation/app/api/models.py`  
**Related:** [orchestration.md](orchestration.md), [api-contracts.md](api-contracts.md), [external-service-boundaries.md](external-service-boundaries.md), [../model/weather-scenarios.md](../model/weather-scenarios.md), [../view/route-scenario-forms.md](../view/route-scenario-forms.md), [../architecture/state-diagrams.md](../architecture/state-diagrams.md)

## Purpose

Confine every difference between Simulated and Real-Time planning to one small module. `ModePolicy`
turns the mode from a string that many modules might inspect into an object that answers a fixed set of
questions. Orchestration asks; nothing else branches.

## Requirements

| ID | Requirement | Status | Phase |
|----|-------------|--------|-------|
| FR-2.2 | Simulated mode returns up to three alternatives with distinct names and objectives | Target | P1 |
| FR-2.3 | Real-Time mode returns exactly one alternative | Target | P1 |
| FR-2.6 | `adjusted_eta_minutes` is computed by the active mode policy | Target | P1 |
| FR-2.9 | Each mode stamps a distinct `data_source` on every route | Target | P1 |
| FR-4.1 | The mode switch offers exactly two options labeled `Simulated` and `Real-Time` | Target | P1 |
| FR-4.3 | `scenario_applied` declares whether scenario inputs were applied | Target | P1 |
| FR-4.4 | Real-Time mode hides the scenario controls and explains that comparison is Simulated-only | Target | P1 |
| FR-4.5 | The response carries a mode-specific `notice` | Target | P1 |
| FR-5.7 | The response echoes the effective scenario actually used | Target | P1 |
| FR-6.2 | `price_factors.time_multiplier` is always present, including when it is `1.0` | Target | P1 |
| NFR-5.5 | Branching on the planning mode occurs only in `app/api/mode_policy.py` | Target | P1 |
| NFR-6.3 | The default test suite exercises each policy without HTTP and without live Google calls | Target | P1 |
| NFR-7.1 | Both modes carry a non-empty provenance `notice` | Target | P1 |
| NFR-7.3 | Each route states its provenance through `data_source`, surfaced by the View | Target | P1 |
| NFR-7.5 | A control with no effect in the active mode is hidden with an explanation | Target | P1 |
| FR-4.6 | Persisting the selected mode across reloads, or deep-linking a mode and trip | Out of scope | — |
| FR-5.8 | Named or saved scenario presets, including per-mode presets | Out of scope | — |
| — | Any third planning mode | Out of scope | — |

## The `ModePolicy` Abstraction

`app/api/mode_policy.py` declares one abstract base and two concrete implementations, plus a single
resolver function. Nothing in the module performs I/O, so every policy is testable with plain
assertions.

```python
class ModePolicy(ABC):
    wire_value: str
    scenario_applied: bool
    data_source: str
    notice: str

    @abstractmethod
    def effective_scenario(self, request: PlanRequest) -> Scenario:
        ...

    @abstractmethod
    def routing_options(self, scenario: Scenario) -> RoutingOptions:
        ...

    @abstractmethod
    def adjusted_eta_minutes(
        self,
        duration_minutes: float,
        weather: WeatherState,
    ) -> float:
        ...

    @abstractmethod
    def pricing_time_multiplier(self, scenario: Scenario) -> float:
        ...
```

| Member | Contract |
|--------|----------|
| `wire_value` | The literal that appears in requests and in the response `mode` field |
| `scenario_applied` | Class-level constant copied to the response field of the same name |
| `data_source` | Provenance label stamped on every `RouteOption` |
| `notice` | Verbatim sentence copied to the response `notice` field |
| `effective_scenario()` | Produces the `Scenario` actually used, from the validated request |
| `routing_options()` | Produces departure time, alternatives flag, and traffic preference for the Routes gateway |
| `adjusted_eta_minutes()` | Applies the mode's ETA formula to a duration already selected by the fallback chain |
| `pricing_time_multiplier()` | Supplies the fare time factor, `1.0` when the mode applies none |

```python
def resolve_mode_policy(mode: str) -> ModePolicy:
    """Return the policy for a validated mode value."""
```

`resolve_mode_policy()` is a lookup over a module-level mapping, not a chain of `if` statements. It
receives an already-validated value, because `PlanRequest` rejects anything outside the two literals
with a 422 before orchestration runs. An unmapped key is therefore a programming error and raises
rather than defaulting to Simulated; silently defaulting would let a typo return scenario-driven
numbers to a user who asked for live traffic.

## Mode Comparison

| Aspect | Simulated | Real-Time |
|--------|-----------|-----------|
| Wire value | `simulated` | `realtime` |
| UI label | `Simulated` | `Real-Time` |
| Policy class | `SimulatedModePolicy` | `RealTimeModePolicy` |
| Alternatives requested | Yes; up to 3 returned | No; exactly 1 returned |
| Scenario handling | Request values pass through unchanged | Request values accepted, then discarded |
| Effective `scenario.hour` | Request `hour` | Current local Austin hour |
| Effective `scenario.weather` | Request `weather` | `0` |
| Effective `scenario.congestion` | Request `congestion` | `0` |
| Departure time | Next occurrence of `scenario.hour`, local Austin time | Now |
| Routing preference | Traffic-aware for the chosen departure hour | Traffic-aware for the current departure time |
| Weather applied to ETA | Yes, `weather.time_multiplier` | No |
| Time-of-day factor in ETA | No | No |
| Time-of-day factor in fare | No; `price_factors.time_multiplier` is `1.0` | Yes; `time_of_day_factor(departure hour)` |
| Adjusted ETA formula | `duration_seconds / 60 * weather.time_multiplier` | `duration_seconds / 60` |
| `data_source` | `Google Routes with departure-hour traffic` | `Google Routes with live traffic` |
| `scenario_applied` | `true` | `false` |
| Inert UI panels | None | Scenario controls, and route comparison ranking |
| Presentation of inert panels | — | Hidden with an explanation, never rendered in a silently disabled state |
| Idempotent for identical requests | Yes | No; departure time and live traffic move |

### Notice strings

| Mode | `notice` |
|------|----------|
| Simulated | `Simulated mode: Google Maps supplies route geometry and departure-hour traffic; scenario controls adjust planning estimates.` |
| Real-Time | `Real-Time mode: route, distance, and travel time come from Google Maps traffic-aware routing for the current departure time.` |

Both strings are class constants on their policy. They are never assembled at runtime, never
translated, and never edited in the View. A test compares them byte for byte, because the difference
between the two sentences is the product's honesty about where its numbers come from.

## Why Real-Time Applies No Weather Factor

Google's traffic-aware duration for the current departure time already reflects conditions on the road,
including whatever slowdown current weather is causing. Multiplying it by a simulated weather factor
would count the same effect twice and inflate a number the UI presents as live. Real-Time therefore
reports `weather.severity` `0` with `time_multiplier` `1.0`, and the weather panel shows a clear state
rather than a stale simulated one.

Simulated mode has the opposite problem and the opposite answer. Its departure hour may be far from
now, so Google's departure-hour traffic is a forecast rather than an observation, and the scenario's
weather severity is the user's stated hypothesis. Applying `weather.time_multiplier` there is the whole
point of the mode.

The pricing time-of-day factor splits the other way. In Simulated mode the user has already expressed
time preference by choosing `hour`, and the congestion control carries the surcharge intent, so an
additional hour-based factor would be a hidden second knob. In Real-Time mode the user chose nothing,
so `time_of_day_factor(departure hour)` is the only signal that a fare at 08:00 differs from one at
02:00.

## Mode Is the Only Branch Point

Exactly one expression in the Controller depends on the mode string: the `resolve_mode_policy()` lookup
in `app/api/planning.py`. After that call, orchestration holds a policy object and asks it questions.

| Module | Rule |
|--------|------|
| `app/api/planning.py` | Calls `resolve_mode_policy()` once; contains no other mode comparison |
| `app/api/routes.py` | Passes the validated request through; never inspects `mode` |
| `app/api/models.py` | Constrains `mode` to the two literals; assigns it no behavior |
| `app/map/places.py` | Mode-unaware; resolves text to a place |
| `app/map/routing.py` | Mode-unaware; receives departure time, alternatives flag, and traffic preference as parameters |
| `app/simulation/*` | Mode-unaware; receives scenario values as parameters |
| `app/pricing/model.py` | Mode-unaware; receives a time multiplier as a parameter |
| `app/weather/service.py` | Mode-unaware; receives a severity as a parameter |

The Model receives decisions, never the mode that produced them. `GoogleRoutesGateway.compute_routes()`
takes `departure_time`, `compute_alternatives`, and `routing_preference`; it must not take a `mode`
argument. `PricingModel.estimate()` takes `time_multiplier`; it must not take a `mode` argument. A
`mode ==` comparison anywhere under `app/map/`, `app/simulation/`, `app/pricing/`, or `app/weather/` is
a review-blocking defect, and an architecture test asserts their absence.

The View has one legitimate mode branch of its own: whether to render the scenario controls. That is a
presentation decision about inert inputs, not a planning decision, and it never changes what the View
sends. The client always submits all six request fields; the server decides what to use.

## Real-Time Mode in the View

| Element | Behavior in Real-Time mode |
|---------|----------------------------|
| `ScenarioControls.tsx` | Not rendered; replaced by a short line explaining that live traffic supplies these values |
| Scenario values in View state | Retained in component state so switching back to Simulated restores the user's settings |
| `RouteOptionList.tsx` | Shows a single route card with no comparison ranking, and states that comparison is a Simulated-mode capability |
| `AnalysisPanel.tsx` | Reports weather as clear from the response rather than from local state |
| `PriceSummary.tsx` | Shows a time-of-day factor above `1.0` when the current hour warrants it |
| `StatusBanner.tsx` | Shows the Real-Time `notice` verbatim |

Hiding is deliberate rather than disabling. A disabled slider still occupies the accessibility tree and
invites a user to try it, so the scenario controls are removed and their absence is explained in text,
per NFR-7.5 and [../view/accessibility.md](../view/accessibility.md). The values behind them survive in
View state, so a mode round trip is lossless even though nothing is rendered.

The request body is unaffected either way. The client always sends all six fields, and the server
decides what to use. Panels report effectiveness from the response `scenario`, never from local state,
which is why `scenario` is populated even when `scenario_applied` is `false`.

## Adding a Mode

A third mode is out of scope for PROJECT2. If that ever changes, the cost is bounded to five edits:
add the literal to the `mode` constraint in `app/api/models.py`, add a `ModePolicy` subclass, register
it in the `resolve_mode_policy()` mapping, add its label to the TypeScript union in `src/types.ts`, and
add its policy unit tests. No change to `PlanningService`, to any Model module, or to any other
Controller file should be required. If a proposed mode cannot be expressed as one policy subclass, the
abstraction is wrong and needs revisiting before the mode is added.

## Acceptance Criteria

- [ ] `resolve_mode_policy("simulated")` returns `SimulatedModePolicy` and `resolve_mode_policy("realtime")` returns `RealTimeModePolicy`.
- [ ] An unmapped mode value raises rather than defaulting to Simulated.
- [ ] `SimulatedModePolicy.effective_scenario()` returns the request `hour`, `weather`, and `congestion` unchanged.
- [ ] `RealTimeModePolicy.effective_scenario()` returns the current local Austin hour with `weather` `0` and `congestion` `0`, whatever the request contained.
- [ ] Simulated `routing_options()` requests alternatives and a departure time at the next occurrence of `scenario.hour`.
- [ ] Real-Time `routing_options()` requests no alternatives and a departure time of now.
- [ ] Simulated `adjusted_eta_minutes()` multiplies by `weather.time_multiplier`; Real-Time applies no factor.
- [ ] Simulated `pricing_time_multiplier()` returns `1.0`; Real-Time returns `time_of_day_factor(departure hour)`.
- [ ] `data_source`, `notice`, and `scenario_applied` match the tables above exactly for both modes.
- [ ] No module under `app/map/`, `app/simulation/`, `app/pricing/`, or `app/weather/` compares against `simulated` or `realtime`.
- [ ] `app/api/planning.py` contains exactly one mode-dependent expression.
- [ ] Scenario controls are absent from the accessibility tree in Real-Time mode, their absence is explained in text, and their values return intact when the user switches back to Simulated.

## Planned Tests

| Test ID | Level | Target file | Assertion |
|---------|-------|-------------|-----------|
| T-22 | unit | `tests/test_mode_policy.py` | Each policy reports the documented alternatives count, scenario handling, routing preference, and notice; `resolve_mode_policy()` maps both literals and raises on anything else; Real-Time `effective_scenario()` discards request scenario values and reports the current Austin hour with weather 0 and congestion 0; Simulated departure time is the next occurrence of `scenario.hour` while Real-Time departure time is now; `adjusted_eta_minutes()` applies the weather factor in Simulated mode only; and `pricing_time_multiplier()` is `1.0` in Simulated mode and the time-of-day factor in Real-Time mode |
| T-28 | component | `src/App.test.tsx` | Switching to Real-Time removes the scenario controls from the accessibility tree, renders one route, and restores the values on switching back |
| T-46 | unit | `tests/test_architecture.py` | No module under `app/map/`, `app/simulation/`, `app/pricing/`, or `app/weather/` contains the mode literals |
| T-02 | api | `tests/test_api.py` | A Real-Time request carrying scenario fields returns `scenario_applied` `false` with weather 0 and congestion 0 |

## Agent Implementation Notes

- Put `data_source`, `notice`, `scenario_applied`, and `wire_value` on the policy classes as constants. Duplicating them in `app/api/planning.py` reintroduces the branching this module exists to remove.
- Compute the Austin local hour and the Simulated departure timestamp inside the policy with an explicit timezone. Never use a naive `datetime.now()`; a UTC-versus-local slip shifts every departure-hour plan by several hours.
- When the Simulated departure hour has already passed today, roll forward to tomorrow so the request always targets a future departure time.
- Give the policy the duration in minutes that the fallback chain already selected. Duration-source selection belongs to orchestration, formula application belongs to the policy.
- Real-Time truncation to one alternative comes from asking the Routes gateway for no alternatives, not from slicing a longer list after the fact. Slicing wastes quota and hides the intent.
- If a mode ever needs a value the base class does not expose, add an abstract member to `ModePolicy` and implement it in both subclasses. Do not let orchestration reach for a subclass-specific attribute.
- Keep the two notice strings in one place and assert them verbatim. They are user-facing provenance claims, not incidental copy.
