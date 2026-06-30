"""
app/models/scrape_log.py
─────────────────────────
Pydantic v2 models for the ``scrape_logs`` collection.

Each scrape job produces one log document recording what was scraped,
how long it took, and whether it succeeded or failed.

Model hierarchy:
  ScrapeLogBase     — shared fields
  ScrapeLogCreate   — POST body (start of a scrape job)
  ScrapeLogUpdate   — PATCH body (end of a scrape job)
  ScrapeLogInDB     — full MongoDB document
  ScrapeLogResponse — API response shape
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Annotated, Any, Literal, Optional

from bson import ObjectId
from pydantic import BaseModel, BeforeValidator, ConfigDict, Field


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


# ── Scrape status type ─────────────────────────────────────────────────────────

ScrapeStatus = Literal["running", "completed", "failed", "partial"]


# ── Base schema ────────────────────────────────────────────────────────────────

class ScrapeLogBase(BaseModel):
    """Shared scrape log fields."""

    product_name: str = Field(
        ...,
        min_length=1,
        max_length=500,
        examples=["Apple iPhone 15 Pro"],
        description="Name of the product being scraped",
    )
    source: str = Field(
        ...,
        pattern="^(amazon|flipkart)$",
        examples=["amazon"],
        description="Platform scraped: 'amazon' or 'flipkart'",
    )
    scrape_start: datetime = Field(
        default_factory=_utcnow,
        description="UTC timestamp when the scrape job started",
    )
    scrape_end: Optional[datetime] = Field(
        None,
        description="UTC timestamp when the job finished (None while running)",
    )
    total_reviews_found: int = Field(
        default=0,
        ge=0,
        examples=[350],
        description="Number of reviews successfully scraped",
    )
    status: ScrapeStatus = Field(
        default="running",
        examples=["completed"],
        description="Job status: running | completed | failed | partial",
    )
    error_message: Optional[str] = Field(
        None,
        max_length=2000,
        description="Error description if the job failed",
    )


# ── Create model ───────────────────────────────────────────────────────────────

class ScrapeLogCreate(ScrapeLogBase):
    """Schema for creating a scrape log at the start of a job."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "product_name": "Samsung Galaxy S24 Ultra",
                "source": "flipkart",
                "status": "running",
            }
        }
    )


# ── Update model ───────────────────────────────────────────────────────────────

class ScrapeLogUpdate(BaseModel):
    """
    Schema for updating a log when the scrape job finishes.
    Typically called with status, scrape_end, and total_reviews_found.
    """

    scrape_end: Optional[datetime] = Field(default_factory=_utcnow)
    total_reviews_found: Optional[int] = Field(None, ge=0)
    status: Optional[ScrapeStatus] = None
    error_message: Optional[str] = Field(None, max_length=2000)

    def to_update_dict(self) -> dict:
        return self.model_dump(exclude_none=True)


# ── InDB model ─────────────────────────────────────────────────────────────────

class ScrapeLogInDB(ScrapeLogBase):
    """Full scrape log document as stored in MongoDB."""

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

class ScrapeLogResponse(BaseModel):
    """API response schema for scrape log documents."""

    id: str
    product_name: str
    source: str
    scrape_start: datetime
    scrape_end: Optional[datetime]
    total_reviews_found: int
    status: ScrapeStatus
    error_message: Optional[str]

    model_config = ConfigDict(from_attributes=True)
