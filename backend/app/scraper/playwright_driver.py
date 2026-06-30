"""
app/scraper/playwright_driver.py
──────────────────────────────────
Async Playwright Chromium helper for robust, human-like scraping.

Responsibilities
─────────────────
• Launch a stealthy Chromium browser (headless or headed).
• Rotate user-agents and randomise viewports.
• Simulate human-like mouse movement and scrolling.
• Navigate pages with network-idle waits and jitter delays.
• Expand ALL collapsed review sections (Read More / See More buttons).
• Provide async context manager lifecycle for clean resource cleanup.
"""

from __future__ import annotations

import asyncio
import os
import random
import time
from pathlib import Path
from typing import Optional

from fake_useragent import UserAgent
from playwright.async_api import (
    Browser,
    BrowserContext,
    Page,
    Playwright,
    async_playwright,
)

from app.config import get_settings
from app.utils.logger import logger

# ── Constants ─────────────────────────────────────────────────────────────────

# Buttons that expand truncated review text (case-insensitive partial match)
_EXPAND_BUTTON_TEXTS = [
    "read more",
    "see more",
    "continue reading",
    "expand",
    "show more",
    "read full review",
    "tap to read",
    "view more",
]

# CSS selectors that may contain "expand" type buttons inside a review block
_EXPAND_SELECTORS = [
    "span[data-hook='review-collapsed']",
    "a[data-hook='review-read-more']",
    "a.review-read-more",
    "a.a-expander-see-more",
    "button.a-expander-header",
    "a.cr-read-more",
    ".a-expander-see-more",
    ".cr-review-see-more-link",
    "span.cr-lightspeed-review-list-body a",
    "div[data-hook='review'] a",
]

# Screenshots saved here for debugging failures
_SCREENSHOT_DIR = Path(__file__).resolve().parents[3] / "static" / "screenshots"


class PlaywrightDriver:
    """
    Async context manager wrapping a Playwright Chromium browser.

    Usage::

        async with PlaywrightDriver() as driver:
            page = await driver.new_page()
            await driver.goto_with_retry(page, url)
            await driver.expand_all_reviews(page)
    """

    def __init__(self, headless: Optional[bool] = None) -> None:
        self._settings = get_settings()
        self._headless = headless if headless is not None else self._settings.scraper_headless
        self._ua = UserAgent(
            platforms="desktop",
            fallback="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                     "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        )
        self._playwright: Optional[Playwright] = None
        self._browser: Optional[Browser] = None
        self._context: Optional[BrowserContext] = None
        _SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)

    # ── Lifecycle ─────────────────────────────────────────────────────────────

    async def __aenter__(self) -> "PlaywrightDriver":
        await self._launch()
        return self

    async def __aexit__(self, *args) -> None:
        await self._close()

    async def _launch(self) -> None:
        """Start Playwright and launch a stealth Chromium browser."""
        self._playwright = await async_playwright().start()

        user_agent = self._ua.random
        viewport_width = random.randint(1280, 1920)
        viewport_height = random.randint(720, 1080)

        logger.debug(
            "[Playwright] Launching Chromium | headless={h} | UA={ua} | viewport={w}x{h2}",
            h=self._headless,
            ua=user_agent[:60],
            w=viewport_width,
            h2=viewport_height,
        )

        self._browser = await self._playwright.chromium.launch(
            headless=self._headless,
            args=[
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--disable-blink-features=AutomationControlled",
                "--disable-infobars",
                "--disable-extensions",
            ],
        )

        self._context = await self._browser.new_context(
            user_agent=user_agent,
            viewport={"width": viewport_width, "height": viewport_height},
            locale="en-US",
            timezone_id="Asia/Kolkata",
            extra_http_headers={
                "Accept-Language": "en-US,en;q=0.9",
                "Accept": (
                    "text/html,application/xhtml+xml,application/xml;q=0.9,"
                    "image/avif,image/webp,*/*;q=0.8"
                ),
                "DNT": "1",
            },
        )

        # Inject stealth JS to hide navigator.webdriver
        await self._context.add_init_script(
            """
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
            Object.defineProperty(navigator, 'plugins', {get: () => [1,2,3,4,5]});
            Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']});
            window.chrome = {runtime: {}};
            """
        )

    async def _close(self) -> None:
        """Close the browser and Playwright instance."""
        try:
            if self._context:
                await self._context.close()
            if self._browser:
                await self._browser.close()
            if self._playwright:
                await self._playwright.stop()
        except Exception as exc:
            logger.warning("[Playwright] Error during teardown: {exc}", exc=exc)
        finally:
            self._context = None
            self._browser = None
            self._playwright = None
            logger.debug("[Playwright] Browser closed.")

    # ── Page creation ─────────────────────────────────────────────────────────

    async def new_page(self) -> Page:
        """Open and return a new browser tab."""
        if not self._context:
            raise RuntimeError("PlaywrightDriver not started. Use `async with` context.")
        page = await self._context.new_page()
        return page

    # ── Navigation ────────────────────────────────────────────────────────────

    async def goto_with_retry(
        self,
        page: Page,
        url: str,
        retries: int = 3,
        wait_until: str = "domcontentloaded",
    ) -> bool:
        """
        Navigate to `url` with retry logic and human-like delays.

        Returns True on success, False if all retries fail.
        """
        for attempt in range(1, retries + 1):
            try:
                logger.debug(
                    "[Playwright] Navigating to {url} (attempt {attempt}/{retries})",
                    url=url[:80],
                    attempt=attempt,
                    retries=retries,
                )
                await page.goto(url, wait_until=wait_until, timeout=30_000)

                # Random jitter after page load
                await self._human_delay(page)
                return True

            except Exception as exc:
                logger.warning(
                    "[Playwright] Navigation attempt {attempt} failed: {exc}",
                    attempt=attempt,
                    exc=exc,
                )
                if attempt < retries:
                    await asyncio.sleep(random.uniform(2, 5))
                else:
                    return False
        return False

    # ── Human-like behaviour ──────────────────────────────────────────────────

    async def _human_delay(self, page: Page) -> None:
        """Wait a random interval and simulate scrolling to look human."""
        delay = random.uniform(
            self._settings.scraper_delay_min,
            self._settings.scraper_delay_max,
        )
        await asyncio.sleep(delay)
        await self._random_scroll(page)

    async def _random_scroll(self, page: Page) -> None:
        """Scroll the page randomly to simulate reading behaviour."""
        try:
            scroll_amount = random.randint(200, 800)
            await page.mouse.wheel(0, scroll_amount)
            await asyncio.sleep(random.uniform(0.3, 0.8))
            # Occasionally scroll back up a bit
            if random.random() < 0.3:
                await page.mouse.wheel(0, -random.randint(50, 200))
        except Exception:
            pass  # Non-critical

    async def _simulate_mouse_movement(self, page: Page) -> None:
        """Move the mouse to random positions to mimic human activity."""
        try:
            for _ in range(random.randint(2, 5)):
                x = random.randint(100, 1200)
                y = random.randint(100, 700)
                await page.mouse.move(x, y)
                await asyncio.sleep(random.uniform(0.05, 0.2))
        except Exception:
            pass  # Non-critical

    # ── Review expansion ──────────────────────────────────────────────────────

    async def expand_all_reviews(self, page: Page) -> int:
        """
        Find and click all "Read More / See More / Continue Reading" buttons
        on the current page to reveal full review text.

        Returns the number of buttons successfully clicked.
        """
        clicked_total = 0

        # Strategy A: Click by visible text content
        for btn_text in _EXPAND_BUTTON_TEXTS:
            try:
                # Playwright's get_by_role / get_by_text with case-insensitive partial match
                buttons = page.get_by_role("link", name=btn_text).or_(
                    page.get_by_role("button", name=btn_text)
                )
                count = await buttons.count()
                for i in range(count):
                    try:
                        btn = buttons.nth(i)
                        if await btn.is_visible():
                            await btn.scroll_into_view_if_needed()
                            await asyncio.sleep(random.uniform(0.2, 0.5))
                            await btn.click()
                            await asyncio.sleep(random.uniform(0.3, 0.7))
                            clicked_total += 1
                    except Exception:
                        pass
            except Exception:
                pass

        # Strategy B: Click by known CSS selectors
        for selector in _EXPAND_SELECTORS:
            try:
                elements = page.locator(selector)
                count = await elements.count()
                for i in range(count):
                    try:
                        el = elements.nth(i)
                        if await el.is_visible():
                            text = (await el.inner_text()).strip().lower()
                            if any(t in text for t in _EXPAND_BUTTON_TEXTS):
                                await el.scroll_into_view_if_needed()
                                await asyncio.sleep(random.uniform(0.2, 0.5))
                                await el.click()
                                await asyncio.sleep(random.uniform(0.3, 0.7))
                                clicked_total += 1
                    except Exception:
                        pass
            except Exception:
                pass

        # Strategy C: JavaScript click on any anchor containing expand text
        try:
            js_clicks = await page.evaluate(
                """
                () => {
                    const expandTexts = [
                        'read more', 'see more', 'continue reading',
                        'read full review', 'show more', 'tap to read', 'view more'
                    ];
                    const links = Array.from(document.querySelectorAll('a, button, span[role="button"]'));
                    let clicked = 0;
                    for (const el of links) {
                        const txt = (el.innerText || el.textContent || '').toLowerCase().trim();
                        if (expandTexts.some(t => txt.includes(t))) {
                            try { el.click(); clicked++; } catch(e) {}
                        }
                    }
                    return clicked;
                }
                """
            )
            clicked_total += js_clicks or 0
        except Exception:
            pass

        if clicked_total > 0:
            # Wait for DOM to settle after expansion clicks
            await asyncio.sleep(random.uniform(0.5, 1.2))

        logger.debug("[Playwright] expand_all_reviews: clicked {n} buttons.", n=clicked_total)
        return clicked_total

    # ── Screenshot ────────────────────────────────────────────────────────────

    async def take_screenshot(self, page: Page, name: str) -> Optional[Path]:
        """Save a debug screenshot to the static/screenshots directory."""
        try:
            ts = int(time.time())
            safe_name = "".join(c if c.isalnum() or c in "-_" else "_" for c in name)
            path = _SCREENSHOT_DIR / f"{safe_name}_{ts}.png"
            await page.screenshot(path=str(path), full_page=False)
            logger.info("[Playwright] Screenshot saved: {path}", path=path)
            return path
        except Exception as exc:
            logger.warning("[Playwright] Failed to take screenshot: {exc}", exc=exc)
            return None
