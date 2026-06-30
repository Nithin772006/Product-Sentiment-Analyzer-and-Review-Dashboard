"""
app/models/sentiment.py
────────────────────────
Pydantic v2 models for the ``sentiments`` collection.

Model hierarchy:
  SentimentBase     — shared fields
  SentimentCreate   — POST body
  SentimentUpdate   — PATCH body
  SentimentInDB     — full MongoDB document
  SentimentResponse — API response
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Annotated, Any, Literal, Optional

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


# ── Sentiment label type ───────────────────────────────────────────────────────

SentimentLabel = Literal["positive", "negative", "neutral"]


# ── Base schema ────────────────────────────────────────────────────────────────

class SentimentBase(BaseModel):
    """Shared sentiment fields validated on every operation."""

    review_id: str = Field(
        ...,
        description="ObjectId of the analysed review",
        examples=["64a1b2c3d4e5f6789abc5678"],
    )
    product_id: str = Field(
        ...,
        description="ObjectId of the parent product",
        examples=["64a1b2c3d4e5f6789abc1234"],
    )
    sentiment: SentimentLabel = Field(
        ...,
        description="Predicted sentiment class: positive | negative | neutral",
        examples=["positive"],
    )
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        examples=[0.93],
        description="Model confidence score (0–1)",
    )
    polarity: float = Field(
        ...,
        ge=-1.0,
        le=1.0,
        examples=[0.75],
        description="TextBlob polarity score (-1 to +1)",
    )
    subjectivity: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        examples=[0.6],
        description="TextBlob subjectivity score (0 = objective, 1 = subjective)",
    )
    processed_at: datetime = Field(
        default_factory=_utcnow,
        description="Timestamp when analysis was run",
    )

    # ── Validators ────────────────────────────────────────────────────────────

    @field_validator("review_id", "product_id")
    @classmethod
    def validate_objectid_fields(cls, v: str) -> str:
        if not ObjectId.is_valid(v):
            raise ValueError(f"Must be a valid ObjectId; got '{v}'")
        return v


# ── Create model ───────────────────────────────────────────────────────────────

class SentimentCreate(SentimentBase):
    """Schema for inserting a new sentiment analysis result."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "review_id": "64a1b2c3d4e5f6789abc5678",
                "product_id": "64a1b2c3d4e5f6789abc1234",
                "sentiment": "positive",
                "confidence": 0.93,
                "polarity": 0.75,
                "subjectivity": 0.6,
            }
        }
    )


# ── Update model ───────────────────────────────────────────────────────────────

class SentimentUpdate(BaseModel):
    """Schema for re-running sentiment analysis on an existing result (PATCH)."""

    sentiment: Optional[SentimentLabel] = None
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0)
    polarity: Optional[float] = Field(None, ge=-1.0, le=1.0)
    subjectivity: Optional[float] = Field(None, ge=0.0, le=1.0)
    processed_at: Optional[datetime] = Field(default_factory=_utcnow)

    def to_update_dict(self) -> dict:
        return self.model_dump(exclude_none=True)


# ── InDB model ─────────────────────────────────────────────────────────────────

class SentimentInDB(SentimentBase):
    """Full sentiment document as stored in MongoDB."""

    id: Optional[PyObjectId] = Field(
        None,
        alias="_id",
        description="MongoDB document ObjectId",
    )

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={datetime: lambda v: v.isoformat()},
    )


# ── Response model ─────────────────────────────────────────────────────────────

class SentimentResponse(BaseModel):
    """API response schema for sentiment documents."""

    id: str
    review_id: str
    product_id: str
    sentiment: SentimentLabel
    confidence: float
    polarity: float
    subjectivity: float
    processed_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ── Aggregated stats schema ────────────────────────────────────────────────────

class SentimentStats(BaseModel):
    """
    Aggregated sentiment statistics for a product.
    Returned by ``SentimentRepository.get_sentiment_stats()``.
    """

    product_id: str
    total_analysed: int = 0
    positive_count: int = 0
    negative_count: int = 0
    neutral_count: int = 0
    avg_polarity: float = 0.0
    avg_subjectivity: float = 0.0
    avg_confidence: float = 0.0
    positive_pct: float = 0.0
    negative_pct: float = 0.0
    neutral_pct: float = 0.0
