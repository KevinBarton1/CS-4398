import logging
from contextlib import asynccontextmanager
from pathlib import Path

import httpx
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api.errors import register_exception_handlers
from app.api.routes import router
from app.config import settings
from app.map.health import GoogleApiProbe, ProbeResult
from app.map.place_cache import PlaceResolutionCache

ROOT = Path(__file__).resolve().parent
STATIC = ROOT / "dist"
PORT = 8000
logger = logging.getLogger(__name__)


def create_app(
    *,
    app_settings=None,
    http_client: httpx.AsyncClient | None = None,
    probe_result: ProbeResult | None = None,
    static_dir: Path | None = None,
) -> FastAPI:
    resolved_settings = app_settings or settings
    dist = static_dir if static_dir is not None else STATIC

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        owns_client = http_client is None
        client = http_client or httpx.AsyncClient()
        app.state.http_client = client
        app.state.settings = resolved_settings
        app.state.place_cache = PlaceResolutionCache()
        if probe_result is not None:
            app.state.probe_result = probe_result
        else:
            probe = GoogleApiProbe(resolved_settings, client)
            result = await probe.check()
            app.state.probe_result = result
            if not result.ok and resolved_settings.google_maps_configured:
                logger.warning("Google API probe failed: %s", result.message)
        try:
            yield
        finally:
            if owns_client:
                await client.aclose()

    application = FastAPI(
        title="TrafficScope API",
        version="2.0",
        description=(
            "Typed controller for the distributed traffic and "
            "rideshare planning simulation."
        ),
        lifespan=lifespan,
    )
    register_exception_handlers(application)
    application.include_router(router)
    _mount_static(application, dist)
    return application


def _mount_static(app: FastAPI, dist: Path) -> None:
    if not dist.exists():
        logger.warning(
            "Frontend build missing at %s. Run `npm install` and `npm run build`.",
            dist,
        )
        return

    assets = dist / "assets"
    if assets.is_dir():
        app.mount("/assets", StaticFiles(directory=assets), name="assets")

    dist_resolved = dist.resolve()

    @app.get("/{path:path}")
    async def spa(path: str):
        if not path:
            return FileResponse(dist / "index.html")

        if ".." in Path(path).parts:
            raise HTTPException(status_code=404, detail="Not found")

        candidate = (dist / path).resolve()
        try:
            candidate.relative_to(dist_resolved)
        except ValueError:
            raise HTTPException(status_code=404, detail="Not found") from None

        if candidate.is_file():
            return FileResponse(candidate)
        return FileResponse(dist / "index.html")


app = create_app()


def main():
    if not STATIC.exists():
        print("Frontend build missing. Run `npm install` and `npm run build` first.")
    uvicorn.run("main:app", host="127.0.0.1", port=PORT, reload=False)


if __name__ == "__main__":
    main()
