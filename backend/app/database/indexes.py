"""
app/database/indexes.py
────────────────────────
MongoDB index definitions and creation routines.

All indexes are idempotent — calling them multiple times will not raise errors
because Motor uses ``create_indexes`` which skips already-existing indexes.

Index strategy
──────────────
products:
  • Unique compound (product_url + source) — prevents duplicate listings
  • product_name, brand, category — text/sort queries
  • category + brand compound — filtered product browsing
  • average_rating DESC — top-rated products

reviews:
  • product_id — "all reviews for a product"
  • product_id + rating compound — filtered review listing
  • review_date DESC — chronological feed
  • review_url unique sparse — deduplication (sparse: skip docs without URL)

sentiments:
  • review_id unique — one sentiment per review
  • product_id — "all sentiments for a product"
  • product_id + sentiment compound — sentiment distribution aggregation

scrape_logs:
  • scrape_start DESC — recent-jobs queries
  • status + scrape_start compound — failed/pending job dashboards
"""

from __future__ import annotations

from pymongo import ASCENDING, DESCENDING, IndexModel
from pymongo.errors import OperationFailure

from app.database.collections import (
    get_products_collection,
    get_reviews_collection,
    get_scrape_logs_collection,
    get_sentiments_collection,
    get_users_collection,
)
from app.utils.logger import logger


# ── Products ───────────────────────────────────────────────────────────────────

async def create_product_indexes() -> None:
    """Create all indexes on the ``products`` collection."""
    col = get_products_collection()
    indexes = [
        # Unique: one listing per URL per source (deduplication)
        IndexModel(
            [("product_url", ASCENDING), ("source", ASCENDING)],
            unique=True,
            name="idx_products_url_source_unique",
        ),
        IndexModel(
            [("product_name", ASCENDING)],
            name="idx_products_name",
        ),
        IndexModel(
            [("brand", ASCENDING)],
            name="idx_products_brand",
        ),
        IndexModel(
            [("category", ASCENDING)],
            name="idx_products_category",
        ),
        # Compound: filtered product browsing (category → brand drill-down)
        IndexModel(
            [("category", ASCENDING), ("brand", ASCENDING)],
            name="idx_products_category_brand",
        ),
        IndexModel(
            [("average_rating", DESCENDING)],
            name="idx_products_avg_rating_desc",
        ),
        IndexModel(
            [("created_at", DESCENDING)],
            name="idx_products_created_at_desc",
        ),
        IndexModel(
            [("last_scraped", DESCENDING)],
            name="idx_products_last_scraped_desc",
        ),
    ]
    await col.create_indexes(indexes)
    logger.info("  [OK] products - {n} indexes created", n=len(indexes))


# ── Reviews ────────────────────────────────────────────────────────────────────

async def create_review_indexes() -> None:
    """Create all indexes on the ``reviews`` collection."""
    col = get_reviews_collection()
    indexes = [
        # All reviews for a specific product
        IndexModel(
            [("product_id", ASCENDING)],
            name="idx_reviews_product_id",
        ),
        # Filter reviews by rating
        IndexModel(
            [("rating", DESCENDING)],
            name="idx_reviews_rating_desc",
        ),
        # Compound: reviews for a product filtered by rating (most common query)
        IndexModel(
            [("product_id", ASCENDING), ("rating", DESCENDING)],
            name="idx_reviews_product_id_rating",
        ),
        # Chronological review feed
        IndexModel(
            [("review_date", DESCENDING)],
            name="idx_reviews_review_date_desc",
        ),
        # Compound: product + date (date-range for a product)
        IndexModel(
            [("product_id", ASCENDING), ("review_date", DESCENDING)],
            name="idx_reviews_product_id_date",
        ),
        # Source platform filter
        IndexModel(
            [("source", ASCENDING)],
            name="idx_reviews_source",
        ),
        # Indexing: review URL (sparse — some reviews have no URL)
        IndexModel(
            [("review_url", ASCENDING)],
            unique=False,
            sparse=True,
            name="idx_reviews_review_url",
        ),
        IndexModel(
            [("created_at", DESCENDING)],
            name="idx_reviews_created_at_desc",
        ),
    ]
    await col.create_indexes(indexes)
    logger.info("  [OK] reviews - {n} indexes created", n=len(indexes))


# ── Sentiments ─────────────────────────────────────────────────────────────────

async def create_sentiment_indexes() -> None:
    """Create all indexes on the ``sentiments`` collection."""
    col = get_sentiments_collection()
    indexes = [
        # Enforce one sentiment per review
        IndexModel(
            [("review_id", ASCENDING)],
            unique=True,
            name="idx_sentiments_review_id_unique",
        ),
        # All sentiments for a product
        IndexModel(
            [("product_id", ASCENDING)],
            name="idx_sentiments_product_id",
        ),
        # Compound: product → sentiment breakdown (pie chart queries)
        IndexModel(
            [("product_id", ASCENDING), ("sentiment", ASCENDING)],
            name="idx_sentiments_product_id_sentiment",
        ),
        IndexModel(
            [("sentiment", ASCENDING)],
            name="idx_sentiments_sentiment",
        ),
        IndexModel(
            [("processed_at", DESCENDING)],
            name="idx_sentiments_processed_at_desc",
        ),
        # High-confidence results
        IndexModel(
            [("confidence", DESCENDING)],
            name="idx_sentiments_confidence_desc",
        ),
    ]
    await col.create_indexes(indexes)
    logger.info("  [OK] sentiments - {n} indexes created", n=len(indexes))


# ── Scrape Logs ────────────────────────────────────────────────────────────────

async def create_scrape_log_indexes() -> None:
    """Create all indexes on the ``scrape_logs`` collection."""
    col = get_scrape_logs_collection()
    indexes = [
        # Recent jobs dashboard
        IndexModel(
            [("scrape_start", DESCENDING)],
            name="idx_scrape_logs_start_desc",
        ),
        # Filter by job status (success / failed / running)
        IndexModel(
            [("status", ASCENDING)],
            name="idx_scrape_logs_status",
        ),
        # Compound: status + time — "recent failed jobs" query
        IndexModel(
            [("status", ASCENDING), ("scrape_start", DESCENDING)],
            name="idx_scrape_logs_status_start",
        ),
        IndexModel(
            [("source", ASCENDING)],
            name="idx_scrape_logs_source",
        ),
    ]
    await col.create_indexes(indexes)
    logger.info("  [OK] scrape_logs - {n} indexes created", n=len(indexes))


async def create_user_indexes() -> None:
    """Create all indexes on the ``users`` collection."""
    col = get_users_collection()
    indexes = [
        IndexModel(
            [("username_normalized", ASCENDING)],
            unique=True,
            name="idx_users_username_unique",
        )
    ]
    await col.create_indexes(indexes)
    logger.info("  [OK] users - {n} indexes created", n=len(indexes))


# ── Master function ────────────────────────────────────────────────────────────

async def create_all_indexes() -> None:
    """
    Create indexes for all five collections.
    Called once at application startup from ``init_db()``.

    Raises:
        OperationFailure: If an index definition conflicts with an existing one.
    """
    logger.info("Creating database indexes …")
    try:
        await create_product_indexes()
        await create_review_indexes()
        await create_sentiment_indexes()
        await create_scrape_log_indexes()
        await create_user_indexes()
        logger.info("[OK] All indexes created successfully.")
    except OperationFailure as exc:
        logger.error("[FAIL] Index creation failed - {exc}", exc=exc)
        raise
