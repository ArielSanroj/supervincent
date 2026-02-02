"""
Cache management routes.
"""

import logging
from datetime import datetime

from fastapi import APIRouter, HTTPException

from ..dependencies import cache_service, security_middleware

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Cache Management"])


@router.get("/cache/stats")
async def get_cache_stats():
    """Get cache statistics."""
    try:
        stats = cache_service.get_stats()
        return {
            "status": "success",
            "stats": stats,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting cache stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/cache")
async def clear_cache():
    """Clear all cache data."""
    try:
        cache_service.redis_client.flushdb()
        return {
            "status": "success",
            "message": "Cache cleared",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error clearing cache: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/rate-limit/{user_id}")
async def get_rate_limit(user_id: str):
    """Get rate limit information for user."""
    try:
        rate_key = f"rate_limit:{user_id}"
        is_allowed, rate_info = security_middleware.rate_limiter.is_allowed(rate_key)

        return {
            "user_id": user_id,
            "is_allowed": is_allowed,
            "rate_info": rate_info,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting rate limit: {e}")
        raise HTTPException(status_code=500, detail=str(e))
