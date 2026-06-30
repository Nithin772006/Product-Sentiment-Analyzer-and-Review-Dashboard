"""
app/sentiment/statistics.py
────────────────────────────
Compiles aggregate sentiment statistics and processing timings for a review batch.
"""

from __future__ import annotations

from typing import Dict, List


class SentimentStatsCompiler:
    """
    Summarizes review sentiments and polarity/subjectivity scores.
    """

    def __init__(self) -> None:
        pass

    def compile_stats(
        self,
        sentiment_results: List[Dict],
        ratings: List[float],
        duration_seconds: float
    ) -> Dict:
        """
        Build aggregate statistics for a batch of analyzed reviews.

        Args:
            sentiment_results: List of dicts returned by SentimentAnalyzer.analyse()
            ratings: List of numerical star ratings associated with the reviews
            duration_seconds: Time taken to process the batch

        Returns:
            dict of statistics
        """
        total = len(sentiment_results)
        if total == 0:
            return {
                "total_processed": 0,
                "positive_count": 0,
                "negative_count": 0,
                "neutral_count": 0,
                "positive_pct": 0.0,
                "negative_pct": 0.0,
                "neutral_pct": 0.0,
                "average_rating": 0.0,
                "average_polarity": 0.0,
                "average_subjectivity": 0.0,
                "average_vader_compound": 0.0,
                "processing_time_seconds": round(duration_seconds, 4),
            }

        pos_count = 0
        neg_count = 0
        neu_count = 0
        total_polarity = 0.0
        total_subjectivity = 0.0
        total_compound = 0.0

        for r in sentiment_results:
            label = r["sentiment"]
            if label == "positive":
                pos_count += 1
            elif label == "negative":
                neg_count += 1
            else:
                neu_count += 1

            total_polarity += r.get("polarity", 0.0)
            total_subjectivity += r.get("subjectivity", 0.0)
            total_compound += r.get("vader_compound", 0.0)

        # Averages
        avg_rating = sum(ratings) / len(ratings) if ratings else 0.0
        avg_polarity = total_polarity / total
        avg_subjectivity = total_subjectivity / total
        avg_compound = total_compound / total

        # Percentages
        pos_pct = (pos_count / total) * 100.0
        neg_pct = (neg_count / total) * 100.0
        neu_pct = (neu_count / total) * 100.0

        return {
            "total_processed": total,
            "positive_count": pos_count,
            "negative_count": neg_count,
            "neutral_count": neu_count,
            "positive_pct": round(pos_pct, 2),
            "negative_pct": round(neg_pct, 2),
            "neutral_pct": round(neu_pct, 2),
            "average_rating": round(avg_rating, 2),
            "average_polarity": round(avg_polarity, 4),
            "average_subjectivity": round(avg_subjectivity, 4),
            "average_vader_compound": round(avg_compound, 4),
            "processing_time_seconds": round(duration_seconds, 4),
        }
