"""
FastAPI application for SuperVincent InvoiceBot.
Thin entry point that assembles routes and middleware.
"""

import logging

from fastapi import FastAPI

from .routes import (
    health_router,
    invoice_router,
    reports_router,
    tax_router,
    cache_router
)
from .middleware import setup_error_handlers, setup_cors

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="SuperVincent InvoiceBot API",
    description="Intelligent Invoice Processing System with Tax Calculation and Alegra Integration",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Setup middleware
setup_cors(app)
setup_error_handlers(app)

# Include routers
app.include_router(health_router)
app.include_router(invoice_router)
app.include_router(reports_router)
app.include_router(tax_router)
app.include_router(cache_router)

# Move /processed/recent to root level for backwards compatibility
from .dependencies import cache_service, RECENT_UPLOADS_KEY
from datetime import datetime


@app.get("/processed/recent")
async def get_recent_processed_compat():
    """Return recently processed invoices (backwards compatibility)."""
    try:
        data = cache_service.get(RECENT_UPLOADS_KEY) or []
        return {
            "status": "success",
            "count": len(data),
            "data": data,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting recent processed: {e}")
        from fastapi import HTTPException
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
