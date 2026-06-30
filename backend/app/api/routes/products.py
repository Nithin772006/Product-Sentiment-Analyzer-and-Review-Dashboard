"""
app/api/routes/products.py
──────────────────────────
Product CRUD routes and trigger scraper endpoints. Integrates dynamic review crawling and sentiment analysis.
"""

from __future__ import annotations

from typing import Optional
from fastapi import APIRouter, HTTPException, Query, Path, Body
from pydantic import BaseModel, HttpUrl

from app.repositories.product_repository import ProductRepository
from app.repositories.review_repository import ReviewRepository
from app.repositories.sentiment_repository import SentimentRepository
from app.scraper.scraper_service import ScraperService
from app.sentiment.processor import SentimentBatchProcessor
from app.utils.bson import format_response

router = APIRouter(prefix="/products", tags=["products"])


# ── Schemas for validation ────────────────────────────────────────────────────

class ProductSearchRequest(BaseModel):
    product_url: str
    max_pages: Optional[int] = 5


class ProductUpdateRequest(BaseModel):
    product_name: Optional[str] = None
    brand: Optional[str] = None
    category: Optional[str] = None


# ── Routes ────────────────────────────────────────────────────────────────────

@router.get("")
async def get_products(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    sort_by: str = Query("created_at", description="Field to sort by"),
    order: str = Query("desc", pattern="^(asc|desc)$")
) -> dict:
    """
    List all products in the database.
    """
    repo = ProductRepository()
    from pymongo import DESCENDING, ASCENDING
    sort_order = DESCENDING if order == "desc" else ASCENDING
    
    try:
        products, total = await repo.find(skip=skip, limit=limit, sort_field=sort_by, sort_order=sort_order)
        return format_response(
            success=True,
            message="Products fetched successfully",
            data=products,
            total=total,
            page=(skip // limit) + 1,
            limit=limit
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to fetch products: {str(exc)}")


@router.get("/{id}")
async def get_product(
    id: str = Path(..., description="The 24-character hexadecimal ObjectId of the product")
) -> dict:
    """
    Get detailed info of a single product.
    """
    repo = ProductRepository()
    product = await repo.get_by_id(id)
    if not product:
        raise HTTPException(status_code=404, detail=f"Product with id '{id}' not found")
    
    return format_response(
        success=True,
        message="Product fetched successfully",
        data=product
    )


@router.post("/search")
async def search_or_trigger_scraper(
    payload: ProductSearchRequest = Body(...)
) -> dict:
    """
    Search database for product URL. If found, returns cached metadata.
    Otherwise, triggers the scraper, performs sentiment analysis, and returns the result.
    """
    product_url = payload.product_url.strip()
    max_pages = payload.max_pages or 5
    
    product_repo = ProductRepository()
    review_repo = ReviewRepository()
    
    # 1. Detect platform source
    s = product_url.lower()
    if "amazon.in" in s or "amazon.com" in s:
        source = "amazon"
    elif "flipkart.com" in s:
        source = "flipkart"
    else:
        raise HTTPException(status_code=400, detail="Unsupported platform URL. Must be Amazon or Flipkart.")

    # 2. Check if product exists in DB
    existing_product = await product_repo.get_by_url(product_url, source)
    if existing_product:
        if existing_product.get("product_name") == "Unknown Product" or existing_product.get("total_reviews", 0) == 0:
            from app.repositories.sentiment_repository import SentimentRepository
            sentiment_repo = SentimentRepository()
            await product_repo.delete(existing_product["id"])
            await review_repo.delete_by_product_id(existing_product["id"])
            await sentiment_repo.delete_by_product_id(existing_product["id"])
        else:
            return format_response(
                success=True,
                message="Product fetched from database cache",
                data=existing_product
            )

    # 3. Trigger Scraper
    from app.api.routes.realtime import manager
    await manager.broadcast({
        "event": "scraping_started",
        "message": f"Scraping started for product URL from {source}",
        "url": product_url
    })

    scraper_service = ScraperService()
    try:
        scraped_data = await scraper_service.scrape_product(product_url, max_pages=max_pages)
    except Exception as exc:
        await manager.broadcast({
            "event": "error",
            "message": f"Scraping failed: {str(exc)}"
        })
        raise HTTPException(status_code=502, detail=f"Scraper failed: {str(exc)}")

    product_info = scraped_data["product_info"]
    reviews = scraped_data["reviews"]

    await manager.broadcast({
        "event": "scraping_completed",
        "message": f"Successfully scraped {len(reviews)} reviews for '{product_info['product_name']}'",
        "product_name": product_info["product_name"]
    })

    # 4. Save Product to Database
    try:
        new_product = await product_repo.create(product_info)
        product_id = new_product["id"]
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to create product record: {str(exc)}")

    # 5. Save Scraped Reviews
    if reviews:
        # Re-map reviews to associate with new product ID
        db_reviews = []
        for r in reviews:
            db_reviews.append({
                "product_id": product_id,
                "reviewer": r["reviewer"],
                "rating": r["rating"],
                "review_text": r["review"],
                "review_date": r["review_date"],
                "helpful_votes": 0,
                "verified_purchase": False,
                "source": source,
                "review_url": r["url"],
                "sentiment_processed": False,
            })
        
        try:
            await review_repo.insert_many(db_reviews)
        except Exception as exc:
            # Non-fatal error; logs continue
            pass

    # 6. Run Sentiment Analysis Batch Processor
    await manager.broadcast({
        "event": "sentiment_started",
        "message": "Starting consensus sentiment analysis on scraped reviews...",
        "product_id": product_id
    })

    try:
        processor = SentimentBatchProcessor()
        await processor.process_product_reviews(product_id)
        await manager.broadcast({
            "event": "sentiment_completed",
            "message": "Sentiment analysis and statistics processing finished successfully!",
            "product_id": product_id
        })
    except Exception as exc:
        await manager.broadcast({
            "event": "error",
            "message": f"Sentiment processing failed: {str(exc)}"
        })

    # 7. Fetch final post-analysis state of product
    final_product = await product_repo.get_by_id(product_id)
    
    return format_response(
        success=True,
        message="Product scraped and analyzed successfully",
        data=final_product
    )


@router.put("/{id}")
async def update_product(
    id: str = Path(...),
    payload: ProductUpdateRequest = Body(...)
) -> dict:
    """
    Update product details.
    """
    repo = ProductRepository()
    update_data = payload.model_dump(exclude_none=True)
    if not update_data:
        raise HTTPException(status_code=400, detail="No fields provided for update")

    updated = await repo.update(id, update_data)
    if not updated:
        raise HTTPException(status_code=404, detail="Product not found")

    return format_response(
        success=True,
        message="Product updated successfully",
        data=updated
    )


@router.delete("/{id}")
async def delete_product(
    id: str = Path(...)
) -> dict:
    """
    Delete a product and cascade delete all its reviews and sentiment records.
    """
    product_repo = ProductRepository()
    review_repo = ReviewRepository()
    sentiment_repo = SentimentRepository()

    # Verify exists
    product = await product_repo.get_by_id(id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    try:
        # Cascade Delete
        await sentiment_repo.delete_by_product_id(id)
        await review_repo.delete_by_product_id(id)
        deleted = await product_repo.delete(id)
        
        return format_response(
            success=deleted,
            message="Product and all associated reviews and sentiments deleted successfully",
            data={"product_id": id}
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Delete failed: {str(exc)}")
