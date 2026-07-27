# TrafficScope 1.1

TrafficScope is a responsive distributed-traffic simulation and rideshare planning prototype regenerated from SRS Revision 1.1. It provides three objective-based Austin route alternatives, BPR traffic adjustment, scenario controls, demand/traffic/profitability heatmaps, road-segment statistics, and a transparent illustrative planning estimate.

## Run

On Windows, double-click `start_demo.bat`, or run:

```powershell
npm install
npm run build
python main.py
```

Open <http://127.0.0.1:8000>. FastAPI also exposes interactive API documentation at <http://127.0.0.1:8000/docs>.

For frontend development, run the API and Vite in separate terminals:

```powershell
python main.py
npm run dev
```

Vite opens on <http://127.0.0.1:5173> and proxies `/api` requests to FastAPI.

## Test

```powershell
python -m pytest
npm test
npm run build
```

## Architecture

- `src/`: React + TypeScript responsive interface and reusable view components.
- `main.py`: FastAPI controller, typed request validation, static production hosting, and OpenAPI documentation.
- `app/map_service.py`: local geocoding, route geometry, and three documented route objectives.
- `app/traffic_simulator.py`: BPR link timing, road capacity, flow, speed, and heatmap calculations.
- `app/pricing_model.py`: reproducible route subtotal and multiplier breakdown.
- `app/config.py`: centralized formula coefficients and scoring weights.
- `tests/`: backend calculation, API, and frontend behavior tests.

Reference mode uses a stable local baseline when external services are unavailable. All demand, traffic, weather, and fare-like values remain clearly labeled as simulated; no private rideshare data or official fare calculation is claimed.
