"""
app/utils/bson.py
──────────────────
Utilities for BSON ObjectId conversion, datetime serialization,
and standardized response formatting.

All modules should import from here instead of calling bson / datetime directly.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from bson import ObjectId
from bson.errors import InvalidId


# ── ObjectId helpers ──────────────────────────────────────────────────────────

def str_to_objectid(oid: str) -> ObjectId:
    """
    Convert a hex string to a BSON ObjectId.

    Raises:
        ValueError: If `oid` is not a valid 24-char hex ObjectId string.
    """
    try:
        return ObjectId(oid)
    except (InvalidId, TypeError) as exc:
        raise ValueError(f"Invalid ObjectId: '{oid}'") from exc


def objectid_to_str(oid: ObjectId | str | None) -> str | None:
    """Convert a BSON ObjectId to its hex string representation."""
    if oid is None:
        return None
    return str(oid)


def is_valid_objectid(value: str) -> bool:
    """Return True if `value` is a valid 24-char hex ObjectId string."""
    return ObjectId.is_valid(value)


# ── Datetime helpers ──────────────────────────────────────────────────────────

def utcnow() -> datetime:
    """Return the current UTC datetime as a timezone-aware datetime object."""
    return datetime.now(tz=timezone.utc)


def ensure_utc(dt: datetime | None) -> datetime | None:
    """Attach UTC timezone info to a naive datetime (no-op if already aware)."""
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


# ── Document serialization ────────────────────────────────────────────────────

def serialize_doc(doc: dict | None) -> dict:
    """
    Recursively prepare a MongoDB document dict for JSON output.

    Transformations applied:
        ``_id``      → ``"id"`` (string)
        ObjectId     → string
        datetime     → ISO 8601 string
        nested dicts → recursively serialized
        list items   → recursively serialized if dict

    Returns an empty dict when `doc` is None.
    """
    if doc is None:
        return {}

    result: dict = {}
    for key, value in doc.items():
        if key == "_id":
            result["id"] = str(value)
        elif isinstance(value, ObjectId):
            result[key] = str(value)
        elif isinstance(value, datetime):
            result[key] = value.isoformat()
        elif isinstance(value, dict):
            result[key] = serialize_doc(value)
        elif isinstance(value, list):
            result[key] = [
                serialize_doc(item) if isinstance(item, dict) else item
                for item in value
            ]
        else:
            result[key] = value

    return result


# ── JSON serialization ────────────────────────────────────────────────────────

class _MongoJSONEncoder(json.JSONEncoder):
    """Custom JSON encoder that handles ObjectId and datetime objects."""

    def default(self, obj: Any) -> Any:
        if isinstance(obj, ObjectId):
            return str(obj)
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)


def to_json(obj: Any, indent: int = 2) -> str:
    """Serialize any object (including MongoDB docs) to a JSON string."""
    return json.dumps(obj, cls=_MongoJSONEncoder, indent=indent, default=str)


# ── Response formatting ───────────────────────────────────────────────────────

def format_response(
    data: Any = None,
    message: str = "Success",
    success: bool = True,
    total: int | None = None,
    page: int | None = None,
    limit: int | None = None,
) -> dict:
    """
    Build a standardized API / script response envelope.

    Shape::

        {
            "success": bool,
            "message": str,
            "data":    any,
            "total":   int | None,
            "page":    int | None,
            "limit":   int | None,
        }
    """
    resp: dict = {
        "success": success,
        "message": message,
        "data": data,
    }
    if total is not None:
        resp["total"] = total
    if page is not None:
        resp["page"] = page
    if limit is not None:
        resp["limit"] = limit
    return resp


def format_error(message: str, detail: str | None = None) -> dict:
    """Build a standardized error response."""
    resp: dict = {"success": False, "message": message}
    if detail:
        resp["detail"] = detail
    return resp
