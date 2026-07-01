"""
app/main.py
────────────
FastAPI application factory.

Startup sequence (lifespan):
  1. Configure Loguru logging sinks
  2. Connect to MongoDB Atlas and ping
  3. Create missing collections
  4. Create / verify all indexes

Shutdown sequence:
  1. Close Motor connection pool
  2. Flush log file sink

Run (development):
    uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config.settings import get_settings
from app.database.database import db_manager
from app.database.init_db import init_db, shutdown_db
from app.utils.logger import configure_logging, logger


# ── Lifespan (startup / shutdown) ─────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Application lifespan context manager.
    Replaces the deprecated @app.on_event decorators.
    """
    # ── Startup ───────────────────────────────────────────────────────────────
    configure_logging()
    settings = get_settings()

    logger.info(
        "Starting {name} v{version} [{env}]",
        name=settings.app_name,
        version=settings.app_version,
        env=settings.app_env,
    )

    # Initialize DB: connect → create collections → create indexes
    await init_db()

    logger.info("[OK] Application ready - serving requests.")
    yield

    # ── Shutdown ──────────────────────────────────────────────────────────────
    logger.info("Shutting down …")
    await shutdown_db()
    logger.info("Shutdown complete.")


# ── Application factory ────────────────────────────────────────────────────────

def create_app() -> FastAPI:
    """Construct and configure the FastAPI application."""
    settings = get_settings()

    from fastapi.staticfiles import StaticFiles

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description=(
            "REST API for scraping Amazon & Flipkart product reviews, "
            "performing AI-driven sentiment analysis, and visualising insights. "
            "Database: MongoDB Atlas (product_sentiment_db)."
        ),
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    # Mount static folder for serving word cloud images
    import os
    os.makedirs("static/wordclouds", exist_ok=True)
    app.mount("/static", StaticFiles(directory="static"), name="static")

    # ── CORS ──────────────────────────────────────────────────────────────────
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["Content-Disposition", "Content-Length"],
    )

    # ── Root redirect ─────────────────────────────────────────────────────────
    @app.get("/", include_in_schema=False)
    async def root() -> JSONResponse:
        return JSONResponse(
            content={
                "app": settings.app_name,
                "version": settings.app_version,
                "docs": "/docs",
                "health": "/health",
                "api": "/api/v1",
            }
        )

    # ── Health check ──────────────────────────────────────────────────────────
    @app.get("/health", tags=["health"], summary="Health Check")
    async def health_check() -> dict:
        """
        Returns the live status of the API and MongoDB connectivity.
        """
        from datetime import datetime, timezone

        db_ok = await db_manager.ping()
        db_info = await db_manager.get_server_info() if db_ok else {"error": "unreachable"}

        return {
            "status": "healthy" if db_ok else "degraded",
            "app": settings.app_name,
            "version": settings.app_version,
            "environment": settings.app_env,
            "timestamp": datetime.now(tz=timezone.utc).isoformat(),
            "database": {
                "connected": db_ok,
                "name": settings.mongodb_db_name,
                "info": db_info,
            },
        }

    # ── Mount API routers ──────────────────────────────────────────────────────
    from app.api.routes.health import router as health_router
    from app.api.routes.products import router as products_router
    from app.api.routes.reviews import router as reviews_router
    from app.api.routes.sentiments import router as sentiments_router
    from app.api.routes.analytics import router as analytics_router
    from app.api.routes.search import router as search_router
    from app.api.routes.auth import router as auth_router
    from app.api.routes.realtime import router as realtime_router
    from app.api.routes.reports import router as reports_router

    app.include_router(health_router, prefix="/api")
    app.include_router(products_router, prefix="/api")
    app.include_router(reviews_router, prefix="/api")
    app.include_router(sentiments_router, prefix="/api")
    app.include_router(analytics_router, prefix="/api")
    app.include_router(search_router, prefix="/api")
    app.include_router(auth_router, prefix="/api")
    app.include_router(realtime_router, prefix="/api")
    app.include_router(reports_router, prefix="/api")

    return app


# ── Entry point ────────────────────────────────────────────────────────────────
app: FastAPI = create_app()
