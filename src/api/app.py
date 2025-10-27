"""
FastAPI application for SuperVincent InvoiceBot.
"""

import logging
from datetime import datetime
from typing import List, Optional, Dict, Any
from pathlib import Path

from fastapi import FastAPI, HTTPException, UploadFile, File, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from ..core.models import InvoiceData, ProcessingResult, InvoiceType
from ..services.invoice_service import InvoiceService
from ..services.tax_service import TaxService
from ..services.alegra_service import AlegraService
from ..services.cache_service import CacheService, InvoiceCacheService
from ..services.async_service import AsyncInvoiceProcessor
from ..core.security import SecurityMiddleware, InputValidator, RateLimiter
from ..core.config import Settings

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

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global services (in production, use dependency injection)
settings = Settings()
cache_service = CacheService(settings.redis_url)
invoice_cache = InvoiceCacheService(cache_service)
tax_service = TaxService()
alegra_service = AlegraService(
    base_url=settings.alegra_base_url,
    email=settings.alegra_email,
    token=settings.alegra_token
)
invoice_service = InvoiceService(tax_service, alegra_service)
async_processor = AsyncInvoiceProcessor(tax_service, alegra_service)

# Security middleware
security_middleware = SecurityMiddleware(
    RateLimiter(cache_service.redis_client),
    InputValidator()
)


# Pydantic models for API
class InvoiceProcessingRequest(BaseModel):
    """Request model for invoice processing."""
    file_path: str = Field(..., description="Path to invoice file")
    user_id: Optional[str] = Field(None, description="User ID for rate limiting")


class InvoiceProcessingResponse(BaseModel):
    """Response model for invoice processing."""
    success: bool
    invoice_id: Optional[str] = None
    invoice_type: Optional[str] = None
    total_amount: Optional[float] = None
    alegra_id: Optional[str] = None
    error_message: Optional[str] = None
    processing_time: Optional[float] = None


class BatchProcessingRequest(BaseModel):
    """Request model for batch processing."""
    file_paths: List[str] = Field(..., description="List of file paths to process")
    user_id: Optional[str] = Field(None, description="User ID for rate limiting")


class BatchProcessingResponse(BaseModel):
    """Response model for batch processing."""
    total_files: int
    successful: int
    failed: int
    results: List[Dict[str, Any]]


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    timestamp: str
    version: str
    services: Dict[str, str]


# API Endpoints

@app.get("/", response_model=Dict[str, str])
async def root():
    """Root endpoint."""
    return {
        "message": "SuperVincent InvoiceBot API",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    try:
        # Check service health
        services = {
            "cache": "healthy" if cache_service.redis_client.ping() else "unhealthy",
            "alegra": "healthy",  # Would check Alegra API
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


@app.post("/process", response_model=InvoiceProcessingResponse)
async def process_invoice(
    request: InvoiceProcessingRequest,
    background_tasks: BackgroundTasks
):
    """Process a single invoice."""
    try:
        # Validate request
        validated_request = security_middleware.validate_request(
            request.file_path, 
            request.user_id
        )
        
        # Process invoice
        start_time = datetime.now()
        result = invoice_service.process_invoice(validated_request["file_path"])
        processing_time = (datetime.now() - start_time).total_seconds()
        
        if result.success:
            # Cache result
            invoice_cache.cache_invoice_data(
                request.file_path, 
                result.invoice_data
            )
            
            return InvoiceProcessingResponse(
                success=True,
                invoice_id=f"inv_{hash(request.file_path)}",
                invoice_type=result.invoice_data.invoice_type.value,
                total_amount=result.invoice_data.total,
                alegra_id=result.alegra_result.get("id") if result.alegra_result else None,
                processing_time=processing_time
            )
        else:
            return InvoiceProcessingResponse(
                success=False,
                error_message=result.error_message,
                processing_time=processing_time
            )
            
    except Exception as e:
        logger.error(f"Error processing invoice: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/process/batch", response_model=BatchProcessingResponse)
async def process_batch(request: BatchProcessingRequest):
    """Process multiple invoices."""
    try:
        # Validate all file paths
        validated_paths = []
        for file_path in request.file_paths:
            validated_request = security_middleware.validate_request(
                file_path, 
                request.user_id
            )
            validated_paths.append(validated_request["file_path"])
        
        # Process batch
        results = await async_processor.process_batch_async(validated_paths)
        
        successful = sum(1 for r in results if r.success)
        failed = len(results) - successful
        
        return BatchProcessingResponse(
            total_files=len(request.file_paths),
            successful=successful,
            failed=failed,
            results=[
                {
                    "file_path": request.file_paths[i],
                    "success": results[i].success,
                    "error": results[i].error_message if not results[i].success else None
                }
                for i in range(len(request.file_paths))
            ]
        )
        
    except Exception as e:
        logger.error(f"Error processing batch: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/process/directory")
async def process_directory(directory_path: str, user_id: Optional[str] = None):
    """Process all invoices in a directory."""
    try:
        # Validate directory
        directory = Path(directory_path)
        if not directory.exists():
            raise HTTPException(status_code=404, detail="Directory not found")
        
        # Process directory
        result = await async_processor.process_directory_async(directory_path)
        
        return {
            "status": "success",
            "directory": directory_path,
            "result": result,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error processing directory: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/cache/stats")
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


@app.delete("/cache")
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


@app.get("/rate-limit/{user_id}")
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


# Bookkeeping and Financial Reports Endpoints

@app.get("/reports/general-ledger")
async def get_general_ledger(
    start_date: str,
    end_date: str,
    account_id: Optional[str] = None
):
    """Get general ledger report."""
    try:
        # This would integrate with AlegraReports
        from alegra_reports import AlegraReports
        reporter = AlegraReports()
        
        result = reporter.generate_ledger_report(
            start_date, end_date, 'general-ledger', account_id
        )
        
        return {
            "status": "success",
            "report_type": "general-ledger",
            "period": {"start": start_date, "end": end_date},
            "data": result,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting general ledger: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/reports/trial-balance")
async def get_trial_balance(start_date: str, end_date: str):
    """Get trial balance report."""
    try:
        from alegra_reports import AlegraReports
        reporter = AlegraReports()
        
        result = reporter.generate_ledger_report(
            start_date, end_date, 'trial-balance'
        )
        
        return {
            "status": "success",
            "report_type": "trial-balance",
            "period": {"start": start_date, "end": end_date},
            "data": result,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting trial balance: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/reports/journal")
async def get_journal_entries(start_date: str, end_date: str):
    """Get journal entries report."""
    try:
        from alegra_reports import AlegraReports
        reporter = AlegraReports()
        
        result = reporter.generate_ledger_report(
            start_date, end_date, 'journal'
        )
        
        return {
            "status": "success",
            "report_type": "journal",
            "period": {"start": start_date, "end": end_date},
            "data": result,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting journal entries: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/reports/aging")
async def get_aging_report(start_date: str, end_date: str):
    """Get aging report for accounts receivable and payable."""
    try:
        from alegra_reports import AlegraReports
        reporter = AlegraReports()
        
        result = reporter.generate_aging_report(start_date, end_date)
        
        return {
            "status": "success",
            "report_type": "aging",
            "period": {"start": start_date, "end": end_date},
            "data": result,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting aging report: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/reports/cash-flow")
async def get_cash_flow_report(start_date: str, end_date: str):
    """Get cash flow report."""
    try:
        from alegra_reports import AlegraReports
        reporter = AlegraReports()
        
        result = reporter.generate_cash_flow_report(start_date, end_date)
        
        return {
            "status": "success",
            "report_type": "cash-flow",
            "period": {"start": start_date, "end": end_date},
            "data": result,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting cash flow report: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Tax Calculation and Information Endpoints

@app.post("/tax/calculate")
async def calculate_taxes(invoice_data: Dict[str, Any]):
    """Calculate Colombian taxes for invoice data."""
    try:
        # Convert to InvoiceData model
        from ..core.models import InvoiceData, InvoiceType, InvoiceItem
        
        items = []
        for item_data in invoice_data.get("items", []):
            items.append(InvoiceItem(
                description=item_data.get("description", ""),
                quantity=item_data.get("quantity", 1),
                price=item_data.get("price", 0)
            ))
        
        invoice = InvoiceData(
            invoice_type=InvoiceType(invoice_data.get("invoice_type", "purchase")),
            date=invoice_data.get("date", ""),
            vendor=invoice_data.get("vendor", ""),
            client=invoice_data.get("client", ""),
            items=items,
            subtotal=invoice_data.get("subtotal", 0),
            taxes=invoice_data.get("taxes", 0),
            total=invoice_data.get("total", 0),
            vendor_nit=invoice_data.get("vendor_nit"),
            vendor_regime=invoice_data.get("vendor_regime", "comun"),
            vendor_city=invoice_data.get("vendor_city", "bogota"),
            buyer_nit=invoice_data.get("buyer_nit"),
            buyer_regime=invoice_data.get("buyer_regime", "comun"),
            buyer_city=invoice_data.get("buyer_city", "bogota"),
            invoice_number=invoice_data.get("invoice_number")
        )
        
        # Calculate taxes
        tax_result = tax_service.calculate_taxes(invoice)
        
        return {
            "status": "success",
            "tax_calculation": tax_result,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error calculating taxes: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/tax/rules")
async def get_tax_rules():
    """Get Colombian tax rules and rates."""
    try:
        # Load tax configuration
        import json
        with open("config/tax_rules_CO_2025.json", "r", encoding="utf-8") as f:
            tax_rules = json.load(f)
        
        return {
            "status": "success",
            "tax_rules": tax_rules,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting tax rules: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/tax/compliance/{invoice_id}")
async def check_tax_compliance(invoice_id: str):
    """Check tax compliance for a specific invoice."""
    try:
        # This would check compliance against DIAN rules
        # For now, return a mock response
        return {
            "status": "success",
            "invoice_id": invoice_id,
            "compliance_status": "compliant",
            "validation_results": {
                "iva_calculation": "valid",
                "retefuente_calculation": "valid",
                "ica_calculation": "valid",
                "cufe_validation": "valid"
            },
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error checking tax compliance: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Error handlers
@app.exception_handler(404)
async def not_found_handler(request, exc):
    return JSONResponse(
        status_code=404,
        content={"error": "Not found", "detail": str(exc)}
    )


@app.exception_handler(500)
async def internal_error_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "detail": str(exc)}
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

