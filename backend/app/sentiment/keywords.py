"""
app/sentiment/keywords.py
──────────────────────────
Keyword extraction and word frequency statistics for reviews.
Associates tokens with review sentiment labels to group positive, negative, and neutral keywords.
"""

from __future__ import annotations

from collections import Counter
from typing import Dict, List, Set, Tuple


class KeywordExtractor:
    """
    Extracts frequency counts and keyword breakdowns from cleaned review tokens.
    """

    def __init__(self) -> None:
        pass

    def extract_keywords(
        self,
        reviews_data: List[Tuple[List[str], str]]
    ) -> Dict:
        """
        Extract keyword statistics from preprocessed reviews.

        Args:
            reviews_data: List of tuples (token_list, sentiment_label)
                          E.g. [(['phone', 'great'], 'positive'), (['bad', 'camera'], 'negative')]

        Returns:
            dict containing:
                "frequent_words": list of (word, count) tuples for all reviews
                "positive_words": list of (word, count) tuples in positive reviews
                "negative_words": list of (word, count) tuples in negative reviews
                "neutral_words": list of (word, count) tuples in neutral reviews
                "unique_words_count": count of all unique words
                "word_frequencies": dict of all words and their frequencies
        """
        all_counter = Counter()
        pos_counter = Counter()
        neg_counter = Counter()
        neu_counter = Counter()
        unique_words: Set[str] = set()

        for tokens, label in reviews_data:
            if not tokens:
                continue
                
            all_counter.update(tokens)
            unique_words.update(tokens)

            if label == "positive":
                pos_counter.update(tokens)
            elif label == "negative":
                neg_counter.update(tokens)
            else:
                neu_counter.update(tokens)

        # Most frequent words overall (top 50)
        frequent_words = all_counter.most_common(50)
        positive_words = pos_counter.most_common(50)
        negative_words = neg_counter.most_common(50)
        neutral_words = neu_counter.most_common(50)

        return {
            "frequent_words": frequent_words,
            "positive_words": positive_words,
            "negative_words": negative_words,
            "neutral_words": neutral_words,
            "unique_words_count": len(unique_words),
            "word_frequencies": dict(all_counter),
        }
