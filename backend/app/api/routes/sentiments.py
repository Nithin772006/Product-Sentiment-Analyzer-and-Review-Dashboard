"""
app/api/routes/sentiments.py
────────────────────────────
Sentiment query routes to retrieve analyzed sentiment records.
"""

from __future__ import annotations

from typing import Optional
from fastapi import APIRouter, Query, HTTPException, Path
from app.repositories.sentiment_repository import SentimentRepository
from app.utils.bson import format_response

router = APIRouter(prefix="/sentiments", tags=["sentiments"])


@router.get("")
async def get_sentiments(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200)
) -> dict:
    """
    List all sentiments.
    """
    repo = SentimentRepository()
    try:
        sentiments, total = await repo.find(skip=skip, limit=limit, sort_field="processed_at")
        return format_response(
            success=True,
            message="Sentiments fetched successfully",
            data=sentiments,
            total=total,
            page=(skip // limit) + 1,
            limit=limit
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/{id}")
async def get_sentiment(
    id: str = Path(..., description="Sentiment ID")
) -> dict:
    """
    Get a single sentiment record.
    """
    repo = SentimentRepository()
    sentiment = await repo.get_by_id(id)
    if not sentiment:
        raise HTTPException(status_code=404, detail="Sentiment not found")
    
    return format_response(
        success=True,
        message="Sentiment fetched successfully",
        data=sentiment
    )


@router.get("/product/{product_id}")
async def get_product_sentiments(
    product_id: str = Path(...),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    label: Optional[str] = Query(None, pattern="^(positive|negative|neutral)$", description="Filter by sentiment label")
) -> dict:
    """
    Get sentiment records for a product.
    """
    repo = SentimentRepository()
    query_filter: dict = {"product_id": product_id}
    if label is not None:
        query_filter["sentiment"] = label

    try:
        sentiments, total = await repo.find(
            filter_query=query_filter,
            skip=skip,
            limit=limit,
            sort_field="processed_at"
        )
        return format_response(
            success=True,
            message=f"Sentiments for product '{product_id}' fetched successfully",
            data=sentiments,
            total=total,
            page=(skip // limit) + 1,
            limit=limit
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
