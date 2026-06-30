"""
app/database/init_db.py
────────────────────────
Database initialization entry point.

Responsibilities:
  1. Connect to MongoDB Atlas via ``db_manager.connect()``
  2. Create the four application collections if they don't exist
  3. Create all indexes via ``create_all_indexes()``

Called from two places:
  • FastAPI ``lifespan`` context manager in ``main.py`` (automatic)
  • Standalone CLI: ``python -m app.database.init_db``

Usage (standalone):
    cd backend
    python -m app.database.init_db
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

from app.database.collections import ALL_COLLECTIONS
from app.database.database import db_manager
from app.database.indexes import create_all_indexes
from app.utils.logger import configure_logging, logger


# ── Collection creation ────────────────────────────────────────────────────────

async def create_collections_if_missing() -> None:
    """
    Explicitly create each collection if it does not already exist.

    MongoDB creates collections implicitly on the first write, but explicit
    creation lets us later add schema validation or capped-collection options
    without touching application code.
    """
    db = db_manager.db
    existing: set[str] = set(await db.list_collection_names())

    logger.info("Checking collections...")
    for name in ALL_COLLECTIONS:
        if name not in existing:
            await db.create_collection(name)
            logger.info("  [OK] Created collection  : {name}", name=name)
        else:
            logger.info("  [OK] Already exists      : {name}", name=name)


# ── Primary init function ──────────────────────────────────────────────────────

async def init_db() -> None:
    """
    Full initialization sequence for the database layer.

    Order:
        1. Open Motor connection + ping Atlas
        2. Create missing collections
        3. Create / verify indexes

    Called by the FastAPI ``lifespan`` on startup.
    """
    logger.info("=" * 60)
    logger.info("  Initializing Product Sentiment DB")
    logger.info("=" * 60)

    try:
        await db_manager.connect()
        await create_collections_if_missing()
        await create_all_indexes()
        logger.info("=" * 60)
        logger.info("  [OK] Database ready: product_sentiment_db")
        logger.info("=" * 60)
    except Exception as exc:
        logger.error("=" * 60)
        logger.error(f"  [FAIL] Database connection failed on startup: {str(exc)}")
        logger.error("  The server will start up in degraded/offline mode.")
        logger.error("=" * 60)


# ── Shutdown function ──────────────────────────────────────────────────────────

async def shutdown_db() -> None:
    """
    Gracefully close the Motor connection pool.
    Called by the FastAPI ``lifespan`` on shutdown.
    """
    await db_manager.close()


# ── Standalone entry point ─────────────────────────────────────────────────────

async def _run_standalone() -> None:
    """Run init_db and print a success summary to stdout."""
    configure_logging()

    try:
        await init_db()
        settings_info = {
            "mongodb_db": db_manager.db.name,
            "collections": ALL_COLLECTIONS,
        }
        print("\n" + "=" * 60)
        print("  DATABASE INITIALIZATION COMPLETE")
        print("=" * 60)
        print(f"  Database : {settings_info['mongodb_db']}")
        print(f"  Collections ({len(ALL_COLLECTIONS)}):")
        for col in settings_info["collections"]:
            print(f"    • {col}")
        print("=" * 60 + "\n")
    except Exception as exc:
        print(f"\n❌ Initialization FAILED: {exc}", file=sys.stderr)
        sys.exit(1)
    finally:
        await shutdown_db()


if __name__ == "__main__":
    # Allow: python -m app.database.init_db
    asyncio.run(_run_standalone())
