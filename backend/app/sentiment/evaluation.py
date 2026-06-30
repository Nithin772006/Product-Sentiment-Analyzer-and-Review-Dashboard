"""
app/sentiment/evaluation.py
────────────────────────────
Evaluates sentiment model predictions against true star ratings.
Uses scikit-learn to calculate classification metrics (Accuracy, Precision, Recall, F1).
"""

from __future__ import annotations

from typing import Dict, List, Tuple
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix

from app.utils.logger import logger


class SentimentEvaluator:
    """
    Evaluates classifier predictions against mapped ground truth ratings.
    """

    def __init__(self) -> None:
        pass

    @staticmethod
    def rating_to_sentiment(rating: float) -> str:
        """
        Map numerical ratings to categorical sentiment labels:
          4.0 - 5.0 → "positive"
          3.0       → "neutral"
          1.0 - 2.0 → "negative"
        """
        if rating >= 4.0:
            return "positive"
        elif rating <= 2.0:
            return "negative"
        return "neutral"

    def evaluate(self, y_true_ratings: List[float], y_pred_labels: List[str]) -> Dict:
        """
        Evaluate predicted labels against true numerical ratings.

        Returns:
            dict containing metrics and confusion matrix.
        """
        if not y_true_ratings or not y_pred_labels:
            return {
                "accuracy": 0.0,
                "report": "No data available",
                "confusion_matrix": []
            }

        # Map ratings to true sentiment labels
        y_true_labels = [self.rating_to_sentiment(r) for r in y_true_ratings]

        # Calculate metrics
        acc = accuracy_score(y_true_labels, y_pred_labels)
        matrix = confusion_matrix(
            y_true_labels,
            y_pred_labels,
            labels=["positive", "neutral", "negative"]
        )

        # Classification report (dict format)
        report = classification_report(
            y_true_labels,
            y_pred_labels,
            labels=["positive", "neutral", "negative"],
            output_dict=True,
            zero_division=0
        )

        logger.info("[Evaluator] Sentiment evaluation run completed. Accuracy: {acc:.2%}", acc=acc)

        return {
            "accuracy": round(acc, 4),
            "report": report,
            "confusion_matrix": matrix.tolist(),
            "metrics": {
                "positive": report.get("positive", {}),
                "negative": report.get("negative", {}),
                "neutral": report.get("neutral", {}),
            }
        }
