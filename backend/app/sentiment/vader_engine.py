"""
app/sentiment/vader_engine.py
──────────────────────────────
VADER sentiment analysis engine. Highly optimized for social media/short review text.
"""

from __future__ import annotations

from typing import Dict
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

from app.utils.logger import logger


class VaderEngine:
    """
    VADER Rule-Based Sentiment Analysis Engine.
    """

    # VADER Standard compound score thresholds
    POSITIVE_THRESHOLD = 0.05
    NEGATIVE_THRESHOLD = -0.05

    def __init__(self) -> None:
        self.analyzer = SentimentIntensityAnalyzer()
        logger.debug("VaderEngine initialized successfully")

    def analyze(self, text: str) -> Dict:
        """
        Analyze text using VADER and classify into positive, negative, or neutral.
        """
        if not text.strip():
            return {
                "compound": 0.0,
                "positive": 0.0,
                "negative": 0.0,
                "neutral": 1.0,
                "confidence": 1.0,
                "label": "neutral",
            }

        scores = self.analyzer.polarity_scores(text)
        compound = scores["compound"]
        
        # Determine label based on VADER standard rules
        if compound >= self.POSITIVE_THRESHOLD:
            label = "positive"
        elif compound <= self.NEGATIVE_THRESHOLD:
            label = "negative"
        else:
            label = "neutral"

        # Confidence is calculated as the absolute compound score (represents the strength of intensity)
        # For neutrals, confidence is 1.0 minus absolute compound score.
        confidence = abs(compound) if label != "neutral" else (1.0 - abs(compound))

        return {
            "compound": round(compound, 4),
            "positive": round(scores["pos"], 4),
            "negative": round(scores["neg"], 4),
            "neutral": round(scores["neu"], 4),
            "confidence": round(confidence, 4),
            "label": label,
        }
