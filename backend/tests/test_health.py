"""
tests/test_health.py
─────────────────────
Integration tests for the /health endpoint.
This is the only fully-implemented endpoint in Phase 1, so it gets tests now.
"""

from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_returns_200(test_app: AsyncClient) -> None:
    """Health endpoint must return HTTP 200."""
    response = await test_app.get("/health")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_health_response_schema(test_app: AsyncClient) -> None:
    """Health response must contain the expected keys."""
    response = await test_app.get("/health")
    data = response.json()

    assert "status" in data
    assert "version" in data
    assert "timestamp" in data
    assert "dependencies" in data
    assert "mongodb" in data["dependencies"]


@pytest.mark.asyncio
async def test_root_redirect(test_app: AsyncClient) -> None:
    """Root endpoint must return 200 with API info."""
    response = await test_app.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "docs" in data
    assert "health" in data
