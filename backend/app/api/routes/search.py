"""
app/api/routes/search.py
────────────────────────
Search endpoint to query products inside the database by name or brand, supporting URL direct parsing.
"""

from __future__ import annotations

from fastapi import APIRouter, Query, HTTPException
from app.repositories.product_repository import ProductRepository
from app.utils.bson import format_response

router = APIRouter(prefix="/search", tags=["search"])


@router.get("/amazon")
async def search_amazon_live(
    q: str = Query(..., min_length=1, description="Keyword search for Amazon products"),
    limit: int = Query(10, ge=1, le=20)
) -> dict:
    """
    Perform a live web search on Amazon using the given keyword query.
    Returns a list of candidate products (with title, price, thumbnail, URL).
    """
    from app.scraper.amazon_scraper import AmazonScraper
    
    try:
        scraper = AmazonScraper()
        results = await scraper.search_amazon(q, limit=limit)
        return format_response(
            success=True,
            message=f"Found {len(results)} live results for '{q}'",
            data=results
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Amazon live search failed: {str(exc)}")



async def _scrape_and_store_product(url: str, source: str, repo: ProductRepository) -> dict:
    from app.scraper.scraper_service import ScraperService
    from app.repositories.review_repository import ReviewRepository
    from app.sentiment.processor import SentimentBatchProcessor

    scraper_service = ScraperService()
    scraped_data = await scraper_service.scrape_product(url, max_pages=3)
    product_info = scraped_data["product_info"]
    reviews = scraped_data["reviews"]

    new_product = await repo.create(product_info)
    product_id = new_product["id"]

    if reviews:
        review_repo = ReviewRepository()
        db_reviews = []
        for r in reviews:
            db_reviews.append({
                "product_id": product_id,
                "reviewer": r["reviewer"],
                "rating": r["rating"],
                "review_text": r["review"],
                "review_date": r["review_date"],
                "helpful_votes": 0,
                "verified_purchase": True,
                "source": source,
                "review_url": r["url"],
                "sentiment_processed": False,
            })
        await review_repo.insert_many(db_reviews)

        processor = SentimentBatchProcessor()
        await processor.process_product_reviews(product_id)

    return await repo.get_by_id(product_id)


@router.get("")
async def search_products(
    q: str = Query(..., min_length=1, description="Product name, brand search query, or product URL"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100)
) -> dict:
    """
    Search products in database by product name or brand.
    If a URL is provided, it returns the product document matching the URL, triggering a scrape if not cached.
    """
    repo = ProductRepository()
    s = q.strip()

    # Check if query is a URL
    if s.startswith("http://") or s.startswith("https://"):
        s_lower = s.lower()
        if "amazon.in" in s_lower or "amazon.com" in s_lower:
            source = "amazon"
        elif "flipkart.com" in s_lower:
            source = "flipkart"
        else:
            raise HTTPException(status_code=400, detail="Unsupported platform URL. Must be Amazon or Flipkart.")

        try:
            existing = await repo.get_by_url(s, source)
            
            # Auto-clear failed cache entries
            if existing and (existing.get("product_name") == "Unknown Product" or existing.get("total_reviews", 0) == 0):
                from app.repositories.review_repository import ReviewRepository
                from app.repositories.sentiment_repository import SentimentRepository
                review_repo = ReviewRepository()
                sentiment_repo = SentimentRepository()
                await repo.delete(existing["id"])
                await review_repo.delete_by_product_id(existing["id"])
                await sentiment_repo.delete_by_product_id(existing["id"])
                existing = None

            if existing:
                return format_response(
                    success=True,
                    message="Found cached product matching URL",
                    data=[existing]
                )

            final_prod = await _scrape_and_store_product(s, source, repo)
            return format_response(
                success=True,
                message="Product scraped and added successfully from URL",
                data=[final_prod] if final_prod else []
            )

        except Exception as exc:
            raise HTTPException(status_code=500, detail=f"URL search failed: {str(exc)}")

    # Regular keyword search
    try:
        results = await repo.search_by_name(s, skip=skip, limit=limit)
        if results:
            return format_response(
                success=True,
                message=f"Found {len(results)} product(s) matching '{s}'",
                data=results
            )
            
        # If no results found in local database, perform live Amazon search and scrape top result
        from app.scraper.amazon_scraper import AmazonScraper
        scraper = AmazonScraper()
        live_results = await scraper.search_amazon(s, limit=1)
        
        if live_results and len(live_results) > 0:
            top_result = live_results[0]
            top_url = top_result["product_url"]
            source = top_result.get("source", "amazon")
            
            # Check if this URL exists in DB
            existing = await repo.get_by_url(top_url, source)
            if existing and (existing.get("product_name") != "Unknown Product" and existing.get("total_reviews", 0) > 0):
                return format_response(
                    success=True,
                    message=f"Found product via live search (cached): '{s}'",
                    data=[existing]
                )
                
            # Otherwise scrape the top product
            final_prod = await _scrape_and_store_product(top_url, source, repo)
            if final_prod:
                return format_response(
                    success=True,
                    message=f"Product scraped and added successfully from keyword '{s}'",
                    data=[final_prod]
                )

        return format_response(
            success=True,
            message=f"No product found or scraped for '{s}'",
            data=[]
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(exc)}")
