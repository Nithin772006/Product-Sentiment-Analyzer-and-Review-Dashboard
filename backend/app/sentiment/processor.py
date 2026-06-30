"""
app/sentiment/processor.py
──────────────────────────
Async batch processor orchestrating the database retrieval, preprocessing,
sentiment analysis, and direct repository storage.
"""

from __future__ import annotations

import time
from typing import Dict, List, Optional
from datetime import datetime, timezone

from app.database.collections import (
    get_products_collection,
    get_reviews_collection,
    get_sentiments_collection,
)
from app.repositories.product_repository import ProductRepository
from app.repositories.review_repository import ReviewRepository
from app.repositories.sentiment_repository import SentimentRepository
from app.sentiment.analyzer import SentimentAnalyzer
from app.sentiment.preprocessor import TextPreprocessor
from app.sentiment.keywords import KeywordExtractor
from app.sentiment.wordcloud_generator import WordCloudGenerator
from app.utils.logger import logger
from app.utils.bson import utcnow


class SentimentBatchProcessor:
    """
    Orchestrates the sentiment analysis pipeline over database documents.
    """

    def __init__(self) -> None:
        self.preprocessor = TextPreprocessor()
        self.analyzer = SentimentAnalyzer()
        self.keywords_extractor = KeywordExtractor()
        self.wordcloud_gen = WordCloudGenerator()
        
        # Initialize repositories
        self.product_repo = ProductRepository()
        self.review_repo = ReviewRepository()
        self.sentiment_repo = SentimentRepository()

    async def process_single_review(self, review_id: str) -> Optional[Dict]:
        """
        Fetch, analyze, and save a single review's sentiment.
        """
        review = await self.review_repo.get_by_id(review_id)
        if not review:
            logger.warning("[Processor] Review not found for id={id}", id=review_id)
            return None

        # VADER works best with capitalization and punctuation, so we only remove HTML and URLs
        raw_text = review.get("review_text", "")
        partially_cleaned_text = self.preprocessor.remove_urls(
            self.preprocessor.remove_html(raw_text)
        ).strip()

        # Run analysis
        analysis_res = self.analyzer.analyse(partially_cleaned_text)

        # Preprocess for keyword tokens
        cleaned_for_tokens = self.preprocessor.preprocess(raw_text)
        tokens = self.preprocessor.tokenize_and_lemmatize(cleaned_for_tokens)

        # Build sentiment record
        sentiment_data = {
            "review_id": review_id,
            "product_id": review["product_id"],
            "sentiment": analysis_res["sentiment"],
            "confidence": analysis_res["confidence"],
            "polarity": analysis_res["polarity"],
            "subjectivity": analysis_res["subjectivity"],
            "vader_compound": analysis_res["vader_compound"],
            "keywords": tokens[:10],  # store top 10 keywords on the sentiment doc
            "processed_at": utcnow(),
        }

        # Save to sentiments collection (upsert safe)
        saved = await self.sentiment_repo.upsert_by_review_id(review_id, sentiment_data)

        # Update parent review status
        await self.review_repo.update(review_id, {
            "sentiment_processed": True,
            "processed_at": utcnow(),
        })

        logger.info(
            "[Processor] Processed review | id={rid} label={lbl} confidence={conf:.2f}",
            rid=review_id, lbl=analysis_res["sentiment"], conf=analysis_res["confidence"]
        )
        return saved

    async def process_batch_reviews(self, review_ids: List[str]) -> List[Dict]:
        """
        Process a specific list of review IDs in batch.
        """
        results = []
        for rid in review_ids:
            try:
                res = await self.process_single_review(rid)
                if res:
                    results.append(res)
            except Exception as exc:
                logger.error("[Processor] Error processing review id={id}: {exc}", id=rid, exc=exc)
        return results

    async def process_product_reviews(self, product_id: str) -> Dict:
        """
        Processes all unprocessed reviews for a specific product.
        Generates updated keywords and saves new Word Cloud images.
        """
        logger.info("[Processor] Starting batch processing for product_id={pid}", pid=product_id)
        start_time = time.time()

        # 1. Fetch unprocessed reviews for this product
        # Query reviews where product_id matches and sentiment_processed is not True
        unprocessed_filter = {"product_id": product_id, "sentiment_processed": {"$ne": True}}
        reviews_cursor = self.review_repo._col.find(unprocessed_filter)
        unprocessed_reviews = await reviews_cursor.to_list(length=5000)

        # 2. Process each unprocessed review
        processed_count = 0
        for r in unprocessed_reviews:
            try:
                review_id = str(r["_id"])
                await self.process_single_review(review_id)
                processed_count += 1
            except Exception as exc:
                logger.error("[Processor] Error processing review id={id}: {exc}", id=r.get("_id"), exc=exc)

        # 3. Fetch ALL reviews for this product to compile aggregate keywords and word clouds
        all_reviews_cursor = self.review_repo._col.find({"product_id": product_id})
        all_reviews = await all_reviews_cursor.to_list(length=5000)

        # Fetch corresponding sentiments
        all_sentiments_cursor = self.sentiment_repo._col.find({"product_id": product_id})
        sentiments_list = await all_sentiments_cursor.to_list(length=5000)
        sentiments_map = {str(s["review_id"]): s for s in sentiments_list}

        # Associate tokens with their sentiment labels
        reviews_data: List[tuple[List[str], str]] = []
        pos_words = {}
        neg_words = {}
        neu_words = {}

        for r in all_reviews:
            r_id_str = str(r["_id"])
            s_doc = sentiments_map.get(r_id_str)
            if not s_doc:
                continue

            # Re-generate tokens for word cloud
            cleaned = self.preprocessor.preprocess(r.get("review_text", ""))
            tokens = self.preprocessor.tokenize_and_lemmatize(cleaned)
            label = s_doc["sentiment"]
            reviews_data.append((tokens, label))

        # 4. Generate keywords & word clouds
        kw_stats = self.keywords_extractor.extract_keywords(reviews_data)
        
        # Convert Counter lists to dicts for word cloud generator
        pos_freqs = dict(kw_stats["positive_words"])
        neg_freqs = dict(kw_stats["negative_words"])
        neu_freqs = dict(kw_stats["neutral_words"])

        # Write Word Cloud images to static folder
        self.wordcloud_gen.generate_all_clouds(pos_freqs, neg_freqs, neu_freqs, product_id=product_id)

        # 5. Update parent product metadata (average rating, etc.)
        avg_rating = await self.review_repo.get_average_rating(product_id)
        if avg_rating is not None:
            await self.product_repo.update(product_id, {
                "average_rating": avg_rating,
                "last_scraped": utcnow(),
            })

        duration = time.time() - start_time
        logger.info(
            "[Processor] Batch completed for product={pid} | Processed: {p_count} | Duration: {dur:.2f}s",
            pid=product_id, p_count=processed_count, dur=duration
        )

        return {
            "product_id": product_id,
            "processed_count": processed_count,
            "duration_seconds": duration,
            "keywords": {
                "top_positive": [w for w, _ in kw_stats["positive_words"][:10]],
                "top_negative": [w for w, _ in kw_stats["negative_words"][:10]],
            }
        }

    async def process_entire_collection(self) -> Dict:
        """
        Find and process all unprocessed reviews inside the database.
        """
        unprocessed_filter = {"sentiment_processed": {"$ne": True}}
        cursor = self.review_repo._col.find(unprocessed_filter)
        unprocessed = await cursor.to_list(length=10000)

        logger.info("[Processor] Found {n} unprocessed reviews in the collection", n=len(unprocessed))

        processed_count = 0
        start_time = time.time()

        # Group by product to update keywords & wordclouds in single batches
        product_ids = set()
        for r in unprocessed:
            try:
                review_id = str(r["_id"])
                await self.process_single_review(review_id)
                product_ids.add(str(r["product_id"]))
                processed_count += 1
            except Exception as exc:
                logger.error("[Processor] Error processing review id={id}: {exc}", id=r.get("_id"), exc=exc)

        # Update word clouds and keywords for each affected product
        for pid in product_ids:
            try:
                await self.process_product_reviews(pid)
            except Exception as exc:
                logger.error("[Processor] Error updating stats for product id={pid}: {exc}", pid=pid, exc=exc)

        duration = time.time() - start_time
        return {
            "total_processed": processed_count,
            "duration_seconds": duration,
            "products_updated": len(product_ids),
        }
