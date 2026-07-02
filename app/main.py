"""FastAPI application factory and startup."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from app.api.routes import router
from app.core.config import settings
from app.services.pipeline import RankingPipeline

# ── Global pipeline instance ──────────────────────────────────────
pipeline: RankingPipeline | None = None


def get_pipeline() -> RankingPipeline:
    """Get the global pipeline instance."""
    global pipeline
    if pipeline is None:
        pipeline = RankingPipeline()
    return pipeline


def set_pipeline(p: RankingPipeline) -> None:
    """Set the global pipeline instance (used by run.py after initial ranking)."""
    global pipeline
    pipeline = p


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    logger.info("FastAPI starting up │ {}:{}", settings.api_host, settings.api_port)
    get_pipeline()  # Initialize pipeline on startup
    yield
    logger.info("FastAPI shutting down")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title=settings.api_title,
        version=settings.api_version,
        description=settings.api_description,
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register routes
    app.include_router(router)

    return app


# ── App instance for uvicorn ──────────────────────────────────────
app = create_app()
