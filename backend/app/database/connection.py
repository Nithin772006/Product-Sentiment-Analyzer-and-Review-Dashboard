"""
app/database/connection.py
──────────────────────────
MongoDB async connection management using Motor.

Supports both local MongoDB instances and MongoDB Atlas (SRV connection strings).
Atlas-specific options (TLS, retryWrites, connection timeouts) are automatically
applied when an `mongodb+srv://` URI is detected.

Usage:
    from app.database.connection import get_database

    async def some_endpoint(db = Depends(get_database)):
        collection = db["products"]
        ...

The motor client is created once at application startup (lifespan) and
gracefully closed on shutdown — avoiding connection leaks.
"""

from __future__ import annotations

import re
from typing import AsyncGenerator

import motor.motor_asyncio
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from app.config import get_settings
from app.utils.logger import logger

# Module-level client — initialised in `connect_to_mongo`
_client: AsyncIOMotorClient | None = None


def _mask_uri(uri: str) -> str:
    """
    Replace the password in a MongoDB URI with '***' for safe log output.

    mongodb+srv://user:password@host → mongodb+srv://user:***@host
    """
    return re.sub(r"(?<=://)[^:]+:[^@]+(?=@)", "***:***", uri)


async def connect_to_mongo() -> None:
    """
    Open the Motor async client.
    Automatically detects Atlas SRV URIs and applies appropriate options.
    Called during FastAPI `lifespan` startup.
    """
    global _client
    settings = get_settings()

    is_atlas = settings.mongodb_uri.startswith("mongodb+srv://")
    safe_uri = _mask_uri(settings.mongodb_uri)

    logger.info(
        "Connecting to MongoDB {'Atlas' if is_atlas else 'local'} at {uri} …",
        uri=safe_uri,
    )

    # ── Build client kwargs ───────────────────────────────────────────────────
    client_kwargs: dict = {
        "maxPoolSize": settings.mongodb_max_pool_size,
        "minPoolSize": settings.mongodb_min_pool_size,
        # How long to wait when selecting a server (ms)
        "serverSelectionTimeoutMS": 10_000,
        # How long to wait for a connection to be established (ms)
        "connectTimeoutMS": 10_000,
        # How long to wait for a socket read/write (ms)
        "socketTimeoutMS": 45_000,
    }

    if is_atlas:
        # Atlas requires TLS; retryWrites improves resilience on transient errors
        client_kwargs["tls"] = True
        client_kwargs["retryWrites"] = True
        client_kwargs["w"] = "majority"   # write concern — ensures durability
        logger.info("Atlas mode: TLS=True, retryWrites=True, writeConcern=majority")

    _client = motor.motor_asyncio.AsyncIOMotorClient(
        settings.mongodb_uri,
        **client_kwargs,
    )

    # Verify the connection is reachable before accepting traffic
    try:
        await _client.admin.command("ping")
        logger.info(
            "✅ MongoDB connection established — database: '{db}'",
            db=settings.mongodb_db_name,
        )
    except Exception as exc:
        logger.error("❌ MongoDB connection FAILED: {exc}", exc=exc)
        # Re-raise so FastAPI lifespan aborts cleanly instead of running degraded
        raise


async def close_mongo_connection() -> None:
    """
    Close the Motor async client.
    Called during FastAPI `lifespan` shutdown.
    """
    global _client
    if _client is not None:
        _client.close()
        _client = None
        logger.info("MongoDB connection closed.")


def get_client() -> AsyncIOMotorClient:
    """Return the raw Motor client (use sparingly; prefer `get_database`)."""
    if _client is None:
        raise RuntimeError(
            "MongoDB client is not initialised. "
            "Ensure `connect_to_mongo` is called during application startup."
        )
    return _client


async def get_database() -> AsyncGenerator[AsyncIOMotorDatabase, None]:
    """
    FastAPI dependency that yields the default database.

    Example:
        @router.get("/products")
        async def list_products(db: AsyncIOMotorDatabase = Depends(get_database)):
            ...
    """
    settings = get_settings()
    yield get_client()[settings.mongodb_db_name]
