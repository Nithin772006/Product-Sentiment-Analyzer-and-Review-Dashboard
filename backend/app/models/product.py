"""
app/models/product.py
──────────────────────
Pydantic v2 models for the ``products`` collection.

Model hierarchy:
  ProductBase     — shared fields validated on every operation
  ProductCreate   — POST body (no _id / timestamps)
  ProductUpdate   — PATCH body (all fields Optional)
  ProductInDB     — full document as stored in MongoDB (_id → id alias)
  ProductResponse — API response shape (id as string, no alias)
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Annotated, Any, Optional

from bson import ObjectId
from pydantic import BaseModel, BeforeValidator, ConfigDict, Field


# ── Pydantic v2 ObjectId type ─────────────────────────────────────────────────

def _validate_object_id(v: Any) -> str:
    """Accept a BSON ObjectId or a 24-hex string; always return a plain string."""
    if isinstance(v, ObjectId):
        return str(v)
    if isinstance(v, str) and ObjectId.is_valid(v):
        return v
    raise ValueError(f"Invalid ObjectId: {v!r}")


PyObjectId = Annotated[str, BeforeValidator(_validate_object_id)]


# ── Timestamp helper ───────────────────────────────────────────────────────────

def _utcnow() -> datetime:
    return datetime.now(tz=timezone.utc)


# ── Allowed values ─────────────────────────────────────────────────────────────

ALLOWED_SOURCES = ("amazon", "flipkart")


# ── Base schema ────────────────────────────────────────────────────────────────

class ProductBase(BaseModel):
    """Fields shared by Create / Update / Response schemas."""

    product_name: str = Field(
        ...,
        min_length=1,
        max_length=500,
        examples=["Apple iPhone 15 Pro"],
        description="Full product name as listed on the platform",
    )
    brand: Optional[str] = Field(
        None,
        max_length=200,
        examples=["Apple"],
        description="Product brand or manufacturer",
    )
    category: Optional[str] = Field(
        None,
        max_length=200,
        examples=["Smartphones"],
        description="Product category / department",
    )
    source: str = Field(
        ...,
        pattern="^(amazon|flipkart)$",
        examples=["amazon"],
        description="Scraping source platform: 'amazon' or 'flipkart'",
    )
    product_url: str = Field(
        ...,
        min_length=10,
        examples=["https://www.amazon.in/dp/B0C7V3DKKS"],
        description="Canonical product page URL",
    )
    average_rating: Optional[float] = Field(
        None,
        ge=0.0,
        le=5.0,
        examples=[4.3],
        description="Current star rating (0–5)",
    )
    total_reviews: Optional[int] = Field(
        None,
        ge=0,
        examples=[2580],
        description="Total number of reviews on the platform",
    )
    last_scraped: Optional[datetime] = Field(
        None,
        description="Timestamp of the most recent successful scrape",
    )


# ── Create model ───────────────────────────────────────────────────────────────

class ProductCreate(ProductBase):
    """
    Schema for creating a new product record.
    Sent as the POST request body to the products endpoint.
    """

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "product_name": "Apple iPhone 15 Pro",
                "brand": "Apple",
                "category": "Smartphones",
                "source": "amazon",
                "product_url": "https://www.amazon.in/dp/B0C7V3DKKS",
                "average_rating": 4.5,
                "total_reviews": 3200,
            }
        }
    )


# ── Update model ───────────────────────────────────────────────────────────────

class ProductUpdate(BaseModel):
    """
    Schema for partially updating a product (PATCH semantics).
    All fields are optional — only supplied fields are written.
    """

    product_name: Optional[str] = Field(None, min_length=1, max_length=500)
    brand: Optional[str] = Field(None, max_length=200)
    category: Optional[str] = Field(None, max_length=200)
    product_url: Optional[str] = Field(None, min_length=10)
    average_rating: Optional[float] = Field(None, ge=0.0, le=5.0)
    total_reviews: Optional[int] = Field(None, ge=0)
    last_scraped: Optional[datetime] = None

    def to_update_dict(self) -> dict:
        """Return only the fields that were explicitly set (non-None)."""
        return self.model_dump(exclude_none=True)


# ── InDB model ─────────────────────────────────────────────────────────────────

class ProductInDB(ProductBase):
    """
    Full product document as returned from MongoDB.

    The ``_id`` field from MongoDB is aliased to ``id`` and serialized
    as a plain string via the ``PyObjectId`` annotation.
    """

    id: Optional[PyObjectId] = Field(
        None,
        alias="_id",
        description="MongoDB document ObjectId (read-only)",
    )
    created_at: datetime = Field(default_factory=_utcnow)
    updated_at: datetime = Field(default_factory=_utcnow)

    model_config = ConfigDict(
        populate_by_name=True,       # allow "id" and "_id" both
        arbitrary_types_allowed=True,
        json_encoders={datetime: lambda v: v.isoformat()},
    )


# ── Response model ─────────────────────────────────────────────────────────────

class ProductResponse(BaseModel):
    """
    API response schema.
    Flat shape — no aliases, datetime as ISO 8601 string compatible.
    """

    id: str
    product_name: str
    brand: Optional[str]
    category: Optional[str]
    source: str
    product_url: str
    average_rating: Optional[float]
    total_reviews: Optional[int]
    last_scraped: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
