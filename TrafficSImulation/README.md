# TrafficScope

TrafficScope is a React 19 and FastAPI application for rideshare-style trip planning in Austin, Texas.

## Install

Run all commands from `TrafficSImulation/`.

```powershell
pip install -r requirements.txt
npm install
```

## Configure Google Maps

Copy `.env.example` to `.env`, then provide the two credentials:

```dotenv
GOOGLE_MAPS_API_KEY=your-server-key
GOOGLE_MAPS_BROWSER_API_KEY=your-browser-key
GOOGLE_MAPS_MAP_ID=
```

In Google Cloud Console:

- Restrict `GOOGLE_MAPS_API_KEY` to Places API (New) and Routes API. Apply an IP restriction when the deployment environment permits it. This server credential never reaches the browser.
- Restrict `GOOGLE_MAPS_BROWSER_API_KEY` to the Maps JavaScript API and to the application's HTTP referrer origins.
- `GOOGLE_MAPS_MAP_ID` is optional and is not a credential.

A working server credential is a hard dependency for route planning. TrafficScope has no offline planning path and does not substitute local or fabricated route data when Google services are unavailable.

The real `.env` file is ignored by git.

## Run For Development

Start the backend and frontend in separate terminals:

```powershell
python main.py
```

```powershell
npm run dev
```

Open <http://127.0.0.1:5173>. Vite proxies `/api` requests to FastAPI at `http://127.0.0.1:8000`.

## Test

Run both suites:

```powershell
python -m pytest
npm test
```

The default pytest run excludes tests marked `live`, so tests requiring real external credentials run only when explicitly selected.

## Build And Run For Production

```powershell
npm run build
python main.py
```

Open <http://127.0.0.1:8000>. The production application service serves the built single-page application from `dist/`.
