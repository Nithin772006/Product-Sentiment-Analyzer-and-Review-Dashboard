"""
app/scraper/amazon_scraper.py
──────────────────────────────
Amazon product review scraper.
Uses BaseScraper._fetch_soup() which delegates to ScraperManager (5-strategy cascade).
"""
from __future__ import annotations
import re
from typing import Dict, List, Optional
from urllib.parse import urlparse
from bs4 import BeautifulSoup

from app.scraper.base_scraper import BaseScraper
from app.scraper.review_parser import clean_text, parse_date, parse_rating
from app.scraper.review_extractor import clean_review_text, is_truncated_text
from app.utils.logger import logger


# ── Selectors ─────────────────────────────────────────────────────────────────

_REVIEW_BLOCK_SELECTORS = [
    "div[data-hook='review']",
    "div[data-hook='reviewContainer']",
    "div[id^='customer_review-']",
    "div[id^='R'][data-hook]",
    "li[data-hook='review']",
]

_REVIEW_BODY_SELECTORS = [
    "span[data-hook='review-body']",
    "[data-hook='review-body'] span",
    "span[data-hook='cr-original-review-content']",
    ".cr-original-review-content",
    "div[data-hook='review-collapsed']",
    "div[data-hook='review-expanded']",
    "div[data-hook='review-text']",
    "div[data-hook='reviewText'] span",
    ".review-text-content span",
    ".review-text-content",
    ".review-text span",
    ".review-text",
    ".review-data span",
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

_REVIEW_TITLE_SELECTORS = [
    "a[data-hook='review-title'] span",
    "span[data-hook='review-title'] span",
    "a.review-title span",
    ".review-title",
]

_REVIEW_UI_PATTERNS = [
    r"brief content visible,?\s*double tap to read full content\.?",
    r"double tap to read full content\.?",
    r"tap to read full content\.?",
    r"read more",
    r"read full review",
    r"see more",
    r"continue reading",
    r"read less",
    r"show less",
    r"show more",
    r"full content not available",
    r"click here to read",
    r"the media could not be loaded\.?",
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


def _remove_amazon_review_ui(text: str) -> str:
    cleaned = text
    for pattern in _REVIEW_UI_PATTERNS:
        cleaned = re.sub(pattern, " ", cleaned, flags=re.IGNORECASE)
    return clean_review_text(cleaned)


def _valid_review_text(text: str, min_len: int = 10) -> bool:
    if not text or len(text) < min_len:
        return False
    lower = text.lower()
    metadata_patterns = [
        r"^\d(?:\.\d)?\s*out of\s*5\s*stars$",
        r"^reviewed in .+ on .+$",
        r"^verified purchase$",
        r"^\d+ people found this helpful$",
        r"^one person found this helpful$",
        r"^helpful$",
        r"^report$",
    ]
    return not any(re.search(pattern, lower) for pattern in metadata_patterns)


def _extract_review_text(block) -> str:
    candidates = []
    for sel in _REVIEW_BODY_SELECTORS:
        for el in block.select(sel):
            cleaned = _remove_amazon_review_ui(el.get_text(separator=" "))
            if _valid_review_text(cleaned):
                candidates.append(cleaned)

    title = _remove_amazon_review_ui(_extract_field(block, _REVIEW_TITLE_SELECTORS))
    if _valid_review_text(title):
        candidates.append(title)
        if candidates:
            body = max(candidates, key=len)
            if title.lower() not in body.lower():
                merged = _remove_amazon_review_ui(f"{title}. {body}")
                if _valid_review_text(merged):
                    candidates.append(merged)

    for el in block.find_all(["span", "div", "p"], recursive=True):
        if el.find(["span", "div", "p"]):
            continue
        cleaned = _remove_amazon_review_ui(el.get_text(separator=" "))
        if _valid_review_text(cleaned, min_len=20) and not is_truncated_text(cleaned):
            candidates.append(cleaned)

    if not candidates:
        return ""
    return max(candidates, key=len)


def _find_review_blocks(soup: BeautifulSoup) -> List:
    for sel in _REVIEW_BLOCK_SELECTORS:
        blocks = soup.select(sel)
        valid = [b for b in blocks if len(clean_text(b.get_text(separator=" "))) > 40]
        if valid:
            return valid
    return []


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

    def __init__(self) -> None:
        super().__init__()
        self._last_product_url: Optional[str] = None
        self._last_product_soup: Optional[BeautifulSoup] = None

    def _extract_asin(self, url: str) -> Optional[str]:
        m = re.search(r"/(?:dp|gp/product|product-reviews|ASIN)/([A-Z0-9]{10})", url, re.IGNORECASE)
        if not m:
            m = re.search(r"[?&](?:asin|pd_rd_i)=([A-Z0-9]{10})", url, re.IGNORECASE)
        return m.group(1).upper() if m else None

    def _build_reviews_url(self, url: str, asin: str, page_num: int) -> str:
        parsed = urlparse(url)
        host = parsed.netloc or "www.amazon.in"
        if "amazon." not in host:
            host = "www.amazon.in"
        return (
            f"https://{host}/product-reviews/{asin}/"
            f"?pageNumber={page_num}&sortBy=recent"
        )

    async def scrape_product_info(self, url: str) -> Dict:
        logger.info(f"[Amazon] Fetching product info: {url[:80]}")
        soup = await self._fetch_soup(url)

        if not soup:
            logger.error("[Amazon] Failed to fetch product page.")
            return self._empty_info(url)

        self._last_product_url = url
        self._last_product_soup = soup

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

        all_reviews: List[Dict] = []

        for page_num in range(1, max_pages + 1):
            page_url = self._build_reviews_url(url, asin, page_num)
            logger.info(f"[Amazon] Scraping reviews page {page_num}: {page_url[:80]}")

            soup = await self._fetch_soup(page_url)
            if not soup:
                logger.warning(f"[Amazon] Failed to fetch review page {page_num}")
                break

            blocks = _find_review_blocks(soup)

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

        if not all_reviews:
            fallback_soup = self._last_product_soup if self._last_product_url == url else None
            if fallback_soup is None:
                logger.info("[Amazon] Review pages yielded 0 reviews; fetching product page fallback")
                fallback_soup = await self._fetch_soup(url)

            if fallback_soup:
                blocks = _find_review_blocks(fallback_soup)
                fallback_reviews = []
                for block in blocks[:20]:
                    r = _parse_review_block(block, url)
                    if r:
                        fallback_reviews.append(r)
                logger.info(f"[Amazon] Product page fallback extracted {len(fallback_reviews)} reviews")
                all_reviews.extend(fallback_reviews)

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
