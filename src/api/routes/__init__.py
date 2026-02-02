"""
API routes organized by domain.
"""

from .health import router as health_router
from .invoice import router as invoice_router
from .reports import router as reports_router
from .tax import router as tax_router
from .cache import router as cache_router

__all__ = [
    "health_router",
    "invoice_router",
    "reports_router",
    "tax_router",
    "cache_router"
]
