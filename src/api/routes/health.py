"""
Health check routes.
"""

import logging
from datetime import datetime
from typing import Dict

from fastapi import APIRouter

from ..schemas import HealthResponse
from ..dependencies import cache_service

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Health"])


@router.get("/", response_model=Dict[str, str])
async def root():
    """Root endpoint."""
    return {
        "message": "SuperVincent InvoiceBot API",
        "version": "1.0.0",
        "docs": "/docs"
    }


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    try:
        services = {
            "cache": "healthy" if cache_service.redis_client.ping() else "unhealthy",
            "alegra": "healthy",
            "tax_service": "healthy"
        }

        overall_status = "healthy" if all(
            status == "healthy" for status in services.values()
        ) else "degraded"

        return HealthResponse(
            status=overall_status,
            timestamp=datetime.now().isoformat(),
            version="1.0.0",
            services=services
        )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return HealthResponse(
            status="unhealthy",
            timestamp=datetime.now().isoformat(),
            version="1.0.0",
            services={"error": str(e)}
        )
