"""
app/repositories/base_repository.py
────────────────────────────────────
Generic async repository providing the standard CRUD surface area.

All domain-specific repositories inherit from ``BaseRepository`` and receive
a Motor collection injected at construction time.  This keeps the repositories
completely independent of FastAPI routes and business logic.

Provided operations:
  create        — Insert one document, return the full inserted doc
  insert_many   — Bulk insert, return list of inserted ID strings
  get_by_id     — Fetch by _id ObjectId
  get_all       — Paginated, sorted listing with optional filter
  update        — Partial update via $set (PATCH semantics)
  delete        — Remove by _id
  count         — Count matching documents
  exists        — Check document existence
  find          — Flexible query: filter + sort + pagination → (docs, total)
  search        — Regex full-text search across specified fields

Custom exceptions defined here:
  RepositoryError        — base
  DuplicateDocumentError — unique index violation
  DocumentNotFoundError  — document not found
  InvalidObjectIdError   — bad ObjectId string
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorCollection
from pymongo import DESCENDING, ReturnDocument
from pymongo.errors import DuplicateKeyError

from app.utils.logger import logger


# ── Custom exceptions ──────────────────────────────────────────────────────────

class RepositoryError(Exception):
    """Base class for all repository-level exceptions."""


class DuplicateDocumentError(RepositoryError):
    """Raised when a unique index constraint is violated."""


class DocumentNotFoundError(RepositoryError):
    """Raised when a requested document does not exist."""


class InvalidObjectIdError(RepositoryError):
    """Raised when an invalid ObjectId string is supplied."""


# ── Internal helpers ───────────────────────────────────────────────────────────

def _to_oid(oid: str) -> ObjectId:
    """Convert a hex string to ObjectId. Raises ``InvalidObjectIdError`` on failure."""
    try:
        return ObjectId(oid)
    except Exception as exc:
        raise InvalidObjectIdError(f"'{oid}' is not a valid ObjectId") from exc


def _serialize(doc: dict | None) -> dict:
    """
    Convert a raw MongoDB document dict to a JSON-safe dict.
    Recursively handles:
      ``_id``  → ``"id"`` (string)
      ObjectId → string
      nested dict / list items → recursively processed
    """
    if doc is None:
        return {}
    result: dict = {}
    for key, value in doc.items():
        if key == "_id":
            result["id"] = str(value)
        elif isinstance(value, ObjectId):
            result[key] = str(value)
        elif isinstance(value, dict):
            result[key] = _serialize(value)
        elif isinstance(value, list):
            result[key] = [
                _serialize(item) if isinstance(item, dict) else item
                for item in value
            ]
        else:
            result[key] = value
    return result


def _utcnow() -> datetime:
    return datetime.now(tz=timezone.utc)


# ── Base repository ────────────────────────────────────────────────────────────

class BaseRepository:
    """
    Generic async repository.  Inject a Motor collection at init.

    Usage::

        class ProductRepository(BaseRepository):
            def __init__(self):
                super().__init__(get_products_collection())
    """

    def __init__(self, collection: AsyncIOMotorCollection) -> None:
        self._col = collection
        self._name = collection.name

    # ── Create ─────────────────────────────────────────────────────────────────

    async def create(self, data: dict) -> dict:
        """
        Insert a single document and return the complete inserted document.

        Automatically injects ``created_at`` and ``updated_at`` if missing.

        Args:
            data: Document dict (without _id — let MongoDB generate it).

        Returns:
            The inserted document dict with ``"id"`` string field.

        Raises:
            DuplicateDocumentError: On unique index violation.
        """
        now = _utcnow()
        data.setdefault("created_at", now)
        data.setdefault("updated_at", now)

        try:
            result = await self._col.insert_one(data)
            logger.info(
                "[{col}] Inserted document | id={id}",
                col=self._name,
                id=str(result.inserted_id),
            )
            inserted = await self._col.find_one({"_id": result.inserted_id})
            return _serialize(inserted)
        except DuplicateKeyError as exc:
            logger.warning(
                "[{col}] Duplicate key violation: {exc}", col=self._name, exc=exc
            )
            raise DuplicateDocumentError(str(exc)) from exc

    async def insert_many(self, data: list[dict]) -> list[str]:
        """
        Bulk-insert multiple documents.

        Args:
            data: List of document dicts.

        Returns:
            List of inserted ID strings (same order as input).

        Raises:
            DuplicateDocumentError: On unique index violation.
        """
        if not data:
            return []

        now = _utcnow()
        for doc in data:
            doc.setdefault("created_at", now)
            doc.setdefault("updated_at", now)

        try:
            result = await self._col.insert_many(data, ordered=False)
            ids = [str(i) for i in result.inserted_ids]
            logger.info(
                "[{col}] Bulk inserted {n} documents", col=self._name, n=len(ids)
            )
            return ids
        except DuplicateKeyError as exc:
            logger.warning(
                "[{col}] Bulk insert duplicate key: {exc}", col=self._name, exc=exc
            )
            raise DuplicateDocumentError(str(exc)) from exc

    # ── Read ───────────────────────────────────────────────────────────────────

    async def get_by_id(self, doc_id: str) -> Optional[dict]:
        """
        Fetch a single document by its ``_id``.

        Returns:
            Serialized document dict, or ``None`` if not found.

        Raises:
            InvalidObjectIdError: If ``doc_id`` is not a valid ObjectId.
        """
        oid = _to_oid(doc_id)
        doc = await self._col.find_one({"_id": oid})
        if doc is None:
            logger.debug(
                "[{col}] get_by_id — not found: {id}", col=self._name, id=doc_id
            )
            return None
        return _serialize(doc)

    async def get_all(
        self,
        skip: int = 0,
        limit: int = 20,
        sort_field: str = "created_at",
        sort_order: int = DESCENDING,
        filter_query: Optional[dict] = None,
    ) -> list[dict]:
        """
        Return a paginated, sorted listing of documents.

        Args:
            skip: Pagination offset.
            limit: Max results (capped at 200).
            sort_field: Field to sort by.
            sort_order: ``ASCENDING`` (1) or ``DESCENDING`` (-1).
            filter_query: Optional MongoDB filter dict.

        Returns:
            List of serialized document dicts.
        """
        limit = min(limit, 200)
        query = filter_query or {}
        cursor = (
            self._col.find(query)
            .sort(sort_field, sort_order)
            .skip(skip)
            .limit(limit)
        )
        docs = await cursor.to_list(length=limit)
        return [_serialize(d) for d in docs]

    # ── Update ─────────────────────────────────────────────────────────────────

    async def update(self, doc_id: str, data: dict) -> Optional[dict]:
        """
        Partially update a document via ``$set`` (PATCH semantics).

        Only the supplied fields are written; other fields remain untouched.
        ``updated_at`` is automatically refreshed.

        Args:
            doc_id: Hex string ObjectId.
            data: Fields to update.

        Returns:
            The post-update document dict, or ``None`` if not found.

        Raises:
            InvalidObjectIdError: If ``doc_id`` is invalid.
        """
        oid = _to_oid(doc_id)
        data["updated_at"] = _utcnow()

        result = await self._col.find_one_and_update(
            {"_id": oid},
            {"$set": data},
            return_document=ReturnDocument.AFTER,
        )
        if result is None:
            logger.debug(
                "[{col}] update — not found: {id}", col=self._name, id=doc_id
            )
            return None

        logger.info("[{col}] Updated document | id={id}", col=self._name, id=doc_id)
        return _serialize(result)

    # ── Delete ─────────────────────────────────────────────────────────────────

    async def delete(self, doc_id: str) -> bool:
        """
        Delete a document by ``_id``.

        Returns:
            ``True`` if deleted, ``False`` if not found.

        Raises:
            InvalidObjectIdError: If ``doc_id`` is invalid.
        """
        oid = _to_oid(doc_id)
        result = await self._col.delete_one({"_id": oid})
        deleted = result.deleted_count > 0

        if deleted:
            logger.info(
                "[{col}] Deleted document | id={id}", col=self._name, id=doc_id
            )
        else:
            logger.debug(
                "[{col}] delete — not found: {id}", col=self._name, id=doc_id
            )
        return deleted

    # ── Aggregation ────────────────────────────────────────────────────────────

    async def count(self, filter_query: Optional[dict] = None) -> int:
        """Return the count of documents matching the filter."""
        return await self._col.count_documents(filter_query or {})

    async def exists(self, filter_query: dict) -> bool:
        """Return ``True`` if at least one document matches the filter."""
        doc = await self._col.find_one(filter_query, {"_id": 1})
        return doc is not None

    # ── Advanced queries ───────────────────────────────────────────────────────

    async def find(
        self,
        filter_query: Optional[dict] = None,
        skip: int = 0,
        limit: int = 20,
        sort_field: str = "created_at",
        sort_order: int = DESCENDING,
        projection: Optional[dict] = None,
    ) -> tuple[list[dict], int]:
        """
        Flexible query with filtering, sorting, and pagination.

        Returns:
            ``(list_of_docs, total_count)`` — total is the unsliced count.
        """
        limit = min(limit, 200)
        query = filter_query or {}

        total = await self._col.count_documents(query)
        cursor = (
            self._col.find(query, projection)
            .sort(sort_field, sort_order)
            .skip(skip)
            .limit(limit)
        )
        docs = await cursor.to_list(length=limit)
        return [_serialize(d) for d in docs], total

    async def search(
        self,
        search_text: str,
        fields: list[str],
        skip: int = 0,
        limit: int = 20,
    ) -> list[dict]:
        """
        Case-insensitive regex search across the specified ``fields``.

        Args:
            search_text: String to search for.
            fields: List of field names to match against.
            skip: Pagination offset.
            limit: Max results.

        Returns:
            List of matching serialized documents.
        """
        limit = min(limit, 200)
        regex = {"$regex": search_text, "$options": "i"}
        query: dict = {"$or": [{f: regex} for f in fields]}
        cursor = self._col.find(query).skip(skip).limit(limit)
        docs = await cursor.to_list(length=limit)
        return [_serialize(d) for d in docs]

    async def delete_many(self, filter_query: dict) -> int:
        """
        Delete all documents matching the filter.

        Args:
            filter_query: MongoDB filter dict (must be non-empty for safety).

        Returns:
            Number of deleted documents.

        Raises:
            ValueError: If ``filter_query`` is empty (safety guard).
        """
        if not filter_query:
            raise ValueError(
                "delete_many requires a non-empty filter to prevent accidental full wipe."
            )
        result = await self._col.delete_many(filter_query)
        logger.info(
            "[{col}] Deleted {n} documents | filter={q}",
            col=self._name,
            n=result.deleted_count,
            q=filter_query,
        )
        return result.deleted_count
