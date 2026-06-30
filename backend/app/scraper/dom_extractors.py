"""
app/scraper/dom_extractors.py
─────────────────────────────
Robust multi-selector extraction and text cleaning.
"""
from typing import List, Optional
from bs4 import BeautifulSoup
from playwright.async_api import Page
import re
from app.utils.logger import logger

class DOMExtractor:
    """Methods to extract text robustly from BS4 or Playwright DOM."""

    @staticmethod
    def clean_text(raw_text: str) -> str:
        """Removes duplicate whitespace, UI clutter, and invisible chars."""
        if not raw_text:
            return ""
            
        # Common UI clutter to remove
        clutter = [
            "read more", "read less", "see more", "see less",
            "continue reading", "brief content visible", "double tap",
            "expand", "show more"
        ]
        
        text = raw_text.lower()
        for c in clutter:
            text = text.replace(c, "")
            
        # Re-apply to original case for the cleaned string
        # Actually a better approach is regex substitution ignoring case
        cleaned = raw_text
        for c in clutter:
            cleaned = re.sub(f"(?i){c}", "", cleaned)
            
        # Clean whitespace and newlines
        cleaned = re.sub(r"\s+", " ", cleaned)
        return cleaned.strip()

    @staticmethod
    def extract_from_soup(soup: BeautifulSoup, selectors: List[str], default: str = "") -> str:
        """Tries multiple CSS selectors on a BS4 soup object and returns the longest valid text."""
        candidates = []
        for sel in selectors:
            elements = soup.select(sel)
            for el in elements:
                text = DOMExtractor.clean_text(el.get_text(separator=" "))
                if len(text) > 2:
                    candidates.append(text)
        
        if not candidates:
            return default
            
        # Return longest
        return max(candidates, key=len)

    @staticmethod
    async def extract_from_page(page: Page, selectors: List[str], default: str = "") -> str:
        """Tries multiple CSS selectors on a Playwright page and returns the longest valid text."""
        candidates = []
        for sel in selectors:
            try:
                elements = await page.locator(sel).all()
                for el in elements:
                    text = await el.inner_text()
                    cleaned = DOMExtractor.clean_text(text)
                    if len(cleaned) > 2:
                        candidates.append(cleaned)
            except Exception:
                continue
                
        if not candidates:
            return default
            
        return max(candidates, key=len)

    @staticmethod
    async def expand_all(page: Page, selectors: List[str]):
        """Clicks on 'Read More' or 'Expand' elements to reveal full text."""
        for sel in selectors:
            try:
                locators = await page.locator(sel).all()
                for loc in locators:
                    if await loc.is_visible():
                        await loc.click(timeout=1000)
            except Exception:
                continue
