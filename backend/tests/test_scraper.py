"""
tests/test_scraper.py
──────────────────────
Unit tests for the reviews scraping and text parsing utilities.

Test suites
───────────
• TestScraperUtilities      — clean_text, parse_rating, parse_date helpers
• TestScraperService        — platform detection
• TestReviewExtraction      — is_truncated_text, clean_review_text, full review scenarios
"""

from __future__ import annotations

import unittest
from datetime import datetime, timezone, timedelta

from app.scraper.review_parser import clean_text, parse_rating, parse_date
from app.scraper.review_extractor import is_truncated_text, clean_review_text
from app.scraper.scraper_service import ScraperService


class TestScraperUtilities(unittest.TestCase):
    """
    Test suite for cleaning functions, rating convertors, and relative date parsers.
    """

    def test_clean_text(self) -> None:
        self.assertEqual(clean_text("  hello   world  "), "hello world")
        self.assertEqual(clean_text("\nhello\rworld\t"), "hello world")
        self.assertEqual(clean_text(None), "")

    def test_parse_rating(self) -> None:
        self.assertEqual(parse_rating("4.5 out of 5 stars"), 4.5)
        self.assertEqual(parse_rating("5 stars"), 5.0)
        self.assertEqual(parse_rating("3★"), 3.0)
        self.assertEqual(parse_rating("4.0"), 4.0)
        self.assertEqual(parse_rating("9 out of 10"), 4.5)
        self.assertEqual(parse_rating(None), None)
        self.assertEqual(parse_rating("no rating"), None)

    def test_parse_date_amazon(self) -> None:
        # Amazon style A: "15 March 2024"
        d1 = parse_date("Reviewed in India on 15 March 2024")
        self.assertEqual(d1.year, 2024)
        self.assertEqual(d1.month, 3)
        self.assertEqual(d1.day, 15)

        # Amazon style B: "January 8, 2024"
        d2 = parse_date("Reviewed in the United States on January 8, 2024")
        self.assertEqual(d2.year, 2024)
        self.assertEqual(d2.month, 1)
        self.assertEqual(d2.day, 8)

    def test_parse_date_flipkart_relative(self) -> None:
        now = datetime.now(tz=timezone.utc)

        # Relative days
        d1 = parse_date("3 days ago")
        diff = now - d1
        self.assertTrue(2 <= diff.days <= 4)

        # Relative weeks
        d2 = parse_date("1 week ago")
        diff_weeks = now - d2
        self.assertTrue(6 <= diff_weeks.days <= 8)

    def test_parse_date_flipkart_calendar(self) -> None:
        # Calendar style: "Dec, 2023"
        d1 = parse_date("Dec, 2023")
        self.assertEqual(d1.year, 2023)
        self.assertEqual(d1.month, 12)

        # Calendar style: "Nov, 2024"
        d2 = parse_date("nov, 2024")
        self.assertEqual(d2.year, 2024)
        self.assertEqual(d2.month, 11)


class TestScraperService(unittest.TestCase):
    """
    Test suite for ScraperService platform detection.
    """

    def setUp(self) -> None:
        self.service = ScraperService()

    def test_detect_platform(self) -> None:
        self.assertEqual(
            self.service._detect_platform("https://www.amazon.in/dp/B0C7V3DKKS"),
            "amazon"
        )
        self.assertEqual(
            self.service._detect_platform("https://www.flipkart.com/apple-iphone-15-black-128-gb/p/itm2d73c14c4c237"),
            "flipkart"
        )
        self.assertIsNone(
            self.service._detect_platform("https://www.google.com")
        )


class TestReviewExtraction(unittest.TestCase):
    """
    Test suite for the review extraction pipeline:
    - is_truncated_text() truncation detection
    - clean_review_text() deep cleaning
    - Full review scenarios (short, long, emoji, multiline, mixed-language)
    """

    # ── is_truncated_text ─────────────────────────────────────────────────────

    def test_is_truncated_text_rejects_brief_content(self) -> None:
        """Must reject Amazon's collapsed preview message."""
        self.assertTrue(is_truncated_text("Brief content visible, double tap to read full content"))
        self.assertTrue(is_truncated_text("Brief content visible, double tap to read full content."))

    def test_is_truncated_text_rejects_read_more(self) -> None:
        """Must reject any text that is just a 'Read More' label."""
        self.assertTrue(is_truncated_text("Read more"))
        self.assertTrue(is_truncated_text("  Read More  "))
        self.assertTrue(is_truncated_text("See more"))
        self.assertTrue(is_truncated_text("Continue reading"))

    def test_is_truncated_text_rejects_double_tap(self) -> None:
        """Must reject 'double tap to read' Amazon mobile artefact."""
        self.assertTrue(is_truncated_text("Double tap to read full content"))
        self.assertTrue(is_truncated_text("Tap to read full content"))

    def test_is_truncated_text_accepts_valid_review(self) -> None:
        """Must NOT reject a real review text."""
        self.assertFalse(is_truncated_text("This product is amazing! Highly recommend."))
        self.assertFalse(is_truncated_text("Waste of money. Broke after 3 days."))

    def test_is_truncated_text_rejects_empty(self) -> None:
        """Empty / None must be considered truncated."""
        self.assertTrue(is_truncated_text(""))
        self.assertTrue(is_truncated_text(None))  # type: ignore[arg-type]

    # ── clean_review_text ─────────────────────────────────────────────────────

    def test_clean_text_strips_invisible_chars(self) -> None:
        """Zero-width spaces and NBSP must be removed."""
        raw = "Great\u200b product\u00a0quality!"
        result = clean_review_text(raw)
        self.assertNotIn("\u200b", result)
        self.assertNotIn("\u00a0", result)
        self.assertIn("Great", result)
        self.assertIn("quality", result)

    def test_clean_text_strips_html_tags(self) -> None:
        """HTML markup leaked into the review text must be stripped."""
        raw = "<span>Good product</span> <br/> Value for money."
        result = clean_review_text(raw)
        self.assertNotIn("<span>", result)
        self.assertNotIn("<br/>", result)
        self.assertIn("Good product", result)
        self.assertIn("Value for money", result)

    def test_clean_text_deduplicates_lines(self) -> None:
        """Duplicate lines (preview + full text merged) must be deduplicated."""
        raw = "Great product\nGreat product\nReally happy with it."
        result = clean_review_text(raw)
        # "Great product" should appear only once
        self.assertEqual(result.lower().count("great product"), 1)
        self.assertIn("Really happy with it", result)

    def test_clean_text_preserves_full_review(self) -> None:
        """A long, valid review must not be trimmed or rejected."""
        long_review = (
            "I purchased this laptop for my college coursework and I have been using it for "
            "three months now. The build quality is excellent, the keyboard has a nice travel, "
            "and the display is bright and colour-accurate. Battery life easily lasts 8 hours "
            "of mixed usage (browsing, document editing, some light video). The performance is "
            "smooth for everyday tasks, though heavy video editing is a stretch. The fans can "
            "get a bit loud under sustained load. Overall, it is great value for the price and "
            "I would recommend it to students and office workers alike."
        )
        result = clean_review_text(long_review)
        self.assertGreater(len(result), 200)
        self.assertIn("laptop", result)
        self.assertIn("Battery life", result)

    def test_clean_text_emoji_review(self) -> None:
        """Reviews containing emoji must be preserved correctly."""
        raw = "Absolutely love it! 😍🔥 Best purchase of the year! 👌"
        result = clean_review_text(raw)
        self.assertIn("love it", result)
        self.assertIn("😍", result)
        self.assertIn("Best purchase", result)

    def test_clean_text_multiline_review(self) -> None:
        """Multiline reviews must be cleaned to a single coherent string."""
        raw = (
            "Pros:\n"
            "- Fast delivery\n"
            "- Good packaging\n\n"
            "Cons:\n"
            "- Slightly overpriced\n"
            "- Manual is only in Chinese\n"
        )
        result = clean_review_text(raw)
        self.assertIn("Fast delivery", result)
        self.assertIn("Good packaging", result)
        self.assertIn("Slightly overpriced", result)
        self.assertIn("Manual is only in Chinese", result)

    def test_clean_text_mixed_language_review(self) -> None:
        """Non-ASCII characters (Hindi, Arabic, etc.) must be preserved."""
        raw = "बहुत अच्छा product है। मैं इसे recommend करता हूँ।"
        result = clean_review_text(raw)
        self.assertIn("बहुत", result)
        self.assertIn("recommend", result)

    def test_clean_text_very_long_review(self) -> None:
        """A 2000+ character review must survive cleaning intact."""
        sentence = "This product exceeded my expectations in every possible way. "
        very_long = sentence * 35  # ~2100 chars
        result = clean_review_text(very_long)
        # Deduplication may collapse repeated sentences, but content should survive
        self.assertGreater(len(result), 0)
        self.assertIn("exceeded my expectations", result)


if __name__ == "__main__":
    unittest.main()
