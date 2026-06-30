"""
tests/conftest.py
──────────────────
Shared pytest fixtures for the backend test suite.

Provides:
    - `test_app`  : AsyncClient-wrapped FastAPI test application
    - `test_db`   : Motor test database (isolated from dev/prod)
    - `settings`  : Overridden Settings for testing
"""

from __future__ import annotations

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.config import get_settings
from app.main import create_app


@pytest.fixture(scope="session")
def anyio_backend():
    """Use asyncio as the anyio backend for all async tests."""
    return "asyncio"


@pytest_asyncio.fixture(scope="session")
async def test_app():
    """
    Yield a configured FastAPI test application.
    The lifespan (DB connect/disconnect) runs automatically.
    """
    app = create_app()
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        yield client
