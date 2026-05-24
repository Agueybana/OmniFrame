from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from alembic import command
from alembic.config import Config
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .db.session import check_database_connection, get_database_url, is_database_configured, reset_engine
from .models import FeedbackRequest, FeedbackResponse, GoalRequest, OptionRefreshRequest, OptionRefreshResponse, RouteResponse
from .routers.persistence import router as persistence_router
from .services.frameworks import load_framework_catalog
from .services.router import refresh_panel_options, route_goal
from .services.wisdom_graph import store_feedback


PROJECT_ROOT = Path(__file__).resolve().parents[2]

load_dotenv(PROJECT_ROOT / ".env")


def run_migrations() -> None:
    database_url = get_database_url()
    if not database_url or database_url.startswith("sqlite"):
        return
    alembic_ini = Path(__file__).resolve().parents[2] / "alembic.ini"
    if not alembic_ini.exists():
        return
    config = Config(str(alembic_ini))
    command.upgrade(config, "head")


@asynccontextmanager
async def lifespan(_: FastAPI):
    reset_engine()
    run_migrations()
    yield


app = FastAPI(title="OmniFrame API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(persistence_router)


@app.get("/api/health")
def health() -> dict[str, str]:
    db_status = "unavailable"
    if is_database_configured():
        db_status = "ok" if check_database_connection() else "unavailable"
    return {"status": "ok", "service": "omniframe", "db": db_status}


@app.get("/api/frameworks")
def frameworks() -> list[dict]:
    return load_framework_catalog()


@app.get("/api/model-options")
def model_options() -> dict:
    return {
        "default": {"provider": "openai", "model": "gpt-5.1"},
        "providers": [
            {
                "id": "openai",
                "name": "OpenAI",
                "models": [
                    {"id": "gpt-5.1", "name": "GPT-5.1", "description": "Default frontier model for deep framework analysis."},
                    {"id": "gpt-5.1-chat-latest", "name": "GPT-5.1 Chat Latest", "description": "Latest chat-tuned GPT-5.1 variant."},
                    {"id": "gpt-5", "name": "GPT-5", "description": "Previous GPT-5 reasoning model."},
                    {"id": "gpt-5-mini", "name": "GPT-5 mini", "description": "Lower-cost GPT-5 family option."},
                ],
            },
            {
                "id": "google",
                "name": "Google Gemini",
                "models": [
                    {"id": "gemini-3.1-pro-preview", "name": "Gemini 3.1 Pro Preview", "description": "Google's latest Gemini 3.1 Pro preview option."},
                    {"id": "gemini-3.1-flash-lite-preview", "name": "Gemini 3.1 Flash-Lite Preview", "description": "Fast, cost-efficient Gemini 3.1 option."},
                    {"id": "gemini-3-pro-preview", "name": "Gemini 3 Pro Preview", "description": "Gemini 3 Pro API preview fallback."},
                ],
            },
        ],
    }


@app.post("/api/route", response_model=RouteResponse)
async def route(request: GoalRequest) -> dict:
    return await route_goal(request.goal, request.framework_id, request.model_provider, request.model_id)


@app.post("/api/options/refresh", response_model=OptionRefreshResponse)
async def refresh_options(request: OptionRefreshRequest) -> dict:
    return await refresh_panel_options(request, request.model_provider, request.model_id)


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
