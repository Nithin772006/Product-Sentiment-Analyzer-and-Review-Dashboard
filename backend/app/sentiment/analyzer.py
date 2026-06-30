"""
app/sentiment/analyzer.py
──────────────────────────
Combined dual-engine sentiment analyzer merging VaderEngine and TextBlobEngine.
Uses confidence-score threshold comparison to resolve engine label disagreements.
"""

from __future__ import annotations

from typing import Dict, List
from app.sentiment.vader_engine import VaderEngine
from app.sentiment.textblob_engine import TextBlobEngine
from app.utils.logger import logger


class SentimentAnalyzer:
    """
    Combined dual-engine sentiment analyzer.
    """

    def __init__(self) -> None:
        self.vader = VaderEngine()
        self.textblob = TextBlobEngine()
        logger.debug("SentimentAnalyzer initialized (VADER + TextBlob engines)")

    def _resolve_disagreement(self, v_res: Dict, t_res: Dict) -> str:
        """
        Resolve disagreements between VADER and TextBlob.
        Compares VADER confidence score and TextBlob polarity strength.
        """
        v_label = v_res["label"]
        t_label = t_res["label"]
        
        # If they agree, return it immediately
        if v_label == t_label:
            return v_label

        v_conf = v_res["confidence"]
        
        # Compute TextBlob confidence as absolute polarity (strength of sentiment)
        # For neutral TextBlob reviews, confidence is 1.0 - abs(polarity)
        t_conf = abs(t_res["polarity"]) if t_label != "neutral" else (1.0 - abs(t_res["polarity"]))

        # Select label with highest confidence
        if v_conf >= t_conf:
            logger.debug(
                "Disagreement resolved: choosing VADER '{v}' (conf={vc:.2f}) over TextBlob '{t}' (conf={tc:.2f})",
                v=v_label, vc=v_conf, t=t_label, tc=t_conf
            )
            return v_label
        else:
            logger.debug(
                "Disagreement resolved: choosing TextBlob '{t}' (conf={tc:.2f}) over VADER '{v}' (conf={vc:.2f})",
                t=t_label, tc=t_conf, v=v_label, vc=v_conf
            )
            return t_label

    def analyse(self, text: str) -> Dict:
        """
        Analyse a single review text string.

        Returns:
            dict containing:
                sentiment: "positive" | "negative" | "neutral" (resolved label)
                confidence: resolved confidence score [0, 1]
                polarity: TextBlob polarity [-1, 1]
                subjectivity: TextBlob subjectivity [0, 1]
                vader_compound: VADER compound score [-1, 1]
        """
        if not text or not text.strip():
            return {
                "sentiment": "neutral",
                "confidence": 1.0,
                "polarity": 0.0,
                "subjectivity": 0.0,
                "vader_compound": 0.0,
            }

        # Run both engines
        v_res = self.vader.analyze(text)
        t_res = self.textblob.analyze(text)

        # Resolve labels
        resolved_label = self._resolve_disagreement(v_res, t_res)
        
        # Resolved confidence is VADER's if we picked VADER, otherwise TextBlob's absolute polarity
        if resolved_label == v_res["label"]:
            confidence = v_res["confidence"]
        else:
            confidence = abs(t_res["polarity"]) if t_res["label"] != "neutral" else (1.0 - abs(t_res["polarity"]))

        return {
            "sentiment": resolved_label,
            "confidence": round(confidence, 4),
            "polarity": t_res["polarity"],
            "subjectivity": t_res["subjectivity"],
            "vader_compound": v_res["compound"],
        }

    def analyse_batch(self, texts: List[str]) -> List[Dict]:
        """
        Analyse a batch of review texts.
        """
        results: List[Dict] = []
        for text in texts:
            results.append(self.analyse(text))
        return results
