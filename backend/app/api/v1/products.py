"""
app/api/v1/products.py
───────────────────────
REST API routes for product management and scraping.

⚠️  Placeholder routes — responses return 501 until Phase 2 services are built.
    Schemas, route paths, query-param contracts, and OpenAPI docs are final.
"""

from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.database import get_database
from app.models.product import ProductCreate, ProductResponse
from app.utils.logger import logger

router = APIRouter(prefix="/products", tags=["products"])


@router.get(
    "",
    response_model=List[ProductResponse],
    summary="List all products",
    description="Return a paginated list of all tracked products, with optional platform filter.",
)
async def list_products(
    skip: int = Query(default=0, ge=0, description="Pagination offset"),
    limit: int = Query(default=20, ge=1, le=100, description="Max results"),
    platform: Optional[str] = Query(default=None, pattern="^(amazon|flipkart)$"),
    db: AsyncIOMotorDatabase = Depends(get_database),
) -> List[ProductResponse]:
    """List all products — Phase 2 implementation pending."""
    logger.info("GET /products | skip={skip} limit={limit} platform={platform}",
                skip=skip, limit=limit, platform=platform)
    # TODO: delegate to ProductService.get_all_products in Phase 2
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="list_products — Phase 2 implementation pending",
    )


@router.post(
    "",
    response_model=ProductResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add a new product",
    description="Register a product URL for scraping and sentiment analysis.",
)
async def create_product(
    payload: ProductCreate,
    db: AsyncIOMotorDatabase = Depends(get_database),
) -> ProductResponse:
    """Create a product record — Phase 2 implementation pending."""
    logger.info("POST /products | name={name} platform={platform}",
                name=payload.name, platform=payload.platform)
    # TODO: delegate to ProductService.create_product in Phase 2
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="create_product — Phase 2 implementation pending",
    )


@router.post(
    "/scrape",
    summary="Trigger scrape + sentiment analysis",
    description=(
        "Start a background job that scrapes reviews for the given product URL "
        "and runs sentiment analysis on the results."
    ),
)
async def trigger_scrape(
    url: str = Query(..., description="Product page URL to scrape"),
    platform: str = Query(..., pattern="^(amazon|flipkart)$"),
    max_pages: int = Query(default=5, ge=1, le=20),
    db: AsyncIOMotorDatabase = Depends(get_database),
) -> dict:
    """Trigger scrape job — Phase 2 implementation pending."""
    logger.info(
        "POST /products/scrape | url={url} platform={platform} max_pages={max_pages}",
        url=url, platform=platform, max_pages=max_pages,
    )
    # TODO: delegate to ProductService.trigger_scrape in Phase 2
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="trigger_scrape — Phase 2 implementation pending",
    )


@router.get(
    "/{product_id}",
    response_model=ProductResponse,
    summary="Get product by ID",
)
async def get_product(
    product_id: str,
    db: AsyncIOMotorDatabase = Depends(get_database),
) -> ProductResponse:
    """Fetch a single product — Phase 2 implementation pending."""
    logger.info("GET /products/{id}", id=product_id)
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="get_product — Phase 2 implementation pending",
    )


@router.get(
    "/{product_id}/reviews",
    summary="Get reviews for a product",
)
async def get_product_reviews(
    product_id: str,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
    sentiment: Optional[str] = Query(
        default=None, pattern="^(positive|negative|neutral)$"
    ),
    db: AsyncIOMotorDatabase = Depends(get_database),
) -> dict:
    """Fetch paginated reviews with optional sentiment filter — Phase 2 pending."""
    logger.info("GET /products/{id}/reviews", id=product_id)
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="get_product_reviews — Phase 2 implementation pending",
    )


@router.get(
    "/{product_id}/sentiment",
    summary="Get sentiment summary for a product",
)
async def get_sentiment_summary(
    product_id: str,
    db: AsyncIOMotorDatabase = Depends(get_database),
) -> dict:
    """Fetch aggregated sentiment metrics — Phase 2 pending."""
    logger.info("GET /products/{id}/sentiment", id=product_id)
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="get_sentiment_summary — Phase 2 implementation pending",
    )
