"""
app/scraper/flipkart_scraper.py
────────────────────────────────
Flipkart product review scraper.
Uses BaseScraper._fetch_soup() which delegates to ScraperManager (multi-strategy cascade).
"""
from __future__ import annotations
import re
from typing import Dict, List, Optional
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
from bs4 import BeautifulSoup

from app.scraper.base_scraper import BaseScraper
from app.scraper.review_parser import clean_text, parse_date, parse_rating
from app.scraper.review_extractor import clean_review_text, is_truncated_text
from app.utils.logger import logger


# ── Selectors ─────────────────────────────────────────────────────────────────

_REVIEW_BLOCK_SELECTORS = [
    "div.EKGNAx",
    "div.col.EPC75C",
    "div._27M2j0",
    "div.col._2w18Vo",
    "div._1w9jov",
    "div[data-id]",
]

_REVIEW_BODY_SELECTORS = [
    "div.ZmyHe8", "div.t-yD1B", "div.qwjRZE", "div._6K-7Co",
    "div._2xg67Y", "div.rQJvmz", "p.z9E0IG", "p._2-N8I7", "p.mD01Gk",
]

_REVIEW_TITLE_SELECTORS = [
    "p.iubmB6", "p._2-N1sw", "p._2xg67Y", "p.h4YBOe",
]

_REVIEWER_SELECTORS = [
    "p._2Ns42I", "p._2sc77z", "p.X1KTa3", "span._3gEIov", "p.d1WRmK", "p._2NsDsY",
]

_STAR_SELECTORS = [
    "div.XQD0XM", "div._3LWZlK", "div._1blX12", "div.ipCw58",
    "div._3c3wQu", "span._3LWZlK", "span.XQD0XM",
]

_DATE_SELECTORS = [
    "p._2sc77z", "span._3nPIwX", "p.X1KTa3", "span._1m4GG5", "p.HtbApb",
]

_HELPFUL_SELECTORS = [
    "span._1LcoK7", "span._3c3wQu", "span._2dB37Z", "span._1CKaXJ",
]

_VERIFIED_SELECTORS = ["p._2mc13F", "span._1ve7Go"]

_PRODUCT_NAME_SELECTORS = [
    "span.VU-ZEz", "h1 span", "h1.yhB1nd", "span.B_NuCI", "div.B_NuCI", "h1",
]

_RATING_SELECTORS = [
    "div.ipCw58", "div.XQD0XM", "div._3LWZlK", "span.Y1HWO0",
    "div._2d4LTz", "span._2_OkBI",
]

_REVIEW_COUNT_SELECTORS = [
    "span.W1Z0nJ", "span._2_R_DZ", "span.t-yD1B", "span._1YokD2",
    "div._3Qzlid span", "span._13vcmD",
]

_BREADCRUMB_SELECTORS = [
    "div.r2C5H9 a", "div._3GIr1Z a", "div.aw9OGe a", "a._1LKTO3", "nav a",
]


# ── Helper functions ──────────────────────────────────────────────────────────

def _to_reviews_url(url: str) -> str:
    parsed = urlparse(url)
    params = parse_qs(parsed.query, keep_blank_values=True)
    clean_params = {k: v for k, v in params.items() if k == "pid"}
    clean_query = urlencode(clean_params, doseq=True)
    if "product-reviews" in parsed.path:
        new_path = parsed.path
    elif "/p/" in parsed.path:
        new_path = parsed.path.replace("/p/", "/product-reviews/")
    else:
        new_path = parsed.path
    new_parsed = parsed._replace(path=new_path, query=clean_query, fragment="")
    return urlunparse(new_parsed)


def _extract_field(block, selectors: list, default: str = "") -> str:
    for sel in selectors:
        el = block.select_one(sel)
        if el:
            text = clean_text(el.get_text(separator=" "))
            if text and len(text) > 1:
                return text
    return default


def _find_review_blocks(soup: BeautifulSoup) -> list:
    # Try known class selectors first
    for sel in _REVIEW_BLOCK_SELECTORS:
        if sel == "div[data-id]":
            continue  # handled below
        blocks = soup.select(sel)
        valid = [b for b in blocks if len(b.get_text(strip=True)) > 20]
        if len(valid) >= 2:
            return valid

    # Fallback: data-id divs with enough content
    data_id_divs = [
        d for d in soup.find_all("div", attrs={"data-id": True})
        if len(d.get_text(strip=True)) > 30
    ]
    return data_id_divs


def _extract_review_text(block) -> str:
    candidates = []
    for sel in _REVIEW_BODY_SELECTORS:
        el = block.select_one(sel)
        if el:
            cleaned = clean_review_text(el.get_text(separator=" "))
            if cleaned and not is_truncated_text(cleaned) and len(cleaned) >= 10:
                candidates.append(cleaned)

    # Try merging title + body
    title = _extract_field(block, _REVIEW_TITLE_SELECTORS)
    body = candidates[0] if candidates else ""
    if title and body and title.lower() not in body.lower():
        merged = clean_review_text(f"{title}. {body}")
        if merged and not is_truncated_text(merged):
            candidates.append(merged)
    elif title and not body:
        cleaned = clean_review_text(title)
        if cleaned and not is_truncated_text(cleaned) and len(cleaned) >= 10:
            candidates.append(cleaned)

    # Fallback: longest paragraph
    for para in block.find_all(["p", "div"], recursive=True):
        if para.name == "div" and len(para.find_all(recursive=False)) > 3:
            continue
        cleaned = clean_review_text(para.get_text(separator=" "))
        if (
            cleaned and not is_truncated_text(cleaned) and len(cleaned) >= 20
            and not re.search(r"^\d+\s*(month|day|year|week|rating|star)", cleaned.lower())
        ):
            candidates.append(cleaned)

    if not candidates:
        return ""
    return max(candidates, key=len)


def _extract_rating(block) -> float:
    for sel in _STAR_SELECTORS:
        el = block.select_one(sel)
        if el:
            r = parse_rating(el.get_text(strip=True))
            if r is not None:
                return r
    return 5.0


def _extract_date(block):
    for sel in _DATE_SELECTORS:
        for el in block.select(sel):
            text = el.get_text(strip=True)
            if re.search(r"\d{4}|ago|month|day|year|week", text.lower()):
                dt = parse_date(text)
                if dt:
                    return dt
    return parse_date(None)


def _parse_review_block(block, review_url: str) -> Optional[Dict]:
    reviewer = _extract_field(block, _REVIEWER_SELECTORS, "Anonymous")
    rating = _extract_rating(block)
    review_date = _extract_date(block)
    review_text = _extract_review_text(block)

    if not review_text:
        return None

    helpful_votes = 0
    helpful_text = _extract_field(block, _HELPFUL_SELECTORS)
    if helpful_text:
        m = re.search(r"(\d[\d,]*)", helpful_text)
        if m:
            helpful_votes = int(m.group(1).replace(",", ""))

    verified = (
        any(block.select_one(s) is not None for s in _VERIFIED_SELECTORS)
        or "certified buyer" in block.get_text().lower()
        or "verified purchase" in block.get_text().lower()
    )

    return {
        "reviewer": reviewer,
        "rating": rating,
        "review_text": review_text,
        "review_date": review_date,
        "helpful_votes": helpful_votes,
        "verified_purchase": verified,
        "source": "flipkart",
        "review_url": review_url,
    }


# ── Main scraper ──────────────────────────────────────────────────────────────

class FlipkartScraper(BaseScraper):
    platform = "flipkart"

    async def scrape_product_info(self, url: str) -> Dict:
        logger.info(f"[Flipkart] Fetching product info: {url[:80]}")
        soup = await self._fetch_soup(url)

        if not soup:
            logger.error("[Flipkart] Failed to fetch product page.")
            return self._empty_info(url)

        product_name = "Unknown Product"
        for sel in _PRODUCT_NAME_SELECTORS:
            el = soup.select_one(sel)
            if el:
                product_name = clean_text(el.get_text(separator=" "))
                if product_name and product_name != "Unknown Product":
                    break

        brand = None
        brand_el = soup.select_one("span.G6XhRU, a._2r_T1I, span._1RkS0B")
        if brand_el:
            brand = clean_text(brand_el.text)
        elif product_name and product_name != "Unknown Product":
            parts = product_name.split()
            if parts:
                brand = parts[0]

        avg_rating = 0.0
        for sel in _RATING_SELECTORS:
            el = soup.select_one(sel)
            if el:
                r = parse_rating(el.get_text(strip=True))
                if r is not None:
                    avg_rating = r
                    break

        total_reviews = 0
        for sel in _REVIEW_COUNT_SELECTORS:
            el = soup.select_one(sel)
            if el:
                text = el.get_text()
                m = (
                    re.search(r"([\d,]+)\s*[Rr]atings?", text)
                    or re.search(r"([\d,]+)\s*[Rr]eviews?", text)
                    or re.search(r"([\d,]+)", text)
                )
                if m:
                    total_reviews = int(m.group(1).replace(",", ""))
                    break

        category = None
        for sel in _BREADCRUMB_SELECTORS:
            crumbs = soup.select(sel)
            if crumbs:
                category = clean_text(crumbs[-1].get_text())
                break

        logger.info(f"[Flipkart] Product info scraped: {product_name[:50]}")
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
        reviews_base = _to_reviews_url(url)
        all_reviews: List[Dict] = []

        for page_num in range(1, max_pages + 1):
            join = "&" if "?" in reviews_base else "?"
            page_url = f"{reviews_base}{join}page={page_num}"
            logger.info(f"[Flipkart] Scraping reviews page {page_num}: {page_url[:80]}")

            soup = await self._fetch_soup(page_url)
            if not soup:
                logger.warning(f"[Flipkart] Failed to fetch review page {page_num}")
                break

            blocks = _find_review_blocks(soup)
            if not blocks:
                logger.info(f"[Flipkart] No review blocks found on page {page_num}")
                break

            page_reviews = []
            for block in blocks[:50]:
                r = _parse_review_block(block, page_url)
                if r:
                    page_reviews.append(r)

            logger.info(f"[Flipkart] Page {page_num}: extracted {len(page_reviews)} reviews")
            all_reviews.extend(page_reviews)

            if not page_reviews:
                break

        logger.info(f"[Flipkart] Total reviews scraped: {len(all_reviews)}")
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
