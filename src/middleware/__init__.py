"""Middleware package for FastAPI application."""

from .protection_middleware import (
    ProtectionMiddleware,
    get_default_protection_middleware,
)

__all__ = [
    "ProtectionMiddleware",
    "get_default_protection_middleware",
]
