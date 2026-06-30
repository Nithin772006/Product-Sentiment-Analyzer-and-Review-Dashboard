"""
app/repositories/user_repository.py
────────────────────────────────────────
Repository for the ``users`` collection, managing account storage and credential validation.
"""

from __future__ import annotations

from typing import Optional
from app.database.collections import get_users_collection
from app.repositories.base_repository import BaseRepository, DuplicateDocumentError, _utcnow


class UserRepository(BaseRepository):
    """
    Async repository for ``users`` collection operations.
    """

    def __init__(self) -> None:
        super().__init__(get_users_collection())

    async def get_by_username(self, username: str) -> Optional[dict]:
        """
        Look up a user record by exact username.
        """
        normalized = username.strip().lower()
        return await self._col.find_one({"username_normalized": normalized})

    async def create_user(self, username: str, password_hash: str, role: str = "user") -> dict:
        """
        Register a new user record.
        """
        normalized = username.strip().lower()
        
        # Check uniqueness
        existing = await self.get_by_username(username)
        if existing:
            raise DuplicateDocumentError(f"User with username '{username}' already exists.")

        user_doc = {
            "username": username.strip(),
            "username_normalized": normalized,
            "password_hash": password_hash,
            "role": role,
            "created_at": _utcnow(),
        }

        result = await self._col.insert_one(user_doc)
        user_doc["id"] = str(result.inserted_id)
        if "_id" in user_doc:
            del user_doc["_id"]
        return user_doc
