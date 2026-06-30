"""
app/scraper/scraper_service.py
───────────────────────────────
Unified service orchestrator for Amazon and Flipkart reviews scraping.
Does not perform database persistence directly (mock-friendly, DB is written in services/api).
"""

from __future__ import annotations

from typing import Dict, List, Optional
from app.scraper.amazon_scraper import AmazonScraper
from app.scraper.flipkart_scraper import FlipkartScraper
from app.utils.logger import logger


class ScraperService:
    """
    Coordinates product info and reviews scraping across Amazon and Flipkart.
    """

    def __init__(self) -> None:
        self._amazon = AmazonScraper()
        self._flipkart = FlipkartScraper()

    def _detect_platform(self, url: str) -> Optional[str]:
        """Detect whether the URL belongs to Amazon or Flipkart."""
        s = url.lower()
        if "amazon.in" in s or "amazon.com" in s:
            return "amazon"
        elif "flipkart.com" in s:
            return "flipkart"
        return None

    async def scrape_product(self, url: str, max_pages: int = 5) -> Dict:
        """
        Scrape both product metadata and reviews for a given URL.

        Returns:
            dict containing:
                "product_info": dict of metadata
                "reviews": list of review dicts formatted to the requested layout
        """
        platform = self._detect_platform(url)
        if not platform:
            raise ValueError(f"Unsupported URL platform. Must be Amazon or Flipkart: {url}")

        scraper = self._amazon if platform == "amazon" else self._flipkart
        logger.info("[ScraperService] Detected platform '{platform}' for URL", platform=platform)

        # Execute context manager life cycle
        async with scraper as active_scraper:
            # 1. Scrape product info
            product_info = await active_scraper.scrape_product_info(url)
            product_name = product_info.get("product_name", "Unknown Product")

            # 2. Scrape reviews
            raw_reviews = await active_scraper.scrape_reviews(url, max_pages=max_pages)

            # 3. Format reviews to the user-requested structure
            formatted_reviews: List[Dict] = []
            for r in raw_reviews:
                formatted_reviews.append({
                    "product_name": product_name,
                    "review": r["review_text"],
                    "rating": int(r["rating"]) if r["rating"] is not None else 5,
                    "review_date": r["review_date"].isoformat() if r["review_date"] else None,
                    "reviewer": r["reviewer"],
                    "source": "Amazon" if platform == "amazon" else "Flipkart",
                    "url": r["review_url"],
                })

            return {
                "product_info": product_info,
                "reviews": formatted_reviews,
            }
