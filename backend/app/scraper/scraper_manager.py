"""
app/scraper/scraper_manager.py
──────────────────────────────
Orchestrates multiple scraping strategies to retrieve HTML from a URL.
Each strategy is responsible for fetching the page HTML.
The scraper then parses the HTML with BeautifulSoup independently.
"""
from __future__ import annotations
import asyncio
import random
import httpx
from pathlib import Path
from typing import Optional
from playwright.async_api import async_playwright
from playwright_stealth import Stealth
from app.utils.logger import logger
from app.scraper.fingerprint import fingerprint_manager

PROFILE_DIR = Path(__file__).resolve().parents[3] / "backend" / "browser_profile"


async def _try_persistent_profile(url: str, headless: bool = True) -> Optional[str]:
    """
    Strategy 0 (Highest Priority): Uses real Chrome with a persistent profile directory.
    Cookies and session data are preserved between runs.
    This is the most reliable strategy for sites like Amazon that require login sessions.
    """
    try:
        PROFILE_DIR.mkdir(parents=True, exist_ok=True)
        async with async_playwright() as pw:
            stealth_obj = Stealth()
            context = await pw.chromium.launch_persistent_context(
                user_data_dir=str(PROFILE_DIR),
                channel="chrome",
                headless=False,  # Force headed mode to bypass strict headless checks
                viewport={"width": 1920, "height": 1080},
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--no-sandbox",
                    "--disable-dev-shm-usage",
                ],
                java_script_enabled=True,
            )
            page = await context.new_page()
            await stealth_obj.apply_stealth_async(page)
            await page.goto(url, timeout=35000, wait_until="domcontentloaded")
            await asyncio.sleep(random.uniform(2, 4))
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight / 3)")
            await asyncio.sleep(1.5)
            html = await page.content()
            await context.close()
            return html
    except Exception as e:
        logger.warning(f"[ScraperManager] Strategy 0 (Persistent Profile) failed: {e}")
        return None


async def _try_playwright_stealth(url: str, headless: bool = True) -> Optional[str]:
    """Strategy 1: Playwright with stealth mode using installed Chromium."""
    try:
        async with async_playwright() as pw:
            browser = await pw.chromium.launch(
                headless=False,  # Force headed mode
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--no-sandbox",
                    "--disable-dev-shm-usage",
                ]
            )
            stealth_obj = Stealth()
            context = await browser.new_context(
                viewport={"width": 1920, "height": 1080},
                java_script_enabled=True,
            )
            page = await context.new_page()
            await stealth_obj.apply_stealth_async(page)
            await page.goto(url, timeout=30000, wait_until="domcontentloaded")
            await asyncio.sleep(random.uniform(2, 4))
            # Scroll down to trigger lazy loading
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight / 2)")
            await asyncio.sleep(1)
            html = await page.content()
            await browser.close()
            return html
    except Exception as e:
        logger.warning(f"[ScraperManager] Strategy 1 (Playwright Stealth) failed: {e}")
        return None


async def _try_playwright_fingerprint(url: str, headless: bool = True) -> Optional[str]:
    """Strategy 2: Playwright with randomized fingerprint using installed Chromium."""
    try:
        fp = fingerprint_manager.get_fingerprint()
        async with async_playwright() as pw:
            browser = await pw.chromium.launch(
                headless=headless,
                args=["--disable-blink-features=AutomationControlled", "--no-sandbox"]
            )
            context = await browser.new_context(
                user_agent=fp.navigator.userAgent,
                viewport={"width": 1920, "height": 1080},
                locale=fp.navigator.language or "en-US",
                java_script_enabled=True,
            )
            await context.add_init_script(
                "Object.defineProperty(navigator, 'webdriver', {get: () => undefined});"
            )
            page = await context.new_page()
            await page.goto(url, timeout=30000, wait_until="domcontentloaded")
            await asyncio.sleep(random.uniform(2, 3))
            html = await page.content()
            await browser.close()
            return html
    except Exception as e:
        logger.warning(f"[ScraperManager] Strategy 2 (Playwright Fingerprint) failed: {e}")
        return None


async def _try_httpx(url: str) -> Optional[str]:
    """Strategy 3: Direct HTTPX request with realistic headers."""
    fp = fingerprint_manager.get_fingerprint()
    headers = {
        "User-Agent": fp.navigator.userAgent,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": fp.navigator.language or "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "DNT": "1",
        "Upgrade-Insecure-Requests": "1",
        "Connection": "keep-alive",
        "Cache-Control": "max-age=0",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
    }
    try:
        async with httpx.AsyncClient(follow_redirects=True, timeout=20.0, headers=headers) as client:
            resp = await client.get(url)
            if resp.status_code == 200:
                return resp.text
            logger.warning(f"[ScraperManager] Strategy 3 (HTTPX) got HTTP {resp.status_code}")
            return None
    except Exception as e:
        logger.warning(f"[ScraperManager] Strategy 3 (HTTPX) failed: {e}")
        return None


def _try_selenium(url: str) -> Optional[str]:
    """Strategy 4: Undetected Chromedriver fallback."""
    try:
        import undetected_chromedriver as uc
        import time

        logger.debug("[ScraperManager] Setting up Undetected Chrome WebDriver...")
        options = uc.ChromeOptions()

        # Headless mode config
        from app.config import get_settings
        settings = get_settings()
        if settings.scraper_headless:
            options.headless = True
            options.add_argument('--headless')

        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--disable-popup-blocking")

        driver = uc.Chrome(options=options, version_main=149)
        driver.set_page_load_timeout(45)

        try:
            driver.get(url)
            time.sleep(random.uniform(3, 5))
            
            # Simple human scroll
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight / 3);")
            time.sleep(2)
            
            return driver.page_source
        finally:
            driver.quit()
    except ImportError:
        logger.warning("[ScraperManager] undetected_chromedriver not installed.")
        return None
    except Exception as e:
        logger.warning(f"[ScraperManager] Strategy 4 (Selenium) failed: {e}")
        return None


def _is_blocked(html: str, platform: str) -> bool:
    """Check if HTML content indicates a block/redirect."""
    if not html:
        return True
    lower = html.lower()

    # Amazon: sign-in/login page (could be large, must check content)
    if platform == "amazon":
        if "<title>amazon sign-in</title>" in lower or "<title>sign-in</title>" in lower:
            return True
        if "enter the characters you see below" in lower:
            return True
        if "to discuss automated access to amazon" in lower:
            return True
        if "robot or not" in lower:
            return True
        if "ap_signin" in lower and "password" in lower and len(lower) < 500000:
            return True

    # Flipkart: homepage redirect or login prompt
    if platform == "flipkart":
        if "buy products online at best price" in lower and len(html) < 200000:
            return True
        if "login" in lower[:3000] and "flipkart" in lower[:3000]:
            return True

    # Suspiciously small pages are almost always bot-block pages
    if len(html) < 5000:
        return True

    if any(ind in lower[:5000] for ind in ["captcha", "robot check", "access denied", "security check"]):
        return True
    return False


class ScraperManager:
    """Fetches page HTML using multiple fallback strategies."""

    def __init__(self):
        from app.config import get_settings
        settings = get_settings()
        self._headless = settings.scraper_headless

    async def get_html(self, url: str, platform: str = "amazon") -> Optional[str]:
        """
        Try each strategy in order and return the first valid HTML.
        Returns None if all strategies fail.
        """
        strategies = [
            ("Persistent Profile", lambda: _try_persistent_profile(url, self._headless)),
            ("Playwright Stealth", lambda: _try_playwright_stealth(url, self._headless)),
            ("Playwright Fingerprint", lambda: _try_playwright_fingerprint(url, self._headless)),
            ("HTTPX", lambda: _try_httpx(url)),
        ]

        for name, strategy_fn in strategies:
            logger.info(f"[ScraperManager] Trying strategy: {name} for {url[:70]}")
            try:
                html = await strategy_fn()
                if html and not _is_blocked(html, platform):
                    logger.info(f"[ScraperManager] Strategy '{name}' succeeded ({len(html)} bytes)")
                    return html
                elif html:
                    logger.warning(f"[ScraperManager] Strategy '{name}' returned blocked content.")
            except Exception as e:
                logger.error(f"[ScraperManager] Strategy '{name}' raised: {e}")

        # Last resort: Selenium (sync, run in thread pool)
        logger.info(f"[ScraperManager] Trying strategy: Selenium Fallback for {url[:70]}")
        try:
            html = await asyncio.get_event_loop().run_in_executor(None, _try_selenium, url)
            if html and not _is_blocked(html, platform):
                logger.info(f"[ScraperManager] Selenium Fallback succeeded ({len(html)} bytes)")
                return html
            elif html:
                logger.warning("[ScraperManager] Selenium returned blocked content.")
        except Exception as e:
            logger.error(f"[ScraperManager] Selenium Fallback raised: {e}")

        logger.error(f"[ScraperManager] All strategies failed for {url}")
        return None
