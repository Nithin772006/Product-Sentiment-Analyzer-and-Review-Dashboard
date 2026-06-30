"""
app/scraper/base_scraper.py
────────────────────────────
Abstract base class that all platform scrapers must inherit from.
Delegates HTML fetching to ScraperManager and provides a clean interface.
"""
from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Dict, List, Optional
from bs4 import BeautifulSoup

from app.utils.logger import logger
from app.scraper.scraper_manager import ScraperManager


class BaseScraper(ABC):
    """
    Abstract scraper interface.
    Subclasses implement `scrape_product_info` and `scrape_reviews`.
    HTML fetching is delegated to ScraperManager which tries multiple strategies.
    """
    platform: str = "unknown"

    def __init__(self) -> None:
        self._manager = ScraperManager()
        logger.debug("Initialised {cls} scraper", cls=self.__class__.__name__)

    async def _fetch_soup(self, url: str) -> Optional[BeautifulSoup]:
        """Fetch a URL via ScraperManager and return parsed BS4 soup, or None."""
        html = await self._manager.get_html(url, platform=self.platform)
        if not html:
            return None
        return BeautifulSoup(html, "lxml")

    @abstractmethod
    async def scrape_product_info(self, url: str) -> Dict:
        raise NotImplementedError

    @abstractmethod
    async def scrape_reviews(self, url: str, max_pages: int = 5) -> List[Dict]:
        raise NotImplementedError

    async def __aenter__(self) -> "BaseScraper":
        return self

    async def __aexit__(self, *args) -> None:
        pass
