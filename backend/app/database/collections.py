"""
app/database/collections.py
────────────────────────────
Centralised collection name constants and typed collection accessors.

Instead of scattering raw string collection names throughout the codebase,
every module imports from here:

    from app.database.collections import (
        PRODUCTS, REVIEWS, SENTIMENTS, SCRAPE_LOGS,
        get_products_collection,
        ...
    )

This means renaming a collection only requires changing this file.
"""

from __future__ import annotations

from motor.motor_asyncio import AsyncIOMotorCollection

from app.database.database import db_manager


# ── Collection name constants ─────────────────────────────────────────────────

PRODUCTS    = "products"
REVIEWS     = "reviews"
SENTIMENTS  = "sentiments"
SCRAPE_LOGS = "scrape_logs"
USERS       = "users"

ALL_COLLECTIONS: list[str] = [PRODUCTS, REVIEWS, SENTIMENTS, SCRAPE_LOGS, USERS]


# ── Typed collection accessors ─────────────────────────────────────────────────
# Each accessor is a zero-argument function so the collection is fetched
# at call time (after the DB is connected) rather than at import time.

def get_products_collection() -> AsyncIOMotorCollection:
    """Return the ``products`` collection from the active database."""
    return db_manager.get_collection(PRODUCTS)


def get_reviews_collection() -> AsyncIOMotorCollection:
    """Return the ``reviews`` collection from the active database."""
    return db_manager.get_collection(REVIEWS)


def get_sentiments_collection() -> AsyncIOMotorCollection:
    """Return the ``sentiments`` collection from the active database."""
    return db_manager.get_collection(SENTIMENTS)


def get_scrape_logs_collection() -> AsyncIOMotorCollection:
    """Return the ``scrape_logs`` collection from the active database."""
    return db_manager.get_collection(SCRAPE_LOGS)


def get_users_collection() -> AsyncIOMotorCollection:
    """Return the ``users`` collection from the active database."""
    return db_manager.get_collection(USERS)
