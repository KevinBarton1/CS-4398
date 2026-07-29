from contextlib import asynccontextmanager
from pathlib import Path

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api.models import PlanRequest
from app.api.routes import plan_route


ROOT = Path(__file__).resolve().parent
STATIC = ROOT / "dist"
PORT = 8000


app = FastAPI(
    title="TrafficScope API",
    version="1.1.0",
    description="Typed controller for the distributed traffic and rideshare planning simulation.",
)


@app.get("/api/health")
def health():
    return {"status": "ok", "service": "TrafficScope", "version": "1.1"}


@app.post("/api/plan")
def plan(request: PlanRequest):
    try:
        return plan_route(request.model_dump())
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


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
