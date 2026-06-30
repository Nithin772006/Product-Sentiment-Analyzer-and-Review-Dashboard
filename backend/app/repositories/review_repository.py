"""
app/repositories/review_repository.py
───────────────────────────────────────
Repository for the ``reviews`` collection.

Extends ``BaseRepository`` with review-specific query methods:
  get_by_product_id     — all reviews for a product (paginated)
  get_by_product_and_rating — filtered by star rating
  get_by_date_range     — reviews within a date window
  get_by_source         — filter by platform
  get_by_verified       — verified purchase reviews only
  count_by_product      — review count for a product
  get_average_rating    — computed average star rating
  get_rating_distribution — star-count breakdown (1★–5★)
  delete_by_product_id  — cascade delete all reviews for a product
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pymongo import ASCENDING, DESCENDING

from app.database.collections import get_reviews_collection
from app.repositories.base_repository import (
    BaseRepository,
    _serialize,
    _to_oid,
    _utcnow,
)
from app.utils.logger import logger


class ReviewRepository(BaseRepository):
    """Async repository for ``reviews`` collection operations."""

    def __init__(self) -> None:
        super().__init__(get_reviews_collection())

    # ── Product-scoped queries ─────────────────────────────────────────────────

    async def get_by_product_id(
        self,
        product_id: str,
        skip: int = 0,
        limit: int = 50,
        sort_field: str = "review_date",
        sort_order: int = DESCENDING,
    ) -> tuple[list[dict], int]:
        """
        Return paginated reviews for a specific product.

        Args:
            product_id: Hex string ObjectId of the parent product.
            skip: Pagination offset.
            limit: Max results per page (capped at 200).
            sort_field: Field to sort by (default: review_date).
            sort_order: DESCENDING (-1) or ASCENDING (1).

        Returns:
            ``(list_of_reviews, total_count)``
        """
        return await self.find(
            filter_query={"product_id": product_id},
            skip=skip,
            limit=limit,
            sort_field=sort_field,
            sort_order=sort_order,
        )

    async def get_by_product_and_rating(
        self,
        product_id: str,
        min_rating: float = 1.0,
        max_rating: float = 5.0,
        skip: int = 0,
        limit: int = 50,
    ) -> tuple[list[dict], int]:
        """
        Return reviews for a product filtered by star-rating range.

        Args:
            product_id: Parent product ObjectId string.
            min_rating: Minimum star rating (inclusive).
            max_rating: Maximum star rating (inclusive).

        Returns:
            ``(list_of_reviews, total_count)``
        """
        return await self.find(
            filter_query={
                "product_id": product_id,
                "rating": {"$gte": min_rating, "$lte": max_rating},
            },
            skip=skip,
            limit=limit,
            sort_field="rating",
            sort_order=DESCENDING,
        )

    # ── Date-range queries ─────────────────────────────────────────────────────

    async def get_by_date_range(
        self,
        start_date: datetime,
        end_date: datetime,
        product_id: Optional[str] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> tuple[list[dict], int]:
        """
        Return reviews posted within a date window.

        Args:
            start_date: Start of the window (inclusive).
            end_date: End of the window (inclusive).
            product_id: Optional — restrict to a specific product.

        Returns:
            ``(list_of_reviews, total_count)``
        """
        query: dict = {"review_date": {"$gte": start_date, "$lte": end_date}}
        if product_id:
            query["product_id"] = product_id

        return await self.find(
            filter_query=query,
            skip=skip,
            limit=limit,
            sort_field="review_date",
            sort_order=DESCENDING,
        )

    # ── Platform filter ────────────────────────────────────────────────────────

    async def get_by_source(
        self,
        source: str,
        skip: int = 0,
        limit: int = 50,
    ) -> tuple[list[dict], int]:
        """Return reviews from a specific platform (amazon / flipkart)."""
        return await self.find(
            filter_query={"source": source},
            skip=skip,
            limit=limit,
        )

    # ── Verified purchase ──────────────────────────────────────────────────────

    async def get_verified_reviews(
        self,
        product_id: str,
        skip: int = 0,
        limit: int = 50,
    ) -> tuple[list[dict], int]:
        """Return only verified-purchase reviews for a product."""
        return await self.find(
            filter_query={"product_id": product_id, "verified_purchase": True},
            skip=skip,
            limit=limit,
            sort_field="review_date",
            sort_order=DESCENDING,
        )

    # ── Aggregation ────────────────────────────────────────────────────────────

    async def count_by_product(self, product_id: str) -> int:
        """Return the total number of reviews for a product."""
        return await self.count(filter_query={"product_id": product_id})

    async def get_average_rating(self, product_id: str) -> Optional[float]:
        """
        Compute the average star rating across all reviews for a product.

        Returns:
            Float average, or ``None`` if no reviews exist.
        """
        pipeline = [
            {"$match": {"product_id": product_id, "rating": {"$ne": None}}},
            {"$group": {"_id": None, "avg": {"$avg": "$rating"}}},
        ]
        async for doc in self._col.aggregate(pipeline):
            return round(doc["avg"], 2)
        return None

    async def get_rating_distribution(self, product_id: str) -> dict[str, int]:
        """
        Return star rating counts for a product.

        Returns:
            Dict mapping star label → count, e.g. ``{"5★": 120, "4★": 80, ...}``
        """
        pipeline = [
            {"$match": {"product_id": product_id, "rating": {"$ne": None}}},
            {"$group": {"_id": {"$floor": "$rating"}, "count": {"$sum": 1}}},
            {"$sort": {"_id": DESCENDING}},
        ]
        distribution: dict[str, int] = {f"{i}★": 0 for i in range(5, 0, -1)}
        async for doc in self._col.aggregate(pipeline):
            star = int(doc["_id"])
            if 1 <= star <= 5:
                distribution[f"{star}★"] = doc["count"]
        return distribution

    # ── Search ─────────────────────────────────────────────────────────────────

    async def search_reviews(
        self,
        search_text: str,
        product_id: Optional[str] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> list[dict]:
        """
        Search review text and reviewer name for a keyword (case-insensitive).

        Args:
            search_text: Keyword to search for.
            product_id: Optional product scope.
            skip: Pagination offset.
            limit: Max results.

        Returns:
            List of matching review dicts.
        """
        regex = {"$regex": search_text, "$options": "i"}
        query: dict = {"$or": [{"review_text": regex}, {"reviewer": regex}]}
        if product_id:
            query["product_id"] = product_id

        limit = min(limit, 200)
        cursor = self._col.find(query).skip(skip).limit(limit)
        docs = await cursor.to_list(length=limit)
        return [_serialize(d) for d in docs]

    # ── Cascade delete ─────────────────────────────────────────────────────────

    async def delete_by_product_id(self, product_id: str) -> int:
        """
        Delete ALL reviews belonging to a product.

        Used for cascade delete when a product is removed.

        Returns:
            Number of deleted review documents.
        """
        count = await self.delete_many({"product_id": product_id})
        logger.info(
            "[reviews] Cascade deleted {n} reviews for product_id={pid}",
            n=count,
            pid=product_id,
        )
        return count
