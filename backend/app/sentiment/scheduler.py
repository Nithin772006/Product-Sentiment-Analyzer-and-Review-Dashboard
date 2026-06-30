"""
app/sentiment/scheduler.py
──────────────────────────
Provides options for manual, background-interval, and failed-job sentiment processing.
"""

from __future__ import annotations

import asyncio
from typing import Optional

from app.sentiment.processor import SentimentBatchProcessor
from app.utils.logger import logger


class SentimentScheduler:
    """
    Handles background and scheduled sentiment analysis tasks.
    """

    def __init__(self) -> None:
        self.processor = SentimentBatchProcessor()
        self._bg_task: Optional[asyncio.Task] = None
        self._running = False

    async def trigger_manual_processing(self) -> dict:
        """
        Manually trigger a run to process all pending reviews.
        """
        logger.info("[Scheduler] Manual processing triggered.")
        try:
            stats = await self.processor.process_entire_collection()
            logger.info("[Scheduler] Manual processing completed: {stats}", stats=stats)
            return stats
        except Exception as exc:
            logger.error("[Scheduler] Error during manual processing run: {exc}", exc=exc)
            return {"error": str(exc), "total_processed": 0}

    async def _loop(self, interval_seconds: int) -> None:
        """
        Internal background interval loop.
        """
        logger.info("[Scheduler] Starting background loop with interval={sec}s", sec=interval_seconds)
        while self._running:
            try:
                # Process unprocessed reviews
                stats = await self.processor.process_entire_collection()
                if stats.get("total_processed", 0) > 0:
                    logger.info("[Scheduler] Background run processed: {stats}", stats=stats)
            except Exception as exc:
                logger.error("[Scheduler] Exception in background processing loop: {exc}", exc=exc)
                
            await asyncio.sleep(interval_seconds)

    def start_background_processing(self, interval_seconds: int = 60) -> None:
        """
        Start the background periodic task runner.
        """
        if self._running:
            logger.warning("[Scheduler] Background processing is already running.")
            return

        self._running = True
        self._bg_task = asyncio.create_task(self._loop(interval_seconds))
        logger.info("[Scheduler] Background sentiment analysis started.")

    async def stop_background_processing(self) -> None:
        """
        Gracefully stop the background processing runner.
        """
        if not self._running:
            return

        logger.info("[Scheduler] Stopping background processing...")
        self._running = False
        if self._bg_task:
            self._bg_task.cancel()
            try:
                await self._bg_task
            except asyncio.CancelledError:
                pass
            self._bg_task = None
        logger.info("[Scheduler] Background sentiment analysis stopped.")

    async def reprocess_failed_reviews(self) -> dict:
        """
        Reprocess reviews that may have failed (e.g. sentiment doc missing but flagged, 
        or flagged as unprocessed). In our structure, any review with 
        `sentiment_processed` != True is eligible for reprocessing.
        """
        logger.info("[Scheduler] Reprocessing failed/unprocessed reviews...")
        return await self.trigger_manual_processing()
