"""
app/database/__init__.py
─────────────────────────
Public re-exports for the database package.
"""
from app.database.database import DatabaseManager, db_manager, get_database
from app.database.collections import (
    PRODUCTS,
    REVIEWS,
    SENTIMENTS,
    SCRAPE_LOGS,
    ALL_COLLECTIONS,
    get_products_collection,
    get_reviews_collection,
    get_sentiments_collection,
    get_scrape_logs_collection,
)
from app.database.init_db import init_db, shutdown_db

__all__ = [
    # Singleton & dependency
    "DatabaseManager",
    "db_manager",
    "get_database",
    # Collection constants
    "PRODUCTS",
    "REVIEWS",
    "SENTIMENTS",
    "SCRAPE_LOGS",
    "ALL_COLLECTIONS",
    # Collection accessors
    "get_products_collection",
    "get_reviews_collection",
    "get_sentiments_collection",
    "get_scrape_logs_collection",
    # Lifecycle
    "init_db",
    "shutdown_db",
]
