"""
app/api/routes/analytics.py
────────────────────────────
Product and global dashboard analytics, aggregating database statistics,
sentiment engine ratios, rating distributions, and keyword listings.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, HTTPException, Path, Query
from app.repositories.product_repository import ProductRepository
from app.repositories.review_repository import ReviewRepository
from app.repositories.sentiment_repository import SentimentRepository
from app.utils.bson import format_response

router = APIRouter(prefix="/analytics", tags=["analytics"])


# ── 1. Single Product Analytics Endpoint ──────────────────────────────────────

@router.get("/product/{product_id}")
async def get_product_analytics(
    product_id: str = Path(..., description="The 24-character hexadecimal ObjectId of the product")
) -> dict:
    """
    Get aggregated rating distributions, average scores, polarity statistics,
    and extracted positive/negative keyword lists for a product.
    """
    product_repo = ProductRepository()
    review_repo = ReviewRepository()
    sentiment_repo = SentimentRepository()

    # Verify product exists
    product = await product_repo.get_by_id(product_id)
    if not product:
        raise HTTPException(status_code=404, detail=f"Product not found for id '{product_id}'")

    try:
        # Compute rating distribution (1★ - 5★)
        rating_dist = await review_repo.get_rating_distribution(product_id)

        # Get VADER and TextBlob sentiment statistics
        sentiment_stats = await sentiment_repo.get_sentiment_stats(product_id)

        # Fetch top positive/negative keywords from the aggregated sentiments
        sentiments_cursor = sentiment_repo._col.find({"product_id": product_id}, {"keywords": 1, "sentiment": 1})
        sentiments = await sentiments_cursor.to_list(length=1000)

        pos_kw: dict[str, int] = {}
        neg_kw: dict[str, int] = {}
        
        for s in sentiments:
            kws = s.get("keywords", [])
            label = s.get("sentiment", "neutral")
            target_map = pos_kw if label == "positive" else (neg_kw if label == "negative" else None)
            if target_map is not None:
                for kw in kws:
                    target_map[kw] = target_map.get(kw, 0) + 1

        # Sort and get top 10 positive & negative keywords
        top_pos = sorted(pos_kw.items(), key=lambda x: x[1], reverse=True)[:10]
        top_neg = sorted(neg_kw.items(), key=lambda x: x[1], reverse=True)[:10]

        analytics_data = {
            "product_id": product_id,
            "product_name": product["product_name"],
            "brand": product["brand"],
            "category": product["category"],
            "source": product["source"],
            "average_rating": product["average_rating"],
            "total_reviews": product["total_reviews"],
            "sentiment_summary": sentiment_stats,
            "rating_distribution": rating_dist,
            "keywords": {
                "positive": [{"word": w, "count": c} for w, c in top_pos],
                "negative": [{"word": w, "count": c} for w, c in top_neg],
            }
        }

        return format_response(
            success=True,
            message="Product analytics compiled successfully",
            data=analytics_data
        )

    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to generate analytics: {str(exc)}")


# ── 2. Global Dashboard Summary Metrics ──────────────────────────────────────

@router.get("/dashboard/summary")
async def get_dashboard_summary() -> dict:
    """
    Get system-wide summary metrics for dashboard summary cards.
    """
    product_repo = ProductRepository()
    review_repo = ReviewRepository()
    sentiment_repo = SentimentRepository()

    try:
        # Direct counts — fast and reliable
        total_products = await product_repo._col.count_documents({})
        total_reviews = await review_repo._col.count_documents({})

        # Scraped counts (today vs this week)
        now_utc = datetime.now(tz=timezone.utc)
        today_start = now_utc.replace(hour=0, minute=0, second=0, microsecond=0)
        week_start = today_start - timedelta(days=7)

        scraped_today = await product_repo._col.count_documents({"created_at": {"$gte": today_start}})
        scraped_this_week = await product_repo._col.count_documents({"created_at": {"$gte": week_start}})


        # Global Sentiment counts — directly from sentiments collection
        pos_count = await sentiment_repo._col.count_documents({"sentiment": "positive"})
        neg_count = await sentiment_repo._col.count_documents({"sentiment": "negative"})
        neu_count = await sentiment_repo._col.count_documents({"sentiment": "neutral"})

        summary_data = {
            "total_products": total_products,
            "total_reviews": total_reviews,
            "sentiment_counts": {
                "positive": pos_count,
                "negative": neg_count,
                "neutral": neu_count,
            },
            "scraped_today": scraped_today,
            "scraped_this_week": scraped_this_week,
        }

        return format_response(
            success=True,
            message="Dashboard summary compiled successfully",
            data=summary_data
        )

    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


# ── 3. Global Charts Data Endpoint ───────────────────────────────────────────

@router.get("/dashboard/charts")
async def get_dashboard_charts() -> dict:
    """
    Get aggregated system chart metrics (Sentiment split, Rating count distribution, Platform volumes).
    """
    review_repo = ReviewRepository()
    sentiment_repo = SentimentRepository()

    try:
        # Star Rating Distribution
        rating_dist = await review_repo.get_rating_distribution(None)

        # Source platform review volumes
        amazon_count = await review_repo._col.count_documents({"source": "amazon"})
        flipkart_count = await review_repo._col.count_documents({"source": "flipkart"})

        # Sentiment categories
        pos_count = await sentiment_repo._col.count_documents({"sentiment": "positive"})
        neg_count = await sentiment_repo._col.count_documents({"sentiment": "negative"})
        neu_count = await sentiment_repo._col.count_documents({"sentiment": "neutral"})

        charts_data = {
            "rating_distribution": rating_dist,
            "source_comparison": {
                "amazon": amazon_count,
                "flipkart": flipkart_count,
            },
            "sentiment_distribution": {
                "positive": pos_count,
                "negative": neg_count,
                "neutral": neu_count,
            }
        }

        return format_response(
            success=True,
            message="Dashboard charts compiled successfully",
            data=charts_data
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


# ── 4. Global Sentiment Trends Endpoint ──────────────────────────────────────

@router.get("/dashboard/trends")
async def get_dashboard_trends(
    timeframe: str = Query("monthly", pattern="^(daily|weekly|monthly)$")
) -> dict:
    """
    Get historical ratings / reviews volume trends daily, weekly, or monthly.
    """
    review_repo = ReviewRepository()
    
    try:
        # Group reviews chronologically based on timeframe
        pipeline = []
        if timeframe == "daily":
            # format date as YYYY-MM-DD
            date_format = "%Y-%m-%d"
        elif timeframe == "weekly":
            # format as YYYY-WW (week number)
            date_format = "%Y-%U"
        else:
            # format as YYYY-MM
            date_format = "%Y-%m"

        pipeline = [
            {"$project": {
                "date_str": {"$dateToString": {"format": date_format, "date": "$review_date"}},
                "rating": 1
            }},
            {"$group": {
                "_id": "$date_str",
                "count": {"$sum": 1},
                "avg_rating": {"$avg": "$rating"}
            }},
            {"$sort": {"_id": 1}}
        ]

        cursor = review_repo._col.aggregate(pipeline)
        results = await cursor.to_list(length=365)

        trends = []
        for r in results:
            if r["_id"]:
                trends.append({
                    "date": r["_id"],
                    "volume": r["count"],
                    "avg_rating": round(r["avg_rating"] or 0.0, 2)
                })

        return format_response(
            success=True,
            message=f"Dashboard trends compiled successfully for timeframe '{timeframe}'",
            data=trends
        )

    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


# ── 5. Global Keywords Frequency Endpoint ────────────────────────────────────

@router.get("/dashboard/keywords")
async def get_dashboard_keywords(
    limit: int = Query(15, ge=5, le=50)
) -> dict:
    """
    Get system-wide aggregated frequency keywords.
    """
    sentiment_repo = SentimentRepository()
    
    try:
        # Aggregate keywords array from all sentiment records
        pipeline = [
            {"$unwind": "$keywords"},
            {"$group": {
                "_id": "$keywords",
                "count": {"$sum": 1}
            }},
            {"$sort": {"count": -1}},
            {"$limit": limit}
        ]

        cursor = sentiment_repo._col.aggregate(pipeline)
        results = await cursor.to_list(length=limit)

        keywords = [{"word": r["_id"], "count": r["count"]} for r in results]

        return format_response(
            success=True,
            message="System keywords fetched successfully",
            data=keywords
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
