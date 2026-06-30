"""
app/repositories/sentiment_repository.py
──────────────────────────────────────────
Repository for the ``sentiments`` collection.

Extends ``BaseRepository`` with sentiment-specific query methods:
  get_by_review_id          — fetch the single sentiment for a review
  get_by_product_id         — all sentiments for a product (paginated)
  get_by_label              — filter by positive / negative / neutral
  get_sentiment_stats       — aggregated statistics for dashboard
  upsert_by_review_id       — insert or replace a sentiment result
  delete_by_product_id      — cascade delete when a product is removed
  get_high_confidence       — results above a confidence threshold
"""

from __future__ import annotations

from typing import Optional

from pymongo import DESCENDING

from app.database.collections import get_sentiments_collection
from app.repositories.base_repository import (
    BaseRepository,
    _serialize,
    _utcnow,
)
from app.utils.logger import logger


class SentimentRepository(BaseRepository):
    """Async repository for ``sentiments`` collection operations."""

    def __init__(self) -> None:
        super().__init__(get_sentiments_collection())

    # ── Single-review lookup ───────────────────────────────────────────────────

    async def get_by_review_id(self, review_id: str) -> Optional[dict]:
        """
        Return the sentiment document for a specific review.

        Since the index enforces one sentiment per review, at most one
        document will be returned.

        Args:
            review_id: Hex string ObjectId of the parent review.

        Returns:
            Serialized sentiment dict, or ``None``.
        """
        doc = await self._col.find_one({"review_id": review_id})
        return _serialize(doc) if doc else None

    # ── Product-scoped queries ─────────────────────────────────────────────────

    async def get_by_product_id(
        self,
        product_id: str,
        skip: int = 0,
        limit: int = 50,
        sort_field: str = "processed_at",
        sort_order: int = DESCENDING,
    ) -> tuple[list[dict], int]:
        """
        Return paginated sentiment results for a specific product.

        Args:
            product_id: Hex string ObjectId.
            skip: Pagination offset.
            limit: Max results.

        Returns:
            ``(list_of_sentiments, total_count)``
        """
        return await self.find(
            filter_query={"product_id": product_id},
            skip=skip,
            limit=limit,
            sort_field=sort_field,
            sort_order=sort_order,
        )

    async def get_by_label(
        self,
        label: str,
        product_id: Optional[str] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> tuple[list[dict], int]:
        """
        Return sentiment results filtered by label.

        Args:
            label: 'positive' | 'negative' | 'neutral'
            product_id: Optional product scope.

        Returns:
            ``(list_of_sentiments, total_count)``
        """
        query: dict = {"sentiment": label}
        if product_id:
            query["product_id"] = product_id

        return await self.find(
            filter_query=query,
            skip=skip,
            limit=limit,
            sort_field="confidence",
            sort_order=DESCENDING,
        )

    # ── Aggregated statistics ──────────────────────────────────────────────────

    async def get_sentiment_stats(self, product_id: str) -> dict:
        """
        Compute aggregated sentiment statistics for a product.

        Returns a dict with the shape::

            {
                "product_id": str,
                "total_analysed": int,
                "positive_count": int,
                "negative_count": int,
                "neutral_count":  int,
                "avg_polarity":   float,
                "avg_subjectivity": float,
                "avg_confidence": float,
                "positive_pct":   float,
                "negative_pct":   float,
                "neutral_pct":    float,
            }

        Uses two aggregation pipeline stages for efficiency:
          1. ``$facet`` — parallel counts per label + numeric averages
          2. Merges results in Python
        """
        pipeline = [
            {"$match": {"product_id": product_id}},
            {
                "$facet": {
                    "label_counts": [
                        {"$group": {"_id": "$sentiment", "count": {"$sum": 1}}}
                    ],
                    "averages": [
                        {
                            "$group": {
                                "_id": None,
                                "total": {"$sum": 1},
                                "avg_polarity": {"$avg": "$polarity"},
                                "avg_subjectivity": {"$avg": "$subjectivity"},
                                "avg_confidence": {"$avg": "$confidence"},
                            }
                        }
                    ],
                }
            },
        ]

        stats: dict = {
            "product_id": product_id,
            "total_analysed": 0,
            "positive_count": 0,
            "negative_count": 0,
            "neutral_count": 0,
            "avg_polarity": 0.0,
            "avg_subjectivity": 0.0,
            "avg_confidence": 0.0,
            "positive_pct": 0.0,
            "negative_pct": 0.0,
            "neutral_pct": 0.0,
        }

        async for doc in self._col.aggregate(pipeline):
            # ── Label counts ────────────────────────────────────────────────────
            for item in doc.get("label_counts", []):
                label = item["_id"]
                count = item["count"]
                if label == "positive":
                    stats["positive_count"] = count
                elif label == "negative":
                    stats["negative_count"] = count
                elif label == "neutral":
                    stats["neutral_count"] = count

            # ── Averages ────────────────────────────────────────────────────────
            for avg in doc.get("averages", []):
                stats["total_analysed"] = avg.get("total", 0)
                stats["avg_polarity"] = round(avg.get("avg_polarity") or 0.0, 4)
                stats["avg_subjectivity"] = round(avg.get("avg_subjectivity") or 0.0, 4)
                stats["avg_confidence"] = round(avg.get("avg_confidence") or 0.0, 4)

        # ── Percentages ─────────────────────────────────────────────────────────
        total = stats["total_analysed"]
        if total > 0:
            stats["positive_pct"] = round(stats["positive_count"] / total * 100, 2)
            stats["negative_pct"] = round(stats["negative_count"] / total * 100, 2)
            stats["neutral_pct"] = round(stats["neutral_count"] / total * 100, 2)

        return stats

    async def count_by_product_and_label(
        self, product_id: str, label: str
    ) -> int:
        """Return the count of a specific sentiment label for a product."""
        return await self.count(
            filter_query={"product_id": product_id, "sentiment": label}
        )

    # ── Upsert ─────────────────────────────────────────────────────────────────

    async def upsert_by_review_id(self, review_id: str, data: dict) -> dict:
        """
        Insert or replace the sentiment result for a review.

        Because the ``review_id`` index is unique, this safely handles
        re-running sentiment analysis without creating duplicates.

        Args:
            review_id: Hex string ObjectId of the parent review.
            data: Full sentiment fields dict.

        Returns:
            The upserted document (post-operation state).
        """
        from pymongo import ReturnDocument

        now = _utcnow()
        data["review_id"] = review_id
        data.setdefault("processed_at", now)

        result = await self._col.find_one_and_update(
            {"review_id": review_id},
            {"$set": data},
            upsert=True,
            return_document=ReturnDocument.AFTER,
        )
        logger.info(
            "[sentiments] Upserted | review_id={rid}", rid=review_id
        )
        return _serialize(result)

    # ── Confidence filter ──────────────────────────────────────────────────────

    async def get_high_confidence(
        self,
        product_id: str,
        min_confidence: float = 0.8,
        limit: int = 50,
    ) -> list[dict]:
        """
        Return high-confidence sentiment results for a product.

        Args:
            product_id: Hex string ObjectId.
            min_confidence: Confidence threshold (0–1).
            limit: Max results.

        Returns:
            List of sentiment dicts sorted by confidence DESC.
        """
        cursor = (
            self._col.find(
                {
                    "product_id": product_id,
                    "confidence": {"$gte": min_confidence},
                }
            )
            .sort("confidence", DESCENDING)
            .limit(min(limit, 200))
        )
        docs = await cursor.to_list(length=limit)
        return [_serialize(d) for d in docs]

    # ── Cascade delete ─────────────────────────────────────────────────────────

    async def delete_by_product_id(self, product_id: str) -> int:
        """
        Delete ALL sentiment documents belonging to a product.

        Returns:
            Number of deleted documents.
        """
        count = await self.delete_many({"product_id": product_id})
        logger.info(
            "[sentiments] Cascade deleted {n} sentiments for product_id={pid}",
            n=count,
            pid=product_id,
        )
        return count

    async def delete_by_review_id(self, review_id: str) -> bool:
        """Delete the sentiment document for a specific review."""
        result = await self._col.delete_one({"review_id": review_id})
        return result.deleted_count > 0
