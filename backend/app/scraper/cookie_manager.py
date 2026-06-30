"""
app/scraper/cookie_manager.py
─────────────────────────────
Handles saving, loading, and validating cookies.
Since we use launch_persistent_context, Playwright automatically manages cookies 
in the user_data_dir. This module provides extra utilities if needed.
"""
from playwright.async_api import BrowserContext
from app.utils.logger import logger

class CookieManager:
    """Manages manual cookie operations."""
    
    @staticmethod
    async def check_login_status(context: BrowserContext, url: str) -> bool:
        """
        Check if the current context has a valid login for a given URL by inspecting cookies.
        Note: The actual detection of login state is better done by looking for DOM elements.
        """
        cookies = await context.cookies([url])
        # A rudimentary check: if there are multiple cookies, there's some session state.
        return len(cookies) > 0

    @staticmethod
    async def clear_cookies(context: BrowserContext):
        """Clears all cookies from the context."""
        try:
            await context.clear_cookies()
            logger.info("[CookieManager] Cleared cookies.")
        except Exception as e:
            logger.error(f"[CookieManager] Error clearing cookies: {e}")

cookie_manager = CookieManager()
