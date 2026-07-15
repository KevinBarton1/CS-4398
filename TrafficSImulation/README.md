# TrafficScope

TrafficScope is a runnable Version 1.0 prototype of the Distributed Traffic Simulation and Rideshare Driver Planning App described in the project SRS. It compares local route alternatives using deterministic simulated traffic, demand, weather, road-segment statistics, heatmaps, adjusted ETAs, and illustrative upfront prices.

## Run it

On Windows, double-click `start_demo.bat`. It opens <http://127.0.0.1:8000> and uses Python 3 when available. On a machine without Python, it automatically uses the included zero-dependency Node.js fallback.

Manual alternatives:

```powershell
python main.py
# or
npm start
```

Stop the server with `Ctrl+C` in its terminal window.

## Use it

1. Choose an origin and destination. Supported local places include Downtown Austin, UT Austin, Austin Airport, The Domain, Zilker Park, Mueller, South Congress, Round Rock, Cedar Park, East Austin, and Barton Springs.
2. Select a route on the left or directly on the map.
3. Switch the heatmap among Traffic, Demand, Earnings, and Off.
4. Adjust time, weather, congestion, and customer demand. Results refresh automatically.
5. Toggle Reference mode to compare against a stable local baseline. No external API key is required.

## Test it

```powershell
npm test
python -m unittest discover -s tests -p "test_*.py"
```

The Python test command requires Python 3. The Node suite covers route validation, ETA and price modifiers, heatmaps, reference fallback behavior, and road segment generation.

## Architecture

- `main.py` and `app/`: standard-library Python server plus separate routing, weather, simulation, heatmap, pricing, and model modules.
- `static/`: responsive browser interface and SVG map.
- `tools/dev-server.js` and `tools/simulation.js`: zero-dependency fallback runtime for machines without Python.
- `tests/`: Python and Node tests.

Version 1.0 intentionally uses a local Austin-area map model and simulated conditions. It does not call Google Maps, use private rideshare data, store location history, require accounts, or claim official fare accuracy.
