"""
app/scraper/review_parser.py
─────────────────────────────
Helper functions for text cleaning, rating extraction, and platform-specific
date parsing (handling both Amazon's detailed date lines and Flipkart's relative dates).
"""

from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone
from typing import Optional

from app.utils.logger import logger

# Re-export for convenience — callers can import from either module
try:
    from app.scraper.review_extractor import is_truncated_text  # noqa: F401
except ImportError:
    # Fallback if review_extractor is not yet available (e.g., during tests)
    def is_truncated_text(text: str) -> bool:  # type: ignore[misc]
        """Fallback: always returns False (no truncation detection)."""
        return False

# ── Date parsing constants ────────────────────────────────────────────────────
MONTHS_MAP = {
    "january": 1, "jan": 1,
    "february": 2, "feb": 2,
    "march": 3, "mar": 3,
    "april": 4, "apr": 4,
    "may": 5,
    "june": 6, "jun": 6,
    "july": 7, "jul": 7,
    "august": 8, "aug": 8,
    "september": 9, "sep": 9, "sept": 9,
    "october": 10, "oct": 10,
    "november": 11, "nov": 11,
    "december": 12, "dec": 12
}


def clean_text(text: Optional[str]) -> str:
    """
    Remove extra whitespace, invisible Unicode characters, HTML tags,
    duplicate lines, and carriage returns.  Returns empty string if input
    is None or empty.
    """
    if not text:
        return ""

    # Remove invisible Unicode characters (zero-width space, NBSP, etc.)
    text = re.sub(r"[\u200b\u200c\u200d\u200e\u200f\u00a0\ufeff\u202f\u2060]", " ", text)

    # Strip HTML tags (safety net for any leaked markup)
    text = re.sub(r"<[^>]+>", " ", text)

    # Normalize line endings
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    # Collapse multiple blank lines
    text = re.sub(r"\n{3,}", "\n\n", text)

    # Deduplicate adjacent lines (handles preview + full text merge artefacts)
    seen_lines: set[str] = set()
    unique_lines: list[str] = []
    for line in text.split("\n"):
        normalized = re.sub(r"[ \t]+", " ", line).strip()
        key = normalized.lower()
        if key not in seen_lines:
            seen_lines.add(key)
            unique_lines.append(normalized)

    cleaned = " ".join(filter(None, unique_lines))
    # Final collapse of any remaining multi-space
    cleaned = re.sub(r"  +", " ", cleaned)
    return cleaned.strip()


def parse_rating(rating_str: Optional[str]) -> Optional[float]:
    """
    Extract rating numerical value from review rating string.
    Supports formats like: "4.5 out of 5 stars", "5 stars", "3★", "4.0".
    """
    if not rating_str:
        return None

    # Clean rating string
    s = rating_str.strip().lower()

    # Match numeric patterns
    match = re.search(r"(\d+(?:\.\d+)?)", s)
    if match:
        val = float(match.group(1))
        # Handle cases where rating is out of 10 or 100
        if "out of" in s and val > 5:
            # Scale down if it says e.g. "9 out of 10" -> 4.5
            second_match = re.search(r"out of\s+(\d+(?:\.\d+)?)", s)
            if second_match:
                scale = float(second_match.group(1))
                if scale > 0:
                    return round((val / scale) * 5.0, 1)
        return min(val, 5.0)

    return None


def parse_date(date_str: Optional[str]) -> datetime:
    """
    Parse a platform date string into a timezone-aware UTC datetime.
    Supports:
      - Amazon: "Reviewed in India on 15 March 2024" or "Reviewed in the United States on January 8, 2024"
      - Flipkart: "3 days ago", "2 months ago", "Dec, 2023", "Nov, 2024"
      - ISO string formats
    Defaults to current UTC datetime if parsing fails.
    """
    now = datetime.now(tz=timezone.utc)
    if not date_str:
        return now

    s = date_str.strip().lower()

    # 1. Check if it's already an ISO timestamp
    try:
        dt = datetime.fromisoformat(s.replace("z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except ValueError:
        pass

    # 2. Parse Amazon style: "Reviewed in <Country> on <Date>"
    # E.g. "on 15 march 2024" or "on january 8, 2024"
    if "on " in s:
        date_part = s.split("on ")[-1].strip()
        # Remove commas
        date_part = date_part.replace(",", "")
        
        # Try formats:
        # Format A: "15 march 2024" (Day Month Year)
        match_a = re.search(r"(\d{1,2})\s+([a-z]+)\s+(\d{4})", date_part)
        if match_a:
            day = int(match_a.group(1))
            month_name = match_a.group(2)
            year = int(match_a.group(3))
            month = MONTHS_MAP.get(month_name, 1)
            try:
                return datetime(year, month, day, tzinfo=timezone.utc)
            except ValueError:
                pass

        # Format B: "january 8 2024" (Month Day Year)
        match_b = re.search(r"([a-z]+)\s+(\d{1,2})\s+(\d{4})", date_part)
        if match_b:
            month_name = match_b.group(1)
            day = int(match_b.group(2))
            year = int(match_b.group(3))
            month = MONTHS_MAP.get(month_name, 1)
            try:
                return datetime(year, month, day, tzinfo=timezone.utc)
            except ValueError:
                pass

    # 3. Parse Flipkart relative style: "3 days ago", "1 month ago", "2 years ago"
    relative_match = re.search(r"(\d+)\s+(day|month|year|week)s?\s+ago", s)
    if relative_match:
        val = int(relative_match.group(1))
        unit = relative_match.group(2)
        if unit == "day":
            return now - timedelta(days=val)
        elif unit == "week":
            return now - timedelta(weeks=val)
        elif unit == "month":
            return now - timedelta(days=val * 30)
        elif unit == "year":
            return now - timedelta(days=val * 365)

    # 4. Parse Flipkart calendar style: "dec, 2023" or "nov, 2024"
    calendar_match = re.search(r"([a-z]+),\s*(\d{4})", s)
    if calendar_match:
        month_name = calendar_match.group(1)
        year = int(calendar_match.group(2))
        month = MONTHS_MAP.get(month_name, 1)
        try:
            return datetime(year, month, 1, tzinfo=timezone.utc)
        except ValueError:
            pass

    # 5. Last resort: match any day month year group
    fallback_match = re.search(r"([a-z]+)\s+(\d{4})", s)
    if fallback_match:
        month_name = fallback_match.group(1)
        year = int(fallback_match.group(2))
        month = MONTHS_MAP.get(month_name, 1)
        try:
            return datetime(year, month, 1, tzinfo=timezone.utc)
        except ValueError:
            pass

    logger.warning("Failed to parse date string '{date_str}'; defaulting to current UTC time", date_str=date_str)
    return now
