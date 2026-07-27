# Repository Guidelines

## Project Structure & Module Organization

The application lives in `TrafficSImulation/`. Its React 19 + TypeScript interface is in `TrafficSImulation/src/`: `App.tsx` composes the UI, `types.ts` defines shared frontend shapes, and `styles.css` holds the presentation layer. The FastAPI service starts at `TrafficSImulation/main.py`; domain logic belongs in `TrafficSImulation/app/` (`models.py`, `routes.py`, simulation, mapping, pricing, and configuration modules). Tests are split between Python files in `TrafficSImulation/tests/` and colocated Vitest files such as `TrafficSImulation/src/App.test.tsx`.

## Build, Test, and Development Commands

Run commands from `TrafficSImulation/`.

- `npm install` installs frontend dependencies.
- `npm run dev` starts Vite at `http://127.0.0.1:5173` and proxies `/api` to FastAPI.
- `npm run build` type-checks TypeScript and creates the production `dist/` bundle.
- `python main.py` starts FastAPI at `http://127.0.0.1:8000`; build first when serving the production frontend.
- `python -m pytest` runs backend and API tests.
- `npm test` runs the Vitest frontend suite in jsdom.

For local development, run `python main.py` and `npm run dev` in separate terminals. On Windows, `start_demo.bat` performs the documented demo startup flow.

## Coding Style & Naming Conventions

Match the existing code: use four spaces in Python and two spaces in TypeScript/TSX. Keep Python modules and functions in `snake_case`; use `PascalCase` for React components and TypeScript types, and `camelCase` for variables and callbacks. Preserve strict TypeScript typing; define API request and response shapes in the appropriate model/type module rather than passing untyped objects. Keep simulation coefficients centralized in `app/config.py`.

## Testing Guidelines

Add or update tests with behavior changes. Name Python tests `test_<behavior>` in `tests/test_*.py`; name frontend tests `*.test.ts` or `*.test.tsx` beneath `src/`. Cover API status codes and response shape, and verify user-visible React behavior with Testing Library. Run both test commands plus `npm run build` before submitting changes that touch either stack.

## Commit & Pull Request Guidelines

Recent history uses short imperative summaries, for example `Fixed Screen` and `Regenerated using revised SRS`. Use a concise subject that states the change, such as `Add weather validation`. Pull requests should explain the user-facing or simulation impact, list validation performed, link the relevant issue when applicable, and include screenshots for visual UI changes.
