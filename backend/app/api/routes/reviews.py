"""
app/api/routes/reviews.py
─────────────────────────
Review query routes to fetch product reviews with filters, sorting, and pagination.
"""

from __future__ import annotations

from typing import Optional
from fastapi import APIRouter, Query, HTTPException, Path
from app.repositories.review_repository import ReviewRepository
from app.utils.bson import format_response

router = APIRouter(prefix="/reviews", tags=["reviews"])


@router.get("")
async def get_reviews(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200)
) -> dict:
    """
    List all reviews.
    """
    repo = ReviewRepository()
    try:
        reviews, total = await repo.find(skip=skip, limit=limit, sort_field="review_date")
        return format_response(
            success=True,
            message="Reviews fetched successfully",
            data=reviews,
            total=total,
            page=(skip // limit) + 1,
            limit=limit
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/{id}")
async def get_review(
    id: str = Path(..., description="Review ID")
) -> dict:
    """
    Get a single review.
    """
    repo = ReviewRepository()
    review = await repo.get_by_id(id)
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    
    return format_response(
        success=True,
        message="Review fetched successfully",
        data=review
    )


@router.get("/product/{product_id}")
async def get_product_reviews(
    product_id: str = Path(..., description="Product ID"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    rating: Optional[float] = Query(None, ge=1.0, le=5.0, description="Filter by exact rating"),
    source: Optional[str] = Query(None, pattern="^(amazon|flipkart)$", description="Filter by source"),
    verified: Optional[bool] = Query(None, description="Filter by verified purchase status"),
    sort_by: str = Query("review_date", description="Field to sort by"),
    order: str = Query("desc", pattern="^(asc|desc)$")
) -> dict:
    """
    Get reviews for a product with filters, sorting, and pagination.
    """
    repo = ReviewRepository()
    from pymongo import DESCENDING, ASCENDING
    sort_order = DESCENDING if order == "desc" else ASCENDING

    # Build filter query
    query_filter: dict = {"product_id": product_id}
    if rating is not None:
        query_filter["rating"] = rating
    if source is not None:
        query_filter["source"] = source
    if verified is not None:
        query_filter["verified_purchase"] = verified

    try:
        reviews, total = await repo.find(
            filter_query=query_filter,
            skip=skip,
            limit=limit,
            sort_field=sort_by,
            sort_order=sort_order
        )
        return format_response(
            success=True,
            message=f"Reviews for product '{product_id}' fetched successfully",
            data=reviews,
            total=total,
            page=(skip // limit) + 1,
            limit=limit
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
