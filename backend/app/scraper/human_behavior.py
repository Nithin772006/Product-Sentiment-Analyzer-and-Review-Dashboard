"""
app/scraper/human_behavior.py
─────────────────────────────
Simulates human interactions like random mouse movements, scrolling, pausing, and typing.
"""
import random
import asyncio
from playwright.async_api import Page
from app.utils.logger import logger

class HumanBehavior:
    """Provides methods to simulate human-like behavior on a Playwright page."""

    @staticmethod
    async def random_pause(min_sec: float = 0.5, max_sec: float = 2.0):
        """Pauses execution for a random duration."""
        await asyncio.sleep(random.uniform(min_sec, max_sec))

    @staticmethod
    async def scroll_randomly(page: Page, scrolls: int = 3):
        """Scrolls up and down randomly to simulate reading."""
        for _ in range(scrolls):
            direction = random.choice([1, -1])
            distance = random.randint(100, 600) * direction
            try:
                await page.mouse.wheel(0, distance)
            except Exception:
                pass
            await HumanBehavior.random_pause(0.5, 1.5)

    @staticmethod
    async def hover_and_click(page: Page, selector: str):
        """Moves the mouse to the element, hovers, then clicks."""
        try:
            element = await page.wait_for_selector(selector, state="visible", timeout=5000)
            if element:
                box = await element.bounding_box()
                if box:
                    # Move to center of element with some jitter
                    x = box["x"] + box["width"] / 2 + random.randint(-5, 5)
                    y = box["y"] + box["height"] / 2 + random.randint(-5, 5)
                    await page.mouse.move(x, y, steps=random.randint(5, 15))
                    await HumanBehavior.random_pause(0.2, 0.7)
                    await page.mouse.click(x, y)
        except Exception as e:
            logger.debug(f"[HumanBehavior] Could not hover/click {selector}: {e}")

    @staticmethod
    async def type_like_human(page: Page, selector: str, text: str):
        """Types text with random delays between keystrokes."""
        try:
            await page.click(selector)
            for char in text:
                await page.keyboard.press(char)
                await asyncio.sleep(random.uniform(0.05, 0.15))
        except Exception as e:
            logger.debug(f"[HumanBehavior] Could not type in {selector}: {e}")

    @staticmethod
    async def scroll_to_bottom(page: Page):
        """Scrolls progressively to the bottom of the page to trigger lazy loading."""
        last_height = 0
        attempts = 0
        while attempts < 5:
            # Scroll down by a large chunk
            await page.mouse.wheel(0, 800)
            await HumanBehavior.random_pause(0.5, 1.2)
            
            # Check if we've reached the bottom
            new_height = await page.evaluate("document.body.scrollHeight")
            current_scroll = await page.evaluate("window.scrollY + window.innerHeight")
            
            if current_scroll >= new_height - 100:
                attempts += 1
            else:
                attempts = 0
                
            last_height = new_height
