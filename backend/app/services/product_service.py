"""
app/services/product_service.py
────────────────────────────────
Business logic layer for Product operations.

⚠️  PLACEHOLDER — Implementation in Phase 2.
    This layer sits between the API routers and the database/scraper,
    keeping route handlers thin and testable.
"""

from __future__ import annotations

from typing import List, Optional

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.models.product import ProductCreate, ProductInDB, ProductResponse, ProductUpdate
from app.utils.logger import logger


class ProductService:
    """
    Orchestrates product creation, retrieval, and scrape-trigger operations.

    Dependencies are injected via __init__ for easy unit-testing with mocks.
    """

    def __init__(self, db: AsyncIOMotorDatabase) -> None:
        self._db = db
        self._collection = db["products"]

    async def get_all_products(
        self,
        skip: int = 0,
        limit: int = 20,
        platform: Optional[str] = None,
    ) -> List[ProductResponse]:
        """
        Return a paginated list of all tracked products.

        Args:
            skip: Number of documents to skip (pagination offset).
            limit: Max documents to return.
            platform: Optional filter — 'amazon' | 'flipkart'.

        Returns:
            list[ProductResponse]: Product documents.

        Raises:
            NotImplementedError: Until Phase 2 implementation.
        """
        logger.info("get_all_products | skip={skip} limit={limit}", skip=skip, limit=limit)
        # TODO: Implement DB query in Phase 2
        raise NotImplementedError("ProductService.get_all_products — Phase 2")

    async def get_product_by_id(self, product_id: str) -> Optional[ProductResponse]:
        """
        Fetch a single product by its MongoDB ObjectId.

        Args:
            product_id: Hex string ObjectId.

        Returns:
            ProductResponse | None if not found.

        Raises:
            NotImplementedError: Until Phase 2 implementation.
        """
        logger.info("get_product_by_id | id={id}", id=product_id)
        # TODO: Implement DB query in Phase 2
        raise NotImplementedError("ProductService.get_product_by_id — Phase 2")

    async def create_product(self, payload: ProductCreate) -> ProductResponse:
        """
        Persist a new product document.

        Args:
            payload: Validated ProductCreate schema.

        Returns:
            ProductResponse: Newly created document.

        Raises:
            NotImplementedError: Until Phase 2 implementation.
        """
        logger.info("create_product | name={name}", name=payload.name)
        # TODO: Implement DB insert in Phase 2
        raise NotImplementedError("ProductService.create_product — Phase 2")

    async def trigger_scrape(self, product_id: str) -> dict:
        """
        Kick off a background scrape + sentiment analysis job.

        Args:
            product_id: Target product ObjectId.

        Returns:
            dict: Job status response.

        Raises:
            NotImplementedError: Until Phase 2 implementation.
        """
        logger.info("trigger_scrape | product_id={id}", id=product_id)
        # TODO: Integrate scraper + SentimentAnalyzer in Phase 2
        raise NotImplementedError("ProductService.trigger_scrape — Phase 2")
