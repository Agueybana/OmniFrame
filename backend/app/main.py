from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .models import FeedbackRequest, FeedbackResponse, GoalRequest, RouteResponse
from .services.frameworks import load_framework_catalog
from .services.router import route_goal
from .services.wisdom_graph import store_feedback


app = FastAPI(title="OmniFrame API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "omniframe"}


@app.get("/api/frameworks")
def frameworks() -> list[dict]:
    return load_framework_catalog()


@app.post("/api/route", response_model=RouteResponse)
async def route(request: GoalRequest) -> dict:
    return await route_goal(request.goal)


@app.post("/api/feedback", response_model=FeedbackResponse)
def feedback(request: FeedbackRequest) -> FeedbackResponse:
    return FeedbackResponse(event_id=store_feedback(request), stored=True)


DIST_DIR = Path(__file__).resolve().parents[2] / "dist"
if DIST_DIR.exists():
    app.mount("/assets", StaticFiles(directory=DIST_DIR / "assets"), name="assets")


@app.get("/{path:path}", include_in_schema=False)
def serve_frontend(path: str) -> FileResponse:
    index_file = DIST_DIR / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    return FileResponse(Path(__file__).resolve().parent / "fallback.html")

