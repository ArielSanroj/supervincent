"""
Dependency injection and service initialization for the API.
"""

import logging
from ..core.config import Settings
from ..services.cache_service import CacheService, InvoiceCacheService
from ..services.tax_service import TaxService
from ..services.alegra_service import AlegraService
from ..services.ollama_service import OllamaService
from ..services.invoice_service import InvoiceService
from ..services.async_service import AsyncInvoiceProcessor
from ..core.security import SecurityMiddleware, InputValidator, RateLimiter

logger = logging.getLogger(__name__)

# Global settings
settings = Settings()

# Cache services
cache_service = CacheService(settings.redis_url)
invoice_cache = InvoiceCacheService(cache_service)

# Business services
tax_service = TaxService()
alegra_service = AlegraService(
    base_url=settings.alegra_base_url,
    email=settings.alegra_email,
    token=settings.alegra_token
)

# Optional Ollama service
ollama_service = OllamaService(settings) if settings.ollama_enabled else None

# Invoice processing services
invoice_service = InvoiceService(
    tax_service,
    alegra_service,
    ollama_service=ollama_service,
    settings=settings
)
async_processor = AsyncInvoiceProcessor(tax_service, alegra_service)

# Security middleware
security_middleware = SecurityMiddleware(
    RateLimiter(cache_service.redis_client),
    InputValidator()
)

# Cache key for recent uploads
RECENT_UPLOADS_KEY = "invoice:recent_uploads"


def get_cache_service() -> CacheService:
    """Dependency for cache service."""
    return cache_service


def get_invoice_cache() -> InvoiceCacheService:
    """Dependency for invoice cache service."""
    return invoice_cache


def get_tax_service() -> TaxService:
    """Dependency for tax service."""
    return tax_service


def get_alegra_service() -> AlegraService:
    """Dependency for Alegra service."""
    return alegra_service


def get_invoice_service() -> InvoiceService:
    """Dependency for invoice service."""
    return invoice_service


def get_async_processor() -> AsyncInvoiceProcessor:
    """Dependency for async processor."""
    return async_processor


def get_security_middleware() -> SecurityMiddleware:
    """Dependency for security middleware."""
    return security_middleware
