"""
app/api/routes/health.py
─────────────────────────
Health check endpoint returning FastAPI server status and database connectivity status.
"""

from __future__ import annotations

from datetime import datetime, timezone
from fastapi import APIRouter
from app.database.database import db_manager
from app.utils.bson import format_response

router = APIRouter(prefix="/health", tags=["health"])


@router.get("")
async def health_check() -> dict:
    """
    Check API service and MongoDB connection health status.
    """
    db_ok = await db_manager.ping()
    db_info = await db_manager.get_server_info() if db_ok else {"error": "database unreachable"}

    status_str = "healthy" if db_ok else "degraded"
    
    return format_response(
        success=db_ok,
        message=f"System health is {status_str}",
        data={
            "status": status_str,
            "timestamp": datetime.now(tz=timezone.utc).isoformat(),
            "database": {
                "connected": db_ok,
                "info": db_info,
            }
        }
    )
