"""
app/repositories/__init__.py
─────────────────────────────
Public re-exports for all repository classes and custom exceptions.
"""
from app.repositories.base_repository import (
    BaseRepository,
    RepositoryError,
    DuplicateDocumentError,
    DocumentNotFoundError,
    InvalidObjectIdError,
)
from app.repositories.product_repository import ProductRepository
from app.repositories.review_repository import ReviewRepository
from app.repositories.sentiment_repository import SentimentRepository
from app.repositories.scrape_log_repository import ScrapeLogRepository

__all__ = [
    # Base
    "BaseRepository",
    "RepositoryError",
    "DuplicateDocumentError",
    "DocumentNotFoundError",
    "InvalidObjectIdError",
    # Specific repositories
    "ProductRepository",
    "ReviewRepository",
    "SentimentRepository",
    "ScrapeLogRepository",
]
