"""
app/models/review.py
─────────────────────
Pydantic v2 models for the ``reviews`` collection.

Model hierarchy:
  ReviewBase     — shared fields with validation
  ReviewCreate   — POST body
  ReviewUpdate   — PATCH body
  ReviewInDB     — full MongoDB document (_id → id alias)
  ReviewResponse — API response shape
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Annotated, Any, Optional

from bson import ObjectId
from pydantic import BaseModel, BeforeValidator, ConfigDict, Field, field_validator


# ── Pydantic v2 ObjectId type ─────────────────────────────────────────────────

def _validate_object_id(v: Any) -> str:
    if isinstance(v, ObjectId):
        return str(v)
    if isinstance(v, str) and ObjectId.is_valid(v):
        return v
    raise ValueError(f"Invalid ObjectId: {v!r}")


PyObjectId = Annotated[str, BeforeValidator(_validate_object_id)]


def _utcnow() -> datetime:
    return datetime.now(tz=timezone.utc)


# ── Base schema ────────────────────────────────────────────────────────────────

class ReviewBase(BaseModel):
    """Shared review fields validated on every operation."""

    product_id: str = Field(
        ...,
        description="MongoDB ObjectId string of the parent product",
        examples=["64a1b2c3d4e5f6789abc1234"],
    )
    reviewer: Optional[str] = Field(
        None,
        max_length=200,
        examples=["Rahul S."],
        description="Display name of the reviewer",
    )
    rating: Optional[float] = Field(
        None,
        ge=1.0,
        le=5.0,
        examples=[4.0],
        description="Star rating given by the reviewer (1–5)",
    )
    review_text: str = Field(
        ...,
        min_length=1,
        examples=["Great product, highly recommend!"],
        description="Full review body text",
    )
    review_date: Optional[datetime] = Field(
        None,
        description="Date the review was originally posted",
    )
    helpful_votes: int = Field(
        default=0,
        ge=0,
        examples=[12],
        description="Number of helpful votes the review received",
    )
    verified_purchase: bool = Field(
        default=False,
        examples=[True],
        description="Whether the reviewer purchased the product",
    )
    source: str = Field(
        ...,
        pattern="^(amazon|flipkart)$",
        examples=["amazon"],
        description="Platform the review was scraped from",
    )
    review_url: Optional[str] = Field(
        None,
        examples=["https://www.amazon.in/gp/customer-reviews/EXAMPLE"],
        description="Direct link to the review (used for deduplication)",
    )

    # ── Field validators ──────────────────────────────────────────────────────

    @field_validator("product_id")
    @classmethod
    def validate_product_id(cls, v: str) -> str:
        if not ObjectId.is_valid(v):
            raise ValueError(f"product_id must be a valid ObjectId; got '{v}'")
        return v

    @field_validator("review_date", mode="before")
    @classmethod
    def parse_review_date(cls, v: Any) -> Optional[datetime]:
        """Accept ISO 8601 strings and datetime objects."""
        if v is None:
            return None
        if isinstance(v, datetime):
            return v
        if isinstance(v, str):
            try:
                dt = datetime.fromisoformat(v.replace("Z", "+00:00"))
                return dt
            except ValueError:
                raise ValueError(f"Cannot parse review_date: '{v}'")
        raise ValueError(f"review_date must be a datetime or ISO string; got {type(v)}")


# ── Create model ───────────────────────────────────────────────────────────────

class ReviewCreate(ReviewBase):
    """Schema for inserting a scraped review into the ``reviews`` collection."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "product_id": "64a1b2c3d4e5f6789abc1234",
                "reviewer": "Priya M.",
                "rating": 5.0,
                "review_text": "Absolutely love this product. Works perfectly!",
                "review_date": "2024-03-15T08:30:00",
                "helpful_votes": 25,
                "verified_purchase": True,
                "source": "flipkart",
                "review_url": "https://www.flipkart.com/product/review/EXAMPLE",
            }
        }
    )


# ── Update model ───────────────────────────────────────────────────────────────

class ReviewUpdate(BaseModel):
    """Schema for partially updating a review (PATCH semantics)."""

    reviewer: Optional[str] = Field(None, max_length=200)
    rating: Optional[float] = Field(None, ge=1.0, le=5.0)
    review_text: Optional[str] = Field(None, min_length=1)
    review_date: Optional[datetime] = None
    helpful_votes: Optional[int] = Field(None, ge=0)
    verified_purchase: Optional[bool] = None

    def to_update_dict(self) -> dict:
        """Return only the fields that were explicitly set (non-None)."""
        return self.model_dump(exclude_none=True)


# ── InDB model ─────────────────────────────────────────────────────────────────

class ReviewInDB(ReviewBase):
    """Full review document as stored in MongoDB."""

    id: Optional[PyObjectId] = Field(
        None,
        alias="_id",
        description="MongoDB document ObjectId",
    )
    created_at: datetime = Field(default_factory=_utcnow)

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={datetime: lambda v: v.isoformat()},
    )


# ── Response model ─────────────────────────────────────────────────────────────

class ReviewResponse(BaseModel):
    """API response schema for review documents."""

    id: str
    product_id: str
    reviewer: Optional[str]
    rating: Optional[float]
    review_text: str
    review_date: Optional[datetime]
    helpful_votes: int
    verified_purchase: bool
    source: str
    review_url: Optional[str]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
