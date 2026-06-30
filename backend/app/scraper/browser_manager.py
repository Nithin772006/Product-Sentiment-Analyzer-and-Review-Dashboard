"""
app/scraper/browser_manager.py
──────────────────────────────
Manages the Playwright lifecycle, persistent context, and Chromium channel.
"""
import os
from pathlib import Path
from typing import Optional
from playwright.async_api import async_playwright, Playwright, BrowserContext

from app.utils.logger import logger
from app.config import get_settings

PROFILE_DIR = Path(__file__).resolve().parents[3] / "backend" / "browser_profile"

class BrowserManager:
    """Manages Playwright lifecycle and persistent browser contexts."""
    
    def __init__(self):
        self._settings = get_settings()
        self._playwright: Optional[Playwright] = None
        self._context: Optional[BrowserContext] = None
        self._headless = self._settings.scraper_headless

    async def __aenter__(self):
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.stop()

    async def start(self, fingerprint=None) -> BrowserContext:
        """Starts a persistent Chromium browser context."""
        if not self._playwright:
            self._playwright = await async_playwright().start()
        
        PROFILE_DIR.mkdir(parents=True, exist_ok=True)
        
        args = [
            "--disable-blink-features=AutomationControlled",
            "--disable-infobars",
            "--no-sandbox",
            "--disable-dev-shm-usage",
        ]
        
        # Merge fingerprint settings if provided
        kwargs = {
            "channel": "chrome",
            "headless": self._headless,
            "args": args,
            "user_data_dir": str(PROFILE_DIR),
            "viewport": {"width": 1920, "height": 1080},
        }

        if fingerprint:
            kwargs["user_agent"] = fingerprint.navigator.userAgent
            if fingerprint.screen:
                kwargs["viewport"] = {
                    "width": fingerprint.screen.width,
                    "height": fingerprint.screen.height
                }
            if fingerprint.navigator.language:
                kwargs["locale"] = fingerprint.navigator.language

        self._context = await self._playwright.chromium.launch_persistent_context(**kwargs)
        
        # Override navigator.webdriver
        await self._context.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

        return self._context

    async def get_context(self) -> BrowserContext:
        """Returns the active context, starts it if not running."""
        if not self._context:
            await self.start()
        return self._context

    async def stop(self):
        """Stops the context and playwright instance."""
        if self._context:
            try:
                await self._context.close()
            except Exception as e:
                logger.error(f"[BrowserManager] Error closing context: {e}")
            self._context = None
            
        if self._playwright:
            try:
                await self._playwright.stop()
            except Exception as e:
                logger.error(f"[BrowserManager] Error stopping playwright: {e}")
            self._playwright = None

