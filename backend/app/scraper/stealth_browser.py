"""
app/scraper/stealth_browser.py
──────────────────────────────
Integrates playwright-stealth to hide automation flags and configure stealth settings.
"""
from playwright.async_api import Page, BrowserContext
from playwright_stealth import Stealth
from app.scraper.fingerprint import fingerprint_manager

class StealthBrowser:
    """Configures pages with stealth capabilities to bypass basic bot detection."""

    @staticmethod
    async def configure_page(page: Page, use_fingerprint: bool = True) -> Page:
        """Applies stealth settings and optional fingerprinting to a page."""
        
        # Apply playwright-stealth v2 API
        stealth_obj = Stealth()
        await stealth_obj.apply_stealth_async(page)

        
        if use_fingerprint:
            fp = fingerprint_manager.get_fingerprint()
            
            # Set extra HTTP headers if applicable
            headers = {}
            if fp.navigator.language:
                headers["Accept-Language"] = fp.navigator.language
            
            headers["Accept"] = "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8"
            headers["Upgrade-Insecure-Requests"] = "1"
            
            await page.set_extra_http_headers(headers)
            
            # Hide webdriver and spoof properties via JS
            await page.add_init_script(f"""
                Object.defineProperty(navigator, 'webdriver', {{get: () => undefined}});
                Object.defineProperty(navigator, 'languages', {{get: () => ['{fp.navigator.language}', 'en-US', 'en']}});
                Object.defineProperty(navigator, 'platform', {{get: () => '{fp.navigator.platform}'}});
                Object.defineProperty(navigator, 'hardwareConcurrency', {{get: () => {fp.navigator.hardwareConcurrency}}});
                Object.defineProperty(navigator, 'deviceMemory', {{get: () => {fp.navigator.deviceMemory}}});
            """)
            
        return page

