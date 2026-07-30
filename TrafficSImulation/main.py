from contextlib import asynccontextmanager
from pathlib import Path

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api.models import MapEmbedRequest, PlanRequest
from app.api.routes import plan_route
from app.config import GOOGLE_MAPS_API_KEY
from app.map.google_embed import build_map_embed_url
from app.map.google_startup_check import get_startup_status, run_startup_check

ROOT = Path(__file__).resolve().parent
STATIC = ROOT / "dist"
PORT = 8000


@asynccontextmanager
async def lifespan(_: FastAPI):
    status = run_startup_check()
    if status["configured"] and not status["ok"]:
        print("Google Maps is required. Route planning will fail until Places and Routes APIs are reachable.")
    yield


app = FastAPI(
    title="TrafficScope API",
    version="1.1.0",
    description="Typed controller for the distributed traffic and rideshare planning simulation.",
    lifespan=lifespan,
)
@app.get("/api/health")
def health():
    google_maps = get_startup_status()
    return {
        "status": "ok",
        "service": "TrafficScope",
        "version": "1.1",
        "google_maps_configured": bool(GOOGLE_MAPS_API_KEY),
        "google_maps": google_maps,
    }


@app.post("/api/plan")
def plan(request: PlanRequest):
    try:
        return plan_route(request.model_dump())
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@app.post("/api/map/embed")
def map_embed(request: MapEmbedRequest):
    url = build_map_embed_url(request.center_lat, request.center_lng, request.zoom)
    if not url:
        raise HTTPException(status_code=400, detail="GOOGLE_MAPS_API_KEY is not configured.")
    return {"map_embed_url": url}


@app.get("/api/map/config")
def map_config():
    if not GOOGLE_MAPS_API_KEY:
        raise HTTPException(status_code=400, detail="GOOGLE_MAPS_API_KEY is not configured.")
    return {"maps_api_key": GOOGLE_MAPS_API_KEY}


if STATIC.exists():
    app.mount("/assets", StaticFiles(directory=STATIC / "assets"), name="assets")

    @app.get("/{path:path}")
    def spa(path: str):
        candidate = (STATIC / path).resolve()
        if path and STATIC.resolve() in candidate.parents and candidate.is_file():
            return FileResponse(candidate)
        return FileResponse(STATIC / "index.html")


def main():
    if not STATIC.exists():
        print("Frontend build missing. Run `npm install` and `npm run build` first.")
    uvicorn.run("main:app", host="127.0.0.1", port=PORT, reload=False)


if __name__ == "__main__":
    main()
