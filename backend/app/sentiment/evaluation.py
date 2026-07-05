"""
app/sentiment/evaluation.py
────────────────────────────
Evaluates sentiment model predictions against true star ratings.
Uses scikit-learn to calculate classification metrics (Accuracy, Precision, Recall, F1).
"""

from __future__ import annotations

from typing import Dict, List

from app.utils.logger import logger


def _accuracy_score(y_true: List[str], y_pred: List[str]) -> float:
    if not y_true:
        return 0.0
    correct = sum(1 for target, predicted in zip(y_true, y_pred) if target == predicted)
    return correct / len(y_true)


def _confusion_matrix(y_true: List[str], y_pred: List[str], labels: List[str]) -> List[List[int]]:
    matrix = [[0 for _ in labels] for _ in labels]
    label_to_index = {label: index for index, label in enumerate(labels)}

    for target, predicted in zip(y_true, y_pred):
        if target in label_to_index and predicted in label_to_index:
            matrix[label_to_index[target]][label_to_index[predicted]] += 1

    return matrix


def _classification_report(
    y_true: List[str],
    y_pred: List[str],
    labels: List[str],
    output_dict: bool = True,
    zero_division: int = 0,
) -> Dict[str, Dict[str, float | int]]:
    if not output_dict:
        raise NotImplementedError("Only dictionary output is supported")

    support = {label: 0 for label in labels}
    for label in y_true:
        if label in support:
            support[label] += 1

    report: Dict[str, Dict[str, float | int]] = {}
    for label in labels:
        true_positives = sum(1 for target, predicted in zip(y_true, y_pred) if target == label and predicted == label)
        false_positives = sum(1 for target, predicted in zip(y_true, y_pred) if target != label and predicted == label)
        false_negatives = sum(1 for target, predicted in zip(y_true, y_pred) if target == label and predicted != label)

        precision = true_positives / (true_positives + false_positives) if (true_positives + false_positives) else zero_division
        recall = true_positives / (true_positives + false_negatives) if (true_positives + false_negatives) else zero_division
        f1_score = (2 * precision * recall / (precision + recall)) if (precision + recall) else zero_division

        report[label] = {
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "f1-score": round(f1_score, 4),
            "support": support[label],
        }

    report["accuracy"] = {"accuracy": round(_accuracy_score(y_true, y_pred), 4)}
    return report


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
        labels = ["positive", "neutral", "negative"]
        acc = _accuracy_score(y_true_labels, y_pred_labels)
        matrix = _confusion_matrix(y_true_labels, y_pred_labels, labels)

        # Classification report (dict format)
        report = _classification_report(
            y_true_labels,
            y_pred_labels,
            labels=labels,
            output_dict=True,
            zero_division=0,
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
