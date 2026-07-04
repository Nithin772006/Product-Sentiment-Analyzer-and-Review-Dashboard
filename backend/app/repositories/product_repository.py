"""
app/repositories/product_repository.py
────────────────────────────────────────
Repository for the ``products`` collection.

Inherits standard CRUD from ``BaseRepository`` and adds product-specific
query methods:
  get_by_url         — exact URL + source lookup (deduplication check)
  get_by_category    — filtered listing by category
  get_by_brand       — filtered listing by brand
  get_by_source      — filtered listing by platform
  search_by_name     — regex search on product_name
  get_top_rated      — products sorted by average_rating DESC
  get_recently_scraped — products sorted by last_scraped DESC
  upsert_by_url      — insert or update a product by its URL+source key
"""

from __future__ import annotations

import re
from datetime import datetime
from typing import Optional

from pymongo import ASCENDING, DESCENDING

from app.database.collections import get_products_collection
from app.repositories.base_repository import (
    BaseRepository,
    DuplicateDocumentError,
    _serialize,
    _to_oid,
    _utcnow,
)
from app.utils.logger import logger


class ProductRepository(BaseRepository):
    """
    Async repository for ``products`` collection operations.

    Instantiated once per request or as a singleton — the Motor collection
    is thread-safe and can be shared.
    """

    def __init__(self) -> None:
        super().__init__(get_products_collection())

    # ── Lookup ─────────────────────────────────────────────────────────────────

    async def get_by_url(self, product_url: str, source: str) -> Optional[dict]:
        """
        Find a product by its exact URL and source platform.

        Used to check for duplicates before inserting a new product.

        Args:
            product_url: Canonical product page URL.
            source: 'amazon' | 'flipkart'

        Returns:
            Serialized product dict, or ``None``.
        """
        doc = await self._col.find_one(
            {"product_url": product_url, "source": source}
        )
        return _serialize(doc) if doc else None

    async def get_by_category(
        self,
        category: str,
        skip: int = 0,
        limit: int = 20,
        sort_by: str = "average_rating",
        sort_order: int = DESCENDING,
    ) -> tuple[list[dict], int]:
        """Return all products in a given category (paginated)."""
        return await self.find(
            filter_query={"category": {"$regex": f"^{category}$", "$options": "i"}},
            skip=skip,
            limit=limit,
            sort_field=sort_by,
            sort_order=sort_order,
        )

    async def get_by_brand(
        self,
        brand: str,
        skip: int = 0,
        limit: int = 20,
    ) -> tuple[list[dict], int]:
        """Return all products from a given brand (paginated)."""
        return await self.find(
            filter_query={"brand": {"$regex": f"^{brand}$", "$options": "i"}},
            skip=skip,
            limit=limit,
        )

    async def get_by_source(
        self,
        source: str,
        skip: int = 0,
        limit: int = 20,
    ) -> tuple[list[dict], int]:
        """Return all products scraped from a specific platform (paginated)."""
        return await self.find(
            filter_query={"source": source},
            skip=skip,
            limit=limit,
        )

    # ── Search ──────────────────────────────────────────────────────────────────

    async def search_by_name(
        self,
        name: str,
        skip: int = 0,
        limit: int = 20,
    ) -> list[dict]:
        """
        Case-insensitive regex search on ``product_name`` and ``brand``.

        Args:
            name: Search query string.
            skip: Pagination offset.
            limit: Max results.

        Returns:
            List of matching products.
        """
        return await self.search(
            search_text=name,
            fields=["product_name", "brand"],
            skip=skip,
            limit=limit,
        )

    # ── Ranked queries ─────────────────────────────────────────────────────────

    async def search_similar(
        self,
        name: str,
        skip: int = 0,
        limit: int = 20,
    ) -> tuple[list[dict], int]:
        """
        Ranked partial-word search over product metadata.

        Handles incomplete multi-word searches such as "oppo ren" or
        "reno 14" and returns close database matches first.
        """
        limit = min(limit, 100)
        query_text = " ".join(name.strip().split()).lower()
        tokens = [t for t in re.findall(r"[a-zA-Z0-9]+", query_text) if t]
        if not tokens:
            return [], 0

        fields = ["product_name", "brand", "category", "source"]

        def token_clause(token: str) -> dict:
            regex = {"$regex": re.escape(token), "$options": "i"}
            return {"$or": [{field: regex} for field in fields]}

        strict_query = {"$and": [token_clause(token) for token in tokens]}
        loose_query = {"$or": [token_clause(token) for token in tokens]}

        cursor = self._col.find(strict_query).limit(300)
        docs = await cursor.to_list(length=300)
        if not docs:
            cursor = self._col.find(loose_query).limit(300)
            docs = await cursor.to_list(length=300)

        def score(doc: dict) -> tuple:
            product_name = str(doc.get("product_name") or "").lower()
            brand = str(doc.get("brand") or "").lower()
            category = str(doc.get("category") or "").lower()
            source = str(doc.get("source") or "").lower()
            combined = f"{product_name} {brand} {category} {source}"

            value = 0
            if product_name == query_text:
                value += 300
            if product_name.startswith(query_text):
                value += 180
            if query_text in product_name:
                value += 120

            for token in tokens:
                if product_name.startswith(token):
                    value += 35
                if token in product_name:
                    value += 25
                if brand.startswith(token):
                    value += 18
                if token in brand:
                    value += 12
                if token in category:
                    value += 8
                if token in combined:
                    value += 5

            updated_at = doc.get("updated_at")
            updated_score = updated_at.timestamp() if isinstance(updated_at, datetime) else 0

            return (
                value,
                doc.get("total_reviews") or 0,
                doc.get("average_rating") or 0,
                updated_score,
            )

        ranked = sorted(docs, key=score, reverse=True)
        total = len(ranked)
        page = ranked[skip: skip + limit]
        return [_serialize(d) for d in page], total

    async def get_top_rated(
        self,
        limit: int = 10,
        min_reviews: int = 10,
    ) -> list[dict]:
        """
        Return top-rated products (min review threshold filters low-volume noise).

        Args:
            limit: Max products to return.
            min_reviews: Minimum total_reviews required.

        Returns:
            List of products sorted by average_rating DESC.
        """
        cursor = (
            self._col.find({"total_reviews": {"$gte": min_reviews}})
            .sort("average_rating", DESCENDING)
            .limit(limit)
        )
        docs = await cursor.to_list(length=limit)
        return [_serialize(d) for d in docs]

    async def get_recently_scraped(self, limit: int = 10) -> list[dict]:
        """Return recently scraped products sorted by last_scraped DESC."""
        cursor = (
            self._col.find({"last_scraped": {"$ne": None}})
            .sort("last_scraped", DESCENDING)
            .limit(limit)
        )
        docs = await cursor.to_list(length=limit)
        return [_serialize(d) for d in docs]

    # ── Upsert ─────────────────────────────────────────────────────────────────

    async def upsert_by_url(self, data: dict) -> dict:
        """
        Insert the product if it doesn't exist; update it if it does.

        Uses ``product_url`` + ``source`` as the natural key.

        Args:
            data: Product fields dict (must include product_url and source).

        Returns:
            The upserted document (post-operation state).
        """
        now = _utcnow()
        filter_q = {
            "product_url": data["product_url"],
            "source": data["source"],
        }
        update_doc = {
            "$set": {**data, "updated_at": now},
            "$setOnInsert": {"created_at": now},
        }

        from pymongo import ReturnDocument

        result = await self._col.find_one_and_update(
            filter_q,
            update_doc,
            upsert=True,
            return_document=ReturnDocument.AFTER,
        )
        logger.info(
            "[products] Upserted | url={url} source={src}",
            url=data["product_url"],
            src=data["source"],
        )
        return _serialize(result)

    # ── Rating filter ──────────────────────────────────────────────────────────

    async def get_by_rating_range(
        self,
        min_rating: float,
        max_rating: float = 5.0,
        skip: int = 0,
        limit: int = 20,
    ) -> tuple[list[dict], int]:
        """Return products with average_rating between min and max (paginated)."""
        return await self.find(
            filter_query={
                "average_rating": {"$gte": min_rating, "$lte": max_rating}
            },
            skip=skip,
            limit=limit,
            sort_field="average_rating",
            sort_order=DESCENDING,
        )

    # ── Distinct values ────────────────────────────────────────────────────────

    async def get_distinct_categories(self) -> list[str]:
        """Return a list of all distinct product categories."""
        return await self._col.distinct("category")

    async def get_distinct_brands(self) -> list[str]:
        """Return a list of all distinct brands."""
        return await self._col.distinct("brand")
