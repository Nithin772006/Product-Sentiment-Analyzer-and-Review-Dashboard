"""
tests/test_sentiment.py
─────────────────────────
Unit and integration tests for the Sentiment Analysis module.
"""

from __future__ import annotations

import unittest
from app.sentiment.preprocessor import TextPreprocessor
from app.sentiment.vader_engine import VaderEngine
from app.sentiment.textblob_engine import TextBlobEngine
from app.sentiment.analyzer import SentimentAnalyzer
from app.sentiment.keywords import KeywordExtractor
from app.sentiment.statistics import SentimentStatsCompiler
from app.sentiment.evaluation import SentimentEvaluator


class TestSentimentPreprocessor(unittest.TestCase):
    """
    Test suite for the TextPreprocessor logic.
    """

    def setUp(self) -> None:
        self.preprocessor = TextPreprocessor()

    def test_basic_cleaning(self) -> None:
        raw = "This is a <p>great</p> phone! Check it out: https://example.com 😊"
        cleaned = self.preprocessor.preprocess(raw)
        # Expected: lowercase, no HTML tags, no URLs, no emojis, no punctuation
        self.assertEqual(cleaned, "this is a great phone check it out")

    def test_tokenization_and_lemmatization(self) -> None:
        cleaned = "this is a great phone check it out"
        tokens = self.preprocessor.tokenize_and_lemmatize(cleaned)
        # Stopwords like "this", "is", "a", "it", "out" should be removed.
        # "phone", "great", "check" should be present.
        self.assertIn("great", tokens)
        self.assertIn("phone", tokens)
        self.assertIn("check", tokens)
        self.assertNotIn("this", tokens)


class TestSentimentEngines(unittest.TestCase):
    """
    Test suite for VADER, TextBlob, and Combined Analyzer consensus logic.
    """

    def setUp(self) -> None:
        self.analyzer = SentimentAnalyzer()

    def test_positive_review(self) -> None:
        text = "The product is absolutely amazing! I love the battery life."
        res = self.analyzer.analyse(text)
        self.assertEqual(res["sentiment"], "positive")
        self.assertGreater(res["confidence"], 0.5)
        self.assertGreater(res["vader_compound"], 0.1)

    def test_negative_review(self) -> None:
        text = "The quality is terrible and horrible. Waste of money."
        res = self.analyzer.analyse(text)
        self.assertEqual(res["sentiment"], "negative")
        self.assertGreater(res["confidence"], 0.5)
        self.assertLess(res["vader_compound"], -0.1)

    def test_neutral_review(self) -> None:
        text = "The package arrived yesterday. It is a cardboard box."
        res = self.analyzer.analyse(text)
        self.assertEqual(res["sentiment"], "neutral")

    def test_empty_review(self) -> None:
        res = self.analyzer.analyse("")
        self.assertEqual(res["sentiment"], "neutral")
        self.assertEqual(res["confidence"], 1.0)

    def test_emoji_review(self) -> None:
        # VADER handles emojis like :) or ❤️
        res_smiley = self.analyzer.analyse("The camera quality is :)")
        self.assertEqual(res_smiley["sentiment"], "positive")

    def test_disagreement_resolution(self) -> None:
        # A mixed review where engines might differ but resolve using confidence
        text = "Not bad, but not particularly great either."
        res = self.analyzer.analyse(text)
        # Should resolve to a valid label without crashing
        self.assertIn(res["sentiment"], ["positive", "negative", "neutral"])


class TestKeywordExtraction(unittest.TestCase):
    """
    Test suite for keyword counts and distributions.
    """

    def test_extract_keywords(self) -> None:
        extractor = KeywordExtractor()
        reviews = [
            (["phone", "amazing", "camera"], "positive"),
            (["phone", "terrible", "battery"], "negative"),
            (["screen", "phone", "ok"], "neutral")
        ]
        stats = extractor.extract_keywords(reviews)
        
        # 'phone' appears in all reviews (frequency = 3)
        self.assertEqual(stats["word_frequencies"]["phone"], 3)
        self.assertEqual(stats["unique_words_count"], 7)

        # positive words should contain 'amazing'
        pos_words = [w for w, _ in stats["positive_words"]]
        self.assertIn("amazing", pos_words)

        # negative words should contain 'terrible'
        neg_words = [w for w, _ in stats["negative_words"]]
        self.assertIn("terrible", neg_words)


class TestStatsCompiler(unittest.TestCase):
    """
    Test suite for stats aggregation.
    """

    def test_compile_stats(self) -> None:
        compiler = SentimentStatsCompiler()
        results = [
            {"sentiment": "positive", "polarity": 0.8, "subjectivity": 0.6, "vader_compound": 0.85},
            {"sentiment": "negative", "polarity": -0.6, "subjectivity": 0.7, "vader_compound": -0.75},
            {"sentiment": "neutral", "polarity": 0.0, "subjectivity": 0.1, "vader_compound": 0.0}
        ]
        ratings = [5.0, 1.0, 3.0]
        stats = compiler.compile_stats(results, ratings, duration_seconds=1.25)

        self.assertEqual(stats["total_processed"], 3)
        self.assertEqual(stats["positive_count"], 1)
        self.assertEqual(stats["negative_count"], 1)
        self.assertEqual(stats["neutral_count"], 1)
        self.assertEqual(stats["average_rating"], 3.0)
        self.assertEqual(stats["processing_time_seconds"], 1.25)


class TestSentimentEvaluator(unittest.TestCase):
    """
    Test suite for classifier evaluation reports.
    """

    def test_evaluator(self) -> None:
        evaluator = SentimentEvaluator()
        ratings = [5.0, 1.0, 3.0, 4.0, 2.0]
        predictions = ["positive", "negative", "neutral", "positive", "negative"]

        res = evaluator.evaluate(ratings, predictions)
        self.assertEqual(res["accuracy"], 1.0)  # perfect agreement
        self.assertEqual(res["confusion_matrix"], [
            [2, 0, 0], # positive
            [0, 1, 0], # neutral
            [0, 0, 2]  # negative
        ])


if __name__ == "__main__":
    unittest.main()
