from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

from dotenv import load_dotenv

load_dotenv()  # Load .env into os.environ before any SDK clients are instantiated

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from config.settings import settings
from gateway.limiter import limiter
from gateway.routes import router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings.ensure_dirs()
    from db.database import init_db

    init_db()
    yield


app = FastAPI(
    title="SignalHarvest AI",
    description="Autonomous agentic lead intelligence system",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)  # type: ignore[arg-type]

app.add_middleware(
    CORSMiddleware,
    # No browser is meant to call this API directly — the frontend's
    # server-side proxy holds the API key and isn't subject to CORS at all.
    # This only matters as defense-in-depth; keep it scoped to known
    # frontend origins instead of "*".
    allow_origins=settings.allowed_origins_list,
    allow_methods=["GET", "POST", "PATCH", "DELETE"],
    allow_headers=["*"],
)

app.include_router(router)


@app.get("/health")
async def health() -> dict[str, Any]:
    return {"status": "ok", "service": "signalharvest-ai"}
