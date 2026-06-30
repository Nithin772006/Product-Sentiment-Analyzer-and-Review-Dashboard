"""
app/api/v1/__init__.py
"""
from fastapi import APIRouter

from app.api.v1 import health, products

# Aggregated v1 router — mounted at /api/v1 in main.py
api_v1_router = APIRouter(prefix="/api/v1")
api_v1_router.include_router(products.router)

# Health is mounted at root level (/health) — included separately in main.py
health_router = health.router

__all__ = ["api_v1_router", "health_router"]
