"""
app/scraper/captcha_detector.py
───────────────────────────────
Detects anti-bot protections like captchas, Cloudflare, and login walls.
"""
import re
from playwright.async_api import Page
from bs4 import BeautifulSoup
from app.utils.logger import logger

class CaptchaDetector:
    """Detects various forms of bot protections on a page."""

    @staticmethod
    async def detect_from_page(page: Page) -> bool:
        """
        Returns True if bot protection is detected on the Playwright page.
        """
        try:
            title = await page.title()
            title_lower = title.lower()
            
            # 1. Login redirects or generic homepages (common Flipkart tactic)
            if "login" in title_lower or "sign in" in title_lower:
                logger.warning("[CaptchaDetector] Detected Login Wall.")
                return True
                
            # If Flipkart redirects to the exact homepage
            if "buy products online at best price" in title_lower:
                logger.warning("[CaptchaDetector] Detected Homepage Redirect (Bot Block).")
                return True

            # 2. Cloudflare / Captcha checks
            content = await page.content()
            return CaptchaDetector.detect_from_html(content)
            
        except Exception as e:
            logger.error(f"[CaptchaDetector] Error checking page: {e}")
            return False

    @staticmethod
    def detect_from_html(html: str) -> bool:
        """
        Returns True if bot protection is detected in raw HTML (for HTTPX/BS4).
        """
        html_lower = html.lower()
        
        # Look for common bot/captcha indicators
        indicators = [
            "captcha",
            "cloudflare",
            "robot verification",
            "access denied",
            "blocked page",
            "are you a human",
            "security check",
            "please verify you are a human"
        ]
        
        for ind in indicators:
            if ind in html_lower[:5000]: # Check first 5000 chars to save time
                logger.warning(f"[CaptchaDetector] Detected indicator: {ind}")
                return True
                
        return False
