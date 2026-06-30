"""
app/scraper/amazon_scraper.py
──────────────────────────────
Amazon product review scraper.
Uses BaseScraper._fetch_soup() which delegates to ScraperManager (5-strategy cascade).
"""
from __future__ import annotations
import re
from typing import Dict, List, Optional
from bs4 import BeautifulSoup

from app.scraper.base_scraper import BaseScraper
from app.scraper.review_parser import clean_text, parse_date, parse_rating
from app.scraper.review_extractor import clean_review_text, is_truncated_text
from app.utils.logger import logger


# ── Selectors ─────────────────────────────────────────────────────────────────

_REVIEW_BLOCK_SELECTORS = [
    "div[data-hook='review']",
    "div[data-hook='reviewContainer']",
    "li[data-hook='review']",
]

_REVIEW_BODY_SELECTORS = [
    "span[data-hook='review-body']",
    "span[data-hook='cr-original-review-content']",
    "div[data-hook='reviewText'] span",
    ".review-text-content span",
    ".review-text span",
    "div.a-expander-content span",
    "div[data-hook='review-body']",
]

_REVIEWER_SELECTORS = [
    "span.a-profile-name",
    "div.a-profile-name",
    "[data-hook='review-author']",
]

_STAR_SELECTORS = [
    "i[data-hook='review-star-rating'] span.a-icon-alt",
    "i[data-hook='cmps-review-star-rating'] span.a-icon-alt",
    "i.a-icon-star-small span.a-icon-alt",
    "i.a-icon-star span.a-icon-alt",
]

_DATE_SELECTORS = [
    "span[data-hook='review-date']",
    "span[data-hook='cr-review-date']",
]

_HELPFUL_SELECTORS = [
    "span[data-hook='helpful-vote-statement']",
    "span[data-hook='helpful-votes-count']",
]

_VERIFIED_SELECTORS = [
    "span[data-hook='avp-badge']",
    "[data-hook='avp-badge-linkless']",
]


# ── Helper functions ──────────────────────────────────────────────────────────

def _extract_field(block, selectors: list, default: str = "") -> str:
    for sel in selectors:
        el = block.select_one(sel)
        if el:
            text = clean_text(el.get_text(separator=" "))
            if text:
                return text
    return default


def _extract_review_text(block) -> str:
    candidates = []
    for sel in _REVIEW_BODY_SELECTORS:
        el = block.select_one(sel)
        if el:
            cleaned = clean_review_text(el.get_text(separator=" "))
            if cleaned and not is_truncated_text(cleaned) and len(cleaned) >= 10:
                candidates.append(cleaned)
    if not candidates:
        return ""
    return max(candidates, key=len)


def _parse_review_block(block, review_url: str) -> Optional[Dict]:
    reviewer = _extract_field(block, _REVIEWER_SELECTORS, "Anonymous")
    rating = parse_rating(_extract_field(block, _STAR_SELECTORS)) or 5.0
    review_date = parse_date(_extract_field(block, _DATE_SELECTORS))
    review_text = _extract_review_text(block)

    if not review_text:
        return None

    helpful_votes = 0
    helpful_text = _extract_field(block, _HELPFUL_SELECTORS)
    if helpful_text:
        m = re.search(r"(\d[\d,]*)", helpful_text)
        if m:
            helpful_votes = int(m.group(1).replace(",", ""))

    verified = any(block.select_one(s) is not None for s in _VERIFIED_SELECTORS)

    return {
        "reviewer": reviewer,
        "rating": rating,
        "review_text": review_text,
        "review_date": review_date,
        "helpful_votes": helpful_votes,
        "verified_purchase": verified,
        "source": "amazon",
        "review_url": review_url,
    }


# ── Main scraper ──────────────────────────────────────────────────────────────

class AmazonScraper(BaseScraper):
    platform = "amazon"

    def _extract_asin(self, url: str) -> Optional[str]:
        m = re.search(r"/(?:dp|gp/product|product-reviews|ASIN)/([A-Z0-9]{10})", url, re.IGNORECASE)
        return m.group(1).upper() if m else None

    async def scrape_product_info(self, url: str) -> Dict:
        logger.info(f"[Amazon] Fetching product info: {url[:80]}")
        soup = await self._fetch_soup(url)

        if not soup:
            logger.error("[Amazon] Failed to fetch product page.")
            return self._empty_info(url)

        name_el = soup.find(id="productTitle")
        product_name = clean_text(name_el.text) if name_el else "Unknown Product"

        brand_el = soup.find(id="bylineInfo")
        brand = clean_text(brand_el.text) if brand_el else None
        if brand:
            for noise in ["Visit the", "Visit The", "Store", "store", "Brand:"]:
                brand = brand.replace(noise, "").strip()

        rating_el = soup.select_one("#acrPopover span.a-icon-alt, span#acrPopover a i span.a-icon-alt")
        avg_rating = parse_rating(rating_el.text) if rating_el else 0.0

        total_reviews = 0
        for sel in ["#acrCustomerReviewText", "span[data-hook='total-review-count']", "#acrCustomerReviewLink span"]:
            el = soup.select_one(sel)
            if el:
                m = re.search(r"([\d,]+)", el.get_text())
                if m:
                    total_reviews = int(m.group(1).replace(",", ""))
                    break

        category = None
        for bc_sel in ["#wayfinding-breadcrumbs_container ul li a", ".a-breadcrumb li a"]:
            crumbs = soup.select(bc_sel)
            if crumbs:
                category = clean_text(crumbs[0].text)
                break

        logger.info(f"[Amazon] Product info scraped: {product_name[:50]}")
        return {
            "product_name": product_name,
            "brand": brand,
            "category": category or "General",
            "source": self.platform,
            "product_url": url,
            "average_rating": avg_rating or 0.0,
            "total_reviews": total_reviews,
        }

    async def scrape_reviews(self, url: str, max_pages: int = 5) -> List[Dict]:
        asin = self._extract_asin(url)
        if not asin:
            logger.warning(f"[Amazon] Cannot extract ASIN from: {url}")
            return []

        base_reviews_url = f"https://www.amazon.in/product-reviews/{asin}/"
        all_reviews: List[Dict] = []

        for page_num in range(1, max_pages + 1):
            page_url = f"{base_reviews_url}?pageNumber={page_num}&sortBy=recent&filterByStar=all_stars&reviewerType=all_reviews"
            logger.info(f"[Amazon] Scraping reviews page {page_num}: {page_url[:80]}")

            soup = await self._fetch_soup(page_url)
            if not soup:
                logger.warning(f"[Amazon] Failed to fetch review page {page_num}")
                break

            blocks = []
            for sel in _REVIEW_BLOCK_SELECTORS:
                blocks = soup.select(sel)
                if blocks:
                    break

            if not blocks:
                logger.info(f"[Amazon] No review blocks found on page {page_num}")
                break

            page_reviews = []
            for block in blocks:
                r = _parse_review_block(block, page_url)
                if r:
                    page_reviews.append(r)

            logger.info(f"[Amazon] Page {page_num}: extracted {len(page_reviews)} reviews")
            all_reviews.extend(page_reviews)

            if not page_reviews:
                break  # No more reviews

        logger.info(f"[Amazon] Total reviews scraped: {len(all_reviews)}")
        return all_reviews

    def _empty_info(self, url: str) -> Dict:
        return {
            "product_name": "Unknown Product",
            "brand": None,
            "category": "General",
            "source": self.platform,
            "product_url": url,
            "average_rating": 0.0,
            "total_reviews": 0,
        }
