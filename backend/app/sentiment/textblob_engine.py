"""
app/sentiment/textblob_engine.py
─────────────────────────────────
TextBlob sentiment analysis engine. Extracts polarity and subjectivity.
"""

from __future__ import annotations

from typing import Dict
from textblob import TextBlob

from app.utils.logger import logger


class TextBlobEngine:
    """
    TextBlob Lexicon-Based Sentiment Analysis Engine.
    """

    # Polarity thresholds
    POSITIVE_THRESHOLD = 0.1
    NEGATIVE_THRESHOLD = -0.1

    def __init__(self) -> None:
        logger.debug("TextBlobEngine initialized successfully")

    def analyze(self, text: str) -> Dict:
        """
        Analyze text using TextBlob.
        """
        if not text.strip():
            return {
                "polarity": 0.0,
                "subjectivity": 0.0,
                "label": "neutral",
            }

        blob = TextBlob(text)
        sentiment = blob.sentiment
        polarity = sentiment.polarity
        subjectivity = sentiment.subjectivity

        # Determine label based on polarity
        if polarity > self.POSITIVE_THRESHOLD:
            label = "positive"
        elif polarity < self.NEGATIVE_THRESHOLD:
            label = "negative"
        else:
            label = "neutral"

        return {
            "polarity": round(polarity, 4),
            "subjectivity": round(subjectivity, 4),
            "label": label,
        }
