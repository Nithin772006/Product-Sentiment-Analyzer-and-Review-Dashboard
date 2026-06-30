"""
app/database/database.py
─────────────────────────
Singleton MongoDB connection manager using Motor (async driver).

The ``DatabaseManager`` class owns the Motor client lifecycle:
  - ``connect()``   → called at FastAPI startup via ``init_db()``
  - ``close()``     → called at FastAPI shutdown via ``shutdown_db()``
  - ``db``          → returns the active ``AsyncIOMotorDatabase``
  - ``get_collection(name)`` → typed collection accessor

Import the module-level singleton:

    from app.database.database import db_manager

FastAPI dependency:

    from app.database.database import get_database

    @router.get("/products")
    async def list_products(db = Depends(get_database)):
        ...
"""

from __future__ import annotations

import re
from typing import Optional

import motor.motor_asyncio
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorCollection, AsyncIOMotorDatabase
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError

from app.config.settings import get_settings
from app.utils.logger import logger


class DatabaseManager:
    """
    Singleton that manages the Motor async client lifecycle.

    Only one instance of this class should exist in the application
    (the ``db_manager`` module-level variable below).
    """

    def __init__(self) -> None:
        self._client: Optional[AsyncIOMotorClient] = None
        self._db: Optional[AsyncIOMotorDatabase] = None

    # ── Properties ─────────────────────────────────────────────────────────────

    @property
    def client(self) -> AsyncIOMotorClient:
        """Return the Motor client. Raises RuntimeError if not connected."""
        if self._client is None:
            raise RuntimeError(
                "Database client is not initialized. "
                "Ensure connect() was called during application startup."
            )
        return self._client

    @property
    def db(self) -> AsyncIOMotorDatabase:
        """Return the active database. Raises RuntimeError if not connected."""
        if self._db is None:
            raise RuntimeError(
                "Database is not initialized. "
                "Ensure connect() was called during application startup."
            )
        return self._db

    @property
    def is_connected(self) -> bool:
        """Return True if the client is initialized."""
        return self._client is not None

    # ── Lifecycle ──────────────────────────────────────────────────────────────

    async def connect(self) -> None:
        """
        Open the async Motor connection and verify it with a ping.

        Automatically applies Atlas-specific options (TLS, retryWrites,
        majority write concern) when the URI starts with ``mongodb+srv://``.

        Raises:
            ConnectionFailure: Atlas / local MongoDB unreachable.
            ServerSelectionTimeoutError: No server found within timeout.
            RuntimeError: Any other unexpected error.
        """
        settings = get_settings()
        is_atlas = settings.mongodb_uri.startswith("mongodb+srv://")
        safe_uri = _mask_uri(settings.mongodb_uri)
        db_type = "Atlas" if is_atlas else "local MongoDB"

        logger.info(
            "Connecting to {db_type} -> {uri}",
            db_type=db_type,
            uri=safe_uri,
        )

        # ── Build Motor kwargs ────────────────────────────────────────────────
        kwargs: dict = {
            "maxPoolSize": settings.mongodb_max_pool_size,
            "minPoolSize": settings.mongodb_min_pool_size,
            "serverSelectionTimeoutMS": 10_000,
            "connectTimeoutMS": 10_000,
            "socketTimeoutMS": 45_000,
        }

        if is_atlas:
            kwargs["tls"] = True
            kwargs["tlsAllowInvalidCertificates"] = True
            kwargs["retryWrites"] = True
            kwargs["w"] = "majority"
            logger.debug("Atlas mode: TLS=True | tlsAllowInvalidCertificates=True | retryWrites=True | writeConcern=majority")

        try:
            self._client = motor.motor_asyncio.AsyncIOMotorClient(
                settings.mongodb_uri, **kwargs
            )
            # Verify the server is reachable before accepting traffic
            await self._client.admin.command("ping")
            self._db = self._client[settings.mongodb_db_name]
            logger.info(
                "[OK] MongoDB connected | database='{db}' | pool={min}-{max}",
                db=settings.mongodb_db_name,
                min=settings.mongodb_min_pool_size,
                max=settings.mongodb_max_pool_size,
            )
        except (ConnectionFailure, ServerSelectionTimeoutError) as exc:
            logger.error("[FAIL] MongoDB connection FAILED: {exc}", exc=exc)
            self._client = None
            self._db = None
            raise
        except Exception as exc:
            logger.error("[FAIL] Unexpected error during MongoDB connect: {exc}", exc=exc)
            self._client = None
            self._db = None
            raise RuntimeError(f"MongoDB connect error: {exc}") from exc

    async def close(self) -> None:
        """
        Gracefully close the Motor client and release all connections.
        Safe to call even if ``connect()`` was never called.
        """
        if self._client is not None:
            self._client.close()
            self._client = None
            self._db = None
            logger.info("MongoDB connection closed gracefully.")

    # ── Accessors ──────────────────────────────────────────────────────────────

    def get_collection(self, name: str) -> AsyncIOMotorCollection:
        """Return a named collection from the active database."""
        return self.db[name]

    async def ping(self) -> bool:
        """Return True if MongoDB responds to a ping, False otherwise."""
        try:
            await self.client.admin.command("ping")
            return True
        except Exception:
            return False

    async def get_server_info(self) -> dict:
        """Return basic server information for health checks."""
        try:
            info = await self.client.server_info()
            return {
                "version": info.get("version", "unknown"),
                "ok": info.get("ok", 0),
            }
        except Exception as exc:
            return {"error": str(exc)}


# ── Credential masking helper ──────────────────────────────────────────────────

def _mask_uri(uri: str) -> str:
    """Replace credentials in a MongoDB URI with *** for safe log output."""
    return re.sub(r"(?<=://)[^:]+:[^@]+(?=@)", "***:***", uri)


# ── Module-level singleton ─────────────────────────────────────────────────────
db_manager: DatabaseManager = DatabaseManager()


# ── FastAPI dependency ─────────────────────────────────────────────────────────

async def get_database() -> AsyncIOMotorDatabase:
    """
    FastAPI dependency — returns the active Motor database.

    Usage::

        from app.database.database import get_database

        @router.get("/products")
        async def list(db: AsyncIOMotorDatabase = Depends(get_database)):
            docs = await db["products"].find().to_list(20)
            ...
    """
    return db_manager.db
