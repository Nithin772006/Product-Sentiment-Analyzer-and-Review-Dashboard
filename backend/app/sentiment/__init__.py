"""
app/sentiment/__init__.py
─────────────────────────
Public re-exports for the sentiment analysis package.
"""
from app.sentiment.analyzer import SentimentAnalyzer
from app.sentiment.vader_engine import VaderEngine
from app.sentiment.textblob_engine import TextBlobEngine
from app.sentiment.preprocessor import TextPreprocessor
from app.sentiment.keywords import KeywordExtractor
from app.sentiment.wordcloud_generator import WordCloudGenerator
from app.sentiment.statistics import SentimentStatsCompiler
from app.sentiment.processor import SentimentBatchProcessor
from app.sentiment.scheduler import SentimentScheduler

__all__ = [
    "SentimentAnalyzer",
    "VaderEngine",
    "TextBlobEngine",
    "TextPreprocessor",
    "KeywordExtractor",
    "WordCloudGenerator",
    "SentimentStatsCompiler",
    "SentimentBatchProcessor",
    "SentimentScheduler",
    "SentimentEvaluator",
]


def __getattr__(name: str):
    if name == "SentimentEvaluator":
        from app.sentiment.evaluation import SentimentEvaluator

        return SentimentEvaluator
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
