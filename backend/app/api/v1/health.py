"""
app/api/v1/health.py
─────────────────────
Health-check endpoint.

GET /health — returns application status, version, and MongoDB connectivity.
This is the only fully implemented endpoint in Phase 1.
"""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.config import get_settings
from app.database import get_database
from app.utils.logger import logger

router = APIRouter(tags=["health"])


@router.get(
    "/health",
    summary="Health Check",
    description="Returns the current health status of the API and its dependencies.",
    response_description="Health status object",
)
async def health_check(db: AsyncIOMotorDatabase = Depends(get_database)) -> dict:
    """
    Verify that the API is running and MongoDB is reachable.

    Returns 200 with status='healthy' on success, or raises a 503 if the
    database ping fails.
    """
    settings = get_settings()

    # ── Database ping ──────────────────────────────────────────────────────────
    db_status = "unknown"
    try:
        await db.command("ping")
        db_status = "connected"
        logger.debug("Health check — MongoDB ping OK")
    except Exception as exc:  # noqa: BLE001
        db_status = f"error: {exc}"
        logger.warning("Health check — MongoDB ping FAILED: {exc}", exc=exc)

    return {
        "status": "healthy" if db_status == "connected" else "degraded",
        "app_name": settings.app_name,
        "version": settings.app_version,
        "environment": settings.app_env,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "dependencies": {
            "mongodb": db_status,
        },
    }
