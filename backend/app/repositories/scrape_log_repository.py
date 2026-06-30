"""
app/repositories/scrape_log_repository.py
───────────────────────────────────────────
Repository for the ``scrape_logs`` collection.

Extends ``BaseRepository`` with scrape-log-specific query methods:
  get_by_status     — filter by running / completed / failed / partial
  get_recent_logs   — latest N logs across all sources
  get_by_source     — logs from amazon or flipkart
  get_failed_logs   — convenience wrapper for status='failed'
  mark_completed    — update a log when a job finishes successfully
  mark_failed       — update a log when a job fails
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pymongo import DESCENDING

from app.database.collections import get_scrape_logs_collection
from app.repositories.base_repository import BaseRepository, _serialize, _utcnow
from app.utils.logger import logger


class ScrapeLogRepository(BaseRepository):
    """Async repository for ``scrape_logs`` collection operations."""

    def __init__(self) -> None:
        super().__init__(get_scrape_logs_collection())

    # ── Status-based queries ───────────────────────────────────────────────────

    async def get_by_status(
        self,
        status: str,
        skip: int = 0,
        limit: int = 20,
    ) -> tuple[list[dict], int]:
        """
        Return logs filtered by job status.

        Args:
            status: 'running' | 'completed' | 'failed' | 'partial'
            skip: Pagination offset.
            limit: Max results.

        Returns:
            ``(list_of_logs, total_count)``
        """
        return await self.find(
            filter_query={"status": status},
            skip=skip,
            limit=limit,
            sort_field="scrape_start",
            sort_order=DESCENDING,
        )

    async def get_failed_logs(
        self,
        skip: int = 0,
        limit: int = 20,
    ) -> tuple[list[dict], int]:
        """Convenience — return all failed scrape jobs (paginated)."""
        return await self.get_by_status("failed", skip=skip, limit=limit)

    async def get_running_jobs(self) -> list[dict]:
        """Return all currently-running scrape jobs (no pagination — should be small)."""
        cursor = self._col.find({"status": "running"}).sort("scrape_start", DESCENDING)
        docs = await cursor.to_list(length=100)
        return [_serialize(d) for d in docs]

    # ── Recency ────────────────────────────────────────────────────────────────

    async def get_recent_logs(self, limit: int = 20) -> list[dict]:
        """
        Return the most recent scrape logs across all sources and statuses.

        Args:
            limit: Max results (capped at 100).

        Returns:
            List of log dicts sorted by ``scrape_start`` DESC.
        """
        limit = min(limit, 100)
        cursor = (
            self._col.find()
            .sort("scrape_start", DESCENDING)
            .limit(limit)
        )
        docs = await cursor.to_list(length=limit)
        return [_serialize(d) for d in docs]

    # ── Source filter ──────────────────────────────────────────────────────────

    async def get_by_source(
        self,
        source: str,
        skip: int = 0,
        limit: int = 20,
    ) -> tuple[list[dict], int]:
        """
        Return logs from a specific platform.

        Args:
            source: 'amazon' | 'flipkart'
        """
        return await self.find(
            filter_query={"source": source},
            skip=skip,
            limit=limit,
            sort_field="scrape_start",
            sort_order=DESCENDING,
        )

    # ── Status transition helpers ──────────────────────────────────────────────

    async def mark_completed(
        self,
        log_id: str,
        total_reviews_found: int,
        scrape_end: Optional[datetime] = None,
    ) -> Optional[dict]:
        """
        Mark a scrape job as completed.

        Args:
            log_id: ObjectId string of the log document.
            total_reviews_found: Final review count.
            scrape_end: Job end timestamp (defaults to utcnow).

        Returns:
            The updated document, or None if not found.
        """
        update_data = {
            "status": "completed",
            "total_reviews_found": total_reviews_found,
            "scrape_end": scrape_end or _utcnow(),
            "error_message": None,
        }
        doc = await self.update(log_id, update_data)
        if doc:
            logger.info(
                "[scrape_logs] Marked completed | id={id} reviews={n}",
                id=log_id,
                n=total_reviews_found,
            )
        return doc

    async def mark_failed(
        self,
        log_id: str,
        error_message: str,
        total_reviews_found: int = 0,
        scrape_end: Optional[datetime] = None,
    ) -> Optional[dict]:
        """
        Mark a scrape job as failed with an error message.

        Args:
            log_id: ObjectId string of the log document.
            error_message: Description of the failure.
            total_reviews_found: Any reviews collected before failure.
            scrape_end: Job end timestamp (defaults to utcnow).

        Returns:
            The updated document, or None if not found.
        """
        update_data = {
            "status": "failed",
            "total_reviews_found": total_reviews_found,
            "scrape_end": scrape_end or _utcnow(),
            "error_message": error_message[:2000],  # truncate to field limit
        }
        doc = await self.update(log_id, update_data)
        if doc:
            logger.warning(
                "[scrape_logs] Marked failed | id={id} error={err}",
                id=log_id,
                err=error_message[:100],
            )
        return doc

    # ── Aggregation ────────────────────────────────────────────────────────────

    async def get_job_summary(self) -> dict:
        """
        Return a count summary grouped by status.

        Returns::

            {
                "total": int,
                "completed": int,
                "failed": int,
                "running": int,
                "partial": int,
            }
        """
        pipeline = [
            {"$group": {"_id": "$status", "count": {"$sum": 1}}},
        ]
        summary: dict = {
            "total": 0,
            "completed": 0,
            "failed": 0,
            "running": 0,
            "partial": 0,
        }
        async for doc in self._col.aggregate(pipeline):
            label = doc["_id"] or "unknown"
            count = doc["count"]
            summary["total"] += count
            if label in summary:
                summary[label] = count

        return summary
