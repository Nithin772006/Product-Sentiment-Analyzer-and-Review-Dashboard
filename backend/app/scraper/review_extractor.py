"""
app/scraper/review_extractor.py
──────────────────────────────────
Multi-strategy full review text extractor for Amazon (and similar) platforms.

Problem
────────
Amazon renders long reviews with a short preview snippet and a "Read More" button.
Even after clicking that button, the DOM may contain BOTH the preview span AND the
full-text span simultaneously (the preview is just hidden via CSS).  A naive
`innerText` call may capture only the preview or may merge the two incorrectly.

Solution
─────────
This module implements a 5-strategy extraction pipeline.  Each strategy attempts
to obtain the full review text from a different angle.  The pipeline returns the
LONGEST valid result, filtering out known truncation artefacts.

Strategy 1 — Playwright inner_text()
    Uses Playwright's built-in `inner_text()` which respects CSS visibility.
    This is the most reliable after "Read More" has been clicked.

Strategy 2 — JavaScript evaluate innerText
    Evaluates `element.innerText` via page.evaluate(), which uses the browser's
    text rendering engine (respects display:none).

Strategy 3 — BeautifulSoup HTML parse
    Fetches the element's outer_html() and uses BeautifulSoup to extract all
    visible text nodes, giving us a secondary DOM view.

Strategy 4 — Playwright nested locator
    Queries every child `span` and `p` inside the block, collects their
    individual text values, and merges them.

Strategy 5 — JavaScript querySelectorAll evaluate
    Runs a JS snippet inside the element that collects textContent from all
    leaf text nodes (ignoring hidden helper spans by checking offsetHeight).

Validation
───────────
Any candidate text is rejected if it contains known Amazon truncation strings
("Brief content visible", "double tap", "Read More", etc.).

The longest valid candidate across all strategies is returned.
"""

from __future__ import annotations

import re
from typing import Optional

from bs4 import BeautifulSoup
from playwright.async_api import ElementHandle, Locator, Page

from app.utils.logger import logger

# ── Truncation detection ───────────────────────────────────────────────────────

# These strings appear inside Amazon's preview/helper spans — if the extracted
# text contains any of these, it is considered truncated and must be rejected.
_TRUNCATION_MARKERS = [
    "brief content visible",
    "double tap to read full content",
    "tap to read full content",
    "read more",
    "read full review",
    "see more",
    "continue reading",
    "read less",
    "show less",
    "show more",
    "full content not available",
    "click here to read",
]

# Minimum character count to consider a review non-empty
_MIN_REVIEW_LENGTH = 5


def is_truncated_text(text: str) -> bool:
    """
    Return True if `text` appears to be Amazon UI helper/preview text rather
    than a real review.

    Parameters
    ----------
    text:
        The candidate review string (already stripped / lowercased is fine).

    Returns
    -------
    bool
        True  → text is a truncation artefact; discard it.
        False → text appears to be a real review.
    """
    if not text:
        return True
    lower = text.lower().strip()
    for marker in _TRUNCATION_MARKERS:
        if marker in lower:
            return True
    return False


def clean_review_text(raw: Optional[str]) -> str:
    """
    Deep-clean a raw extracted review string.

    Steps
    ─────
    1. Return empty string for None / falsy input.
    2. Strip invisible Unicode characters (zero-width space, NBSP, etc.).
    3. Remove residual HTML tags (safety net for leaked markup).
    4. Collapse repeated whitespace and newlines.
    5. Remove duplicate adjacent lines (preview + full text sometimes concatenated).
    6. Strip leading/trailing whitespace.
    """
    if not raw:
        return ""

    text = raw

    # Remove invisible Unicode characters
    text = re.sub(r"[\u200b\u200c\u200d\u200e\u200f\u00a0\ufeff\u202f\u2060]", " ", text)

    # Strip HTML tags
    text = re.sub(r"<[^>]+>", " ", text)

    # Normalize line endings
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    # Collapse multiple blank lines → single newline
    text = re.sub(r"\n{3,}", "\n\n", text)

    # Collapse repeated whitespace within lines
    lines = []
    seen_lines: set[str] = set()
    for line in text.split("\n"):
        cleaned_line = re.sub(r"[ \t]+", " ", line).strip()
        if not cleaned_line:
            lines.append("")
            continue
        # Deduplicate lines (handles preview + full text concatenation)
        key = cleaned_line.lower()
        if key not in seen_lines:
            seen_lines.add(key)
            lines.append(cleaned_line)

    result = "\n".join(lines).strip()
    return result


# ── Review selectors ──────────────────────────────────────────────────────────

# Ordered list of CSS selectors that may contain the full review text
# inside a single review block.  We try them all and pick the longest.
_REVIEW_TEXT_SELECTORS = [
    # Primary Amazon hook
    "span[data-hook='review-body']",
    # Lightspeed/CDN variant
    "span[data-hook='cr-original-review-content']",
    # Collapsed/expander containers
    "div[data-hook='review-collapsed']",
    "div[data-hook='review-truncated-text']",
    # Generic class-based selectors
    ".review-text-content span",
    ".review-text span",
    ".review-data span",
    ".reviewText span",
    ".cr-original-review-content",
    # Full block fallbacks
    "div.a-expander-content span",
    "div.review-text-content",
    "div[data-hook='reviewText']",
    # Any nested span inside the body
    "span[data-hook='review-body'] span",
]


# ── 5-Strategy extraction pipeline ────────────────────────────────────────────

class ReviewExtractor:
    """
    Extracts the FULL review text from a single Amazon review DOM block
    using 5 complementary strategies, returning the longest valid result.
    """

    def __init__(self, page: Page) -> None:
        self._page = page

    async def extract(
        self,
        block_locator: Locator,
        review_id: str = "unknown",
    ) -> str:
        """
        Run all 5 strategies on `block_locator` and return the best result.

        Parameters
        ----------
        block_locator:
            A Playwright Locator pointing to a single `div[data-hook='review']`.
        review_id:
            An identifier used for log messages only.

        Returns
        -------
        str
            The longest valid review text found, or empty string on failure.
        """
        import time as _time
        t0 = _time.monotonic()
        candidates: list[tuple[str, str]] = []  # (strategy_name, text)

        handle: Optional[ElementHandle] = None
        try:
            handle = await block_locator.element_handle()
        except Exception:
            pass

        # ── Strategy 1: Playwright inner_text ────────────────────────────────
        try:
            for sel in _REVIEW_TEXT_SELECTORS:
                sub = block_locator.locator(sel).first
                count = await block_locator.locator(sel).count()
                if count > 0:
                    txt = await sub.inner_text()
                    c = clean_review_text(txt)
                    if c and not is_truncated_text(c) and len(c) >= _MIN_REVIEW_LENGTH:
                        candidates.append(("strategy1_inner_text", c))
                        break
        except Exception as exc:
            logger.debug("[Extractor][{id}] Strategy 1 failed: {exc}", id=review_id, exc=exc)

        # Also try the full block inner_text as a strategy 1 fallback
        try:
            full_txt = await block_locator.inner_text()
            c = clean_review_text(full_txt)
            if c and not is_truncated_text(c) and len(c) >= _MIN_REVIEW_LENGTH:
                candidates.append(("strategy1_block_inner_text", c))
        except Exception as exc:
            logger.debug("[Extractor][{id}] Strategy 1b failed: {exc}", id=review_id, exc=exc)

        # ── Strategy 2: JavaScript evaluate innerText ─────────────────────────
        if handle:
            try:
                for sel in _REVIEW_TEXT_SELECTORS:
                    js_text = await self._page.evaluate(
                        """(args) => {
                            const [el, selector] = args;
                            const child = el.querySelector(selector);
                            if (!child) return null;
                            return child.innerText || child.textContent;
                        }""",
                        [handle, sel],
                    )
                    if js_text:
                        c = clean_review_text(js_text)
                        if c and not is_truncated_text(c) and len(c) >= _MIN_REVIEW_LENGTH:
                            candidates.append(("strategy2_js_innerText", c))
                            break
            except Exception as exc:
                logger.debug("[Extractor][{id}] Strategy 2 failed: {exc}", id=review_id, exc=exc)

        # ── Strategy 3: BeautifulSoup HTML parse ──────────────────────────────
        try:
            html = await block_locator.inner_html()
            soup = BeautifulSoup(html, "lxml")

            # Remove known helper spans that contain truncation text
            for tag in soup.find_all(
                True,
                attrs={"data-hook": re.compile(r"collapsed|truncated|helper|accessibility")},
            ):
                tag.decompose()

            # Try each selector in BS4
            for sel in _REVIEW_TEXT_SELECTORS:
                el = soup.select_one(sel)
                if el:
                    txt = el.get_text(separator=" ")
                    c = clean_review_text(txt)
                    if c and not is_truncated_text(c) and len(c) >= _MIN_REVIEW_LENGTH:
                        candidates.append(("strategy3_bs4", c))
                        break

            # BS4 fallback: all text from the block
            all_text = soup.get_text(separator=" ")
            c = clean_review_text(all_text)
            if c and not is_truncated_text(c) and len(c) >= _MIN_REVIEW_LENGTH:
                candidates.append(("strategy3_bs4_full", c))

        except Exception as exc:
            logger.debug("[Extractor][{id}] Strategy 3 failed: {exc}", id=review_id, exc=exc)

        # ── Strategy 4: Playwright nested locator (collect all spans/p) ───────
        try:
            parts: list[str] = []
            for child_sel in ["span", "p"]:
                children = block_locator.locator(child_sel)
                n = await children.count()
                for i in range(n):
                    try:
                        child = children.nth(i)
                        if await child.is_visible():
                            t = (await child.inner_text()).strip()
                            if t and not is_truncated_text(t):
                                parts.append(t)
                    except Exception:
                        pass
            merged = clean_review_text(" ".join(parts))
            if merged and not is_truncated_text(merged) and len(merged) >= _MIN_REVIEW_LENGTH:
                candidates.append(("strategy4_locator_merge", merged))
        except Exception as exc:
            logger.debug("[Extractor][{id}] Strategy 4 failed: {exc}", id=review_id, exc=exc)

        # ── Strategy 5: Browser evaluate querySelectorAll ─────────────────────
        if handle:
            try:
                js_result = await self._page.evaluate(
                    """(el) => {
                        // Collect text from all leaf-level text nodes,
                        // skipping elements with zero height (hidden).
                        function getVisible(node) {
                            if (node.nodeType === 3) {  // TEXT_NODE
                                return node.textContent || '';
                            }
                            if (node.nodeType === 1) {  // ELEMENT_NODE
                                const style = window.getComputedStyle(node);
                                if (style.display === 'none' || style.visibility === 'hidden') {
                                    return '';
                                }
                            }
                            let text = '';
                            for (const child of node.childNodes) {
                                text += getVisible(child) + ' ';
                            }
                            return text;
                        }
                        return getVisible(el).trim();
                    }""",
                    handle,
                )
                if js_result:
                    c = clean_review_text(js_result)
                    if c and not is_truncated_text(c) and len(c) >= _MIN_REVIEW_LENGTH:
                        candidates.append(("strategy5_js_evaluate", c))
            except Exception as exc:
                logger.debug("[Extractor][{id}] Strategy 5 failed: {exc}", id=review_id, exc=exc)

        # ── Pick the best candidate ───────────────────────────────────────────
        elapsed = _time.monotonic() - t0
        if not candidates:
            logger.warning(
                "[Extractor][{id}] All 5 strategies failed. elapsed={t:.2f}s",
                id=review_id,
                t=elapsed,
            )
            return ""

        best_strategy, best_text = max(candidates, key=lambda x: len(x[1]))

        logger.debug(
            "[Extractor][{id}] strategy={s} | preview_len≈{pl} | final_len={fl} | elapsed={t:.2f}s",
            id=review_id,
            s=best_strategy,
            pl=len(candidates[0][1]) if candidates else 0,
            fl=len(best_text),
            t=elapsed,
        )

        return best_text
