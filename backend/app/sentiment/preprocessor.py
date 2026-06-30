"""
app/sentiment/preprocessor.py
──────────────────────────────
Text preprocessing module for review cleaning, tokenization, stopword removal,
and lemmatization using NLTK.
"""

from __future__ import annotations

import re
from typing import List, Optional
import nltk
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from nltk.tokenize import word_tokenize

from app.utils.logger import logger

# ── Ensure NLTK resources are downloaded ─────────────────────────────────────
# Using quiet mode to prevent console clutter on startup
try:
    logger.debug("Downloading NLTK resources...")
    nltk.download("punkt", quiet=True)
    nltk.download("stopwords", quiet=True)
    nltk.download("wordnet", quiet=True)
    nltk.download("omw-1.4", quiet=True)
    nltk.download("averaged_perceptron_tagger", quiet=True)
except Exception as e:
    logger.warning("Failed to download some NLTK resources, using defaults: {exc}", exc=e)


class TextPreprocessor:
    """
    Cleans and preprocesses text reviews for sentiment extraction.
    """

    def __init__(self) -> None:
        self.lemmatizer = WordNetLemmatizer()
        try:
            self.stop_words = set(stopwords.words("english"))
        except Exception:
            logger.warning("Stopwords not loaded; using default empty stopword set")
            self.stop_words = set()

    def remove_html(self, text: str) -> str:
        """Strip HTML tags using regex."""
        return re.sub(r"<[^>]*>", "", text)

    def remove_urls(self, text: str) -> str:
        """Strip http/https URLs."""
        return re.sub(r"https?://\S+|www\.\S+", "", text)

    def remove_emojis(self, text: str) -> str:
        """Strip emojis and non-BMP characters."""
        # Replace non-ascii or emoji characters matching standard unicode blocks
        return text.encode("ascii", "ignore").decode("ascii")

    def clean_special_characters(self, text: str) -> str:
        """Remove punctuation and numbers, keeping only letters and spaces."""
        # Remove numbers and punctuation
        cleaned = re.sub(r"[^a-zA-Z\s]", "", text)
        # Normalize extra spaces
        return re.sub(r"\s+", " ", cleaned).strip()

    def preprocess(self, text: Optional[str]) -> str:
        """
        Full preprocessing chain:
          1. Lowercasing
          2. HTML tag removal
          3. URL removal
          4. Emoji and non-ASCII character removal
          5. Punctuation and digits removal
          6. Extra whitespaces compression
        """
        if not text:
            return ""

        # Lowercase
        s = text.lower()

        # Chain cleaners
        s = self.remove_html(s)
        s = self.remove_urls(s)
        s = self.remove_emojis(s)
        s = self.clean_special_characters(s)

        return s

    def tokenize_and_lemmatize(self, cleaned_text: str) -> List[str]:
        """
        Tokenizes the clean text, filters out English stopwords,
        and lemmatizes remaining words to their dictionary form.
        """
        if not cleaned_text:
            return []

        try:
            tokens = word_tokenize(cleaned_text)
        except Exception:
            # Fallback split-based tokenization if nltk tokenizer fails
            tokens = cleaned_text.split()

        processed_tokens: List[str] = []
        for word in tokens:
            if word not in self.stop_words and len(word) > 2:
                # Lemmatize nouns (default) and verbs
                lemma = self.lemmatizer.lemmatize(word, pos="v")
                lemma = self.lemmatizer.lemmatize(lemma, pos="n")
                processed_tokens.append(lemma)

        return processed_tokens

    def get_processed_string(self, text: Optional[str]) -> str:
        """
        Preprocesses a review and returns the tokens joined back as a clean string.
        Useful for TF-IDF, Word Clouds, or word counts.
        """
        cleaned = self.preprocess(text)
        tokens = self.tokenize_and_lemmatize(cleaned)
        return " ".join(tokens)
