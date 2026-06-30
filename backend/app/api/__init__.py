"""
app/api/__init__.py
"""
from app.api.v1 import api_v1_router, health_router

__all__ = ["api_v1_router", "health_router"]
