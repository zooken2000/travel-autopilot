"""Travel Autopilot web app.

Run:  uvicorn app.main:app --reload
"""

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse

from app.api.routes import ensure_runtime_state, router

FRONTEND = Path(__file__).resolve().parents[1] / "frontend" / "index.html"


@asynccontextmanager
async def lifespan(app: FastAPI):
    ensure_runtime_state()
    yield


app = FastAPI(title="Travel Autopilot", lifespan=lifespan)
app.include_router(router)


@app.get("/")
def index() -> FileResponse:
    return FileResponse(FRONTEND)
