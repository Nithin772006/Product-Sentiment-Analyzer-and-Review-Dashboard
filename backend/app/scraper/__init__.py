"""
app/scraper/__init__.py
────────────────────────
Public re-exports for the scraper package.
"""
from app.scraper.base_scraper import BaseScraper
from app.scraper.playwright_driver import PlaywrightDriver
from app.scraper.review_extractor import ReviewExtractor, is_truncated_text, clean_review_text
from app.scraper.amazon_scraper import AmazonScraper
from app.scraper.flipkart_scraper import FlipkartScraper
from app.scraper.scraper_service import ScraperService

__all__ = [
    "BaseScraper",
    "PlaywrightDriver",
    "ReviewExtractor",
    "is_truncated_text",
    "clean_review_text",
    "AmazonScraper",
    "FlipkartScraper",
    "ScraperService",
]
