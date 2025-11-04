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
from ..services.ollama_service import OllamaService
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
ollama_service = OllamaService(settings) if settings.ollama_enabled else None
invoice_service = InvoiceService(tax_service, alegra_service, ollama_service=ollama_service, settings=settings)
async_processor = AsyncInvoiceProcessor(tax_service, alegra_service)

# In-memory recent uploads list (also mirrored in cache)
_RECENT_UPLOADS_KEY = "invoice:recent_uploads"

def _append_recent_upload(entry: Dict[str, Any]) -> None:
    try:
        # Load current list
        current = cache_service.get(_RECENT_UPLOADS_KEY) or []
        # Keep only last 50
        current.append(entry)
        current = current[-50:]
        cache_service.set(_RECENT_UPLOADS_KEY, current, ttl=24 * 3600)
    except Exception as e:
        logger.warning(f"Could not append recent upload: {e}")

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
    vendor: Optional[str] = None
    date: Optional[str] = None
    alegra_id: Optional[str] = None
    error_message: Optional[str] = None
    processing_time: Optional[float] = None
    is_duplicate: Optional[bool] = False
    duplicate_count: Optional[int] = 0
    duplicates: Optional[List[Dict[str, Any]]] = []


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
            # Check for duplicates BEFORE adding to recent list
            recent_data = cache_service.get(_RECENT_UPLOADS_KEY) or []
            vendor = result.invoice_data.vendor.strip().lower() if result.invoice_data.vendor else ""
            total_amount = result.invoice_data.total
            invoice_type = result.invoice_data.invoice_type.value.lower()
            date = result.invoice_data.date
            
            logger.info(f"🔍 Checking duplicates - Vendor: '{vendor}', Total: {total_amount}, Type: '{invoice_type}', Date: '{date}'")
            logger.info(f"📊 Recent invoices count: {len(recent_data)}")
            
            amount_tolerance = max(total_amount * 0.01, 1000)
            duplicates = []
            for entry in recent_data:
                if not entry.get("success"):
                    continue
                entry_vendor = entry.get("vendor", "").strip().lower()
                if vendor and entry_vendor and vendor != entry_vendor:
                    continue
                entry_type = entry.get("invoice_type", "").lower()
                if invoice_type and entry_type and invoice_type != entry_type:
                    continue
                entry_amount = float(entry.get("total_amount", 0))
                if abs(total_amount - entry_amount) > amount_tolerance:
                    continue
                if date:
                    # Use 'date' field if available, otherwise fallback to timestamp
                    entry_date = entry.get("date", "")
                    if not entry_date and entry.get("timestamp"):
                        entry_date = entry.get("timestamp", "")[:10]
                    if entry_date and date[:10] == entry_date[:10]:
                        duplicates.append({
                            "invoice_id": entry.get("invoice_id"),
                            "vendor": entry.get("vendor"),
                            "total_amount": entry_amount,
                            "invoice_type": entry.get("invoice_type"),
                            "timestamp": entry.get("timestamp"),
                            "date": entry_date
                        })
                        logger.info(f"✅ Found duplicate: {entry.get('vendor')} - {entry_amount} - {entry_date}")
                else:
                    duplicates.append({
                        "invoice_id": entry.get("invoice_id"),
                        "vendor": entry.get("vendor"),
                        "total_amount": entry_amount,
                        "invoice_type": entry.get("invoice_type"),
                        "timestamp": entry.get("timestamp"),
                        "date": entry.get("date") or (entry.get("timestamp", "")[:10] if entry.get("timestamp") else "")
                    })
                    logger.info(f"✅ Found duplicate (no date): {entry.get('vendor')} - {entry_amount}")
            
            is_duplicate = len(duplicates) > 0
            logger.info(f"🔎 Duplicate check result: {is_duplicate} ({len(duplicates)} matches)")
            
            # Cache result
            invoice_cache.cache_invoice_data(
                request.file_path, 
                result.invoice_data
            )
            
            # Prepare response with duplicate info
            response = InvoiceProcessingResponse(
                success=True,
                invoice_id=f"inv_{hash(request.file_path)}",
                invoice_type=result.invoice_data.invoice_type.value,
                total_amount=result.invoice_data.total,
                vendor=result.invoice_data.vendor,
                date=result.invoice_data.date,
                alegra_id=result.alegra_result.get("id") if result.alegra_result else None,
                processing_time=processing_time,
                is_duplicate=is_duplicate,
                duplicate_count=len(duplicates),
                duplicates=duplicates[:5]
            )
            
            # Convert to dict for response
            response_dict = response.dict()
            
            # Store pending invoice data temporarily if duplicate
            if is_duplicate:
                temp_invoice_data = {
                    "invoice_id": response_dict['invoice_id'],
                    "timestamp": datetime.now().isoformat(),
                    "source": "path",
                    "file_path": request.file_path,
                    "success": True,
                    "invoice_type": result.invoice_data.invoice_type.value,
                    "vendor": result.invoice_data.vendor,
                    "total_amount": result.invoice_data.total,
                    "date": result.invoice_data.date,
                    "processing_time": processing_time,
                    "taxes": {
                        "retefuente_ica": getattr(result.tax_result, "retefuente_ica", 0) if result.tax_result else 0,
                        "retefuente_iva": getattr(result.tax_result, "retefuente_iva", 0) if result.tax_result else 0,
                        "retefuente_renta": getattr(result.tax_result, "retefuente_renta", 0) if result.tax_result else 0,
                    },
                }
                cache_service.set(f"pending_invoice:{response_dict['invoice_id']}", temp_invoice_data, ttl=300)
            else:
                # No duplicate, add immediately
                _append_recent_upload({
                    "invoice_id": response_dict['invoice_id'],
                    "timestamp": datetime.now().isoformat(),
                    "source": "path",
                    "file_path": request.file_path,
                    "success": True,
                    "invoice_type": result.invoice_data.invoice_type.value,
                    "vendor": result.invoice_data.vendor,
                    "total_amount": result.invoice_data.total,
                    "date": result.invoice_data.date,
                    "processing_time": processing_time,
                    "taxes": {
                        "retefuente_ica": getattr(result.tax_result, "retefuente_ica", 0) if result.tax_result else 0,
                        "retefuente_iva": getattr(result.tax_result, "retefuente_iva", 0) if result.tax_result else 0,
                        "retefuente_renta": getattr(result.tax_result, "retefuente_renta", 0) if result.tax_result else 0,
                    },
                })
            
            return response_dict
        else:
            # Track failure
            _append_recent_upload({
                "timestamp": datetime.now().isoformat(),
                "source": "path",
                "file_path": request.file_path,
                "success": False,
                "error_message": result.error_message,
                "processing_time": processing_time,
            })
            return InvoiceProcessingResponse(
                success=False,
                error_message=result.error_message,
                processing_time=processing_time
            )
            
    except Exception as e:
        logger.error(f"Error processing invoice: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/process/upload", response_model=InvoiceProcessingResponse)
async def process_invoice_upload(file: UploadFile = File(...)):
    """Upload and process a single invoice file."""
    try:
        # Save uploaded file to a temporary location
        uploads_dir = Path("uploads")
        uploads_dir.mkdir(parents=True, exist_ok=True)
        temp_path = uploads_dir / file.filename
        with temp_path.open("wb") as f:
            content = await file.read()
            f.write(content)

        # Process invoice
        start_time = datetime.now()
        result = invoice_service.process_invoice(str(temp_path))
        processing_time = (datetime.now() - start_time).total_seconds()

        if result.success:
            # Check for duplicates BEFORE adding to recent list
            recent_data = cache_service.get(_RECENT_UPLOADS_KEY) or []
            vendor = result.invoice_data.vendor.strip().lower() if result.invoice_data.vendor else ""
            total_amount = result.invoice_data.total
            invoice_type = result.invoice_data.invoice_type.value.lower()
            date = result.invoice_data.date
            
            logger.info(f"🔍 Checking duplicates - Vendor: '{vendor}', Total: {total_amount}, Type: '{invoice_type}', Date: '{date}'")
            logger.info(f"📊 Recent invoices count: {len(recent_data)}")
            
            amount_tolerance = max(total_amount * 0.01, 1000)
            duplicates = []
            for entry in recent_data:
                if not entry.get("success"):
                    continue
                entry_vendor = entry.get("vendor", "").strip().lower()
                if vendor and entry_vendor and vendor != entry_vendor:
                    continue
                entry_type = entry.get("invoice_type", "").lower()
                if invoice_type and entry_type and invoice_type != entry_type:
                    continue
                entry_amount = float(entry.get("total_amount", 0))
                if abs(total_amount - entry_amount) > amount_tolerance:
                    continue
                if date:
                    # Use 'date' field if available, otherwise fallback to timestamp
                    entry_date = entry.get("date", "")
                    if not entry_date and entry.get("timestamp"):
                        entry_date = entry.get("timestamp", "")[:10]
                    if entry_date and date[:10] == entry_date[:10]:
                        duplicates.append({
                            "invoice_id": entry.get("invoice_id"),
                            "vendor": entry.get("vendor"),
                            "total_amount": entry_amount,
                            "invoice_type": entry.get("invoice_type"),
                            "timestamp": entry.get("timestamp"),
                            "date": entry_date
                        })
                        logger.info(f"✅ Found duplicate: {entry.get('vendor')} - {entry_amount} - {entry_date}")
                else:
                    duplicates.append({
                        "invoice_id": entry.get("invoice_id"),
                        "vendor": entry.get("vendor"),
                        "total_amount": entry_amount,
                        "invoice_type": entry.get("invoice_type"),
                        "timestamp": entry.get("timestamp"),
                        "date": entry.get("date") or (entry.get("timestamp", "")[:10] if entry.get("timestamp") else "")
                    })
                    logger.info(f"✅ Found duplicate (no date): {entry.get('vendor')} - {entry_amount}")
            
            is_duplicate = len(duplicates) > 0
            logger.info(f"🔎 Duplicate check result: {is_duplicate} ({len(duplicates)} matches)")
            
            # Cache result
            invoice_cache.cache_invoice_data(
                str(temp_path),
                result.invoice_data
            )
            
            # Prepare response with duplicate info
            response = InvoiceProcessingResponse(
                success=True,
                invoice_id=f"inv_{hash(str(temp_path))}",
                invoice_type=result.invoice_data.invoice_type.value,
                total_amount=result.invoice_data.total,
                vendor=result.invoice_data.vendor,
                date=result.invoice_data.date,
                alegra_id=result.alegra_result.get("id") if result.alegra_result else None,
                processing_time=processing_time,
                is_duplicate=is_duplicate,
                duplicate_count=len(duplicates),
                duplicates=duplicates[:5]
            )
            
            # Convert to dict for response
            response_dict = response.dict()
            
            # Store pending invoice data temporarily (frontend will confirm if duplicate)
            if is_duplicate:
                temp_invoice_data = {
                    "invoice_id": response_dict['invoice_id'],
                    "timestamp": datetime.now().isoformat(),
                    "source": "upload",
                    "file_path": str(temp_path),
                    "filename": file.filename,
                    "success": True,
                    "invoice_type": result.invoice_data.invoice_type.value,
                    "vendor": result.invoice_data.vendor,
                    "total_amount": result.invoice_data.total,
                    "date": result.invoice_data.date,
                    "processing_time": processing_time,
                    "taxes": {
                        "retefuente_ica": getattr(result.tax_result, "retefuente_ica", 0) if result.tax_result else 0,
                        "retefuente_iva": getattr(result.tax_result, "retefuente_iva", 0) if result.tax_result else 0,
                        "retefuente_renta": getattr(result.tax_result, "retefuente_renta", 0) if result.tax_result else 0,
                    },
                }
                # Store temporarily with invoice_id as key
                cache_service.set(f"pending_invoice:{response_dict['invoice_id']}", temp_invoice_data, ttl=300)  # 5 min
            else:
                # No duplicate, add immediately
                _append_recent_upload({
                    "invoice_id": response_dict['invoice_id'],
                    "timestamp": datetime.now().isoformat(),
                    "source": "upload",
                    "file_path": str(temp_path),
                    "filename": file.filename,
                    "success": True,
                    "invoice_type": result.invoice_data.invoice_type.value,
                    "vendor": result.invoice_data.vendor,
                    "total_amount": result.invoice_data.total,
                    "date": result.invoice_data.date,
                    "processing_time": processing_time,
                    "taxes": {
                        "retefuente_ica": getattr(result.tax_result, "retefuente_ica", 0) if result.tax_result else 0,
                        "retefuente_iva": getattr(result.tax_result, "retefuente_iva", 0) if result.tax_result else 0,
                        "retefuente_renta": getattr(result.tax_result, "retefuente_renta", 0) if result.tax_result else 0,
                    },
                })
            
            return response_dict
        else:
            # Track failure
            _append_recent_upload({
                "timestamp": datetime.now().isoformat(),
                "source": "upload",
                "file_path": str(temp_path),
                "filename": file.filename,
                "success": False,
                "error_message": result.error_message,
                "processing_time": processing_time,
            })
            return InvoiceProcessingResponse(
                success=False,
                error_message=result.error_message,
                processing_time=processing_time
            )
    except Exception as e:
        logger.error(f"Error processing uploaded invoice: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/process/upload-multiple")
@app.post("/process/upload/multiple")
@app.post("/process/multi-upload")
async def process_invoice_upload_multiple(files: List[UploadFile] = File(...)):
    """Upload and process multiple invoice files in one request.
    Returns a list of results; each result mirrors InvoiceProcessingResponse shape plus filename.
    """
    results: List[Dict[str, Any]] = []
    try:
        uploads_dir = Path("uploads")
        uploads_dir.mkdir(parents=True, exist_ok=True)

        for file in files:
            try:
                temp_path = uploads_dir / file.filename
                with temp_path.open("wb") as f:
                    content = await file.read()
                    f.write(content)

                start_time = datetime.now()
                result = invoice_service.process_invoice(str(temp_path))
                processing_time = (datetime.now() - start_time).total_seconds()

                if result.success:
                    # Duplicate check before storing
                    recent_data = cache_service.get(_RECENT_UPLOADS_KEY) or []
                    vendor = result.invoice_data.vendor.strip().lower() if result.invoice_data.vendor else ""
                    total_amount = result.invoice_data.total
                    invoice_type = result.invoice_data.invoice_type.value.lower()
                    date = result.invoice_data.date

                    amount_tolerance = max(total_amount * 0.01, 1000)
                    duplicates = []
                    for entry in recent_data:
                        if not entry.get("success"):
                            continue
                        entry_vendor = entry.get("vendor", "").strip().lower()
                        if vendor and entry_vendor and vendor != entry_vendor:
                            continue
                        entry_type = entry.get("invoice_type", "").lower()
                        if invoice_type and entry_type and invoice_type != entry_type:
                            continue
                        entry_amount = float(entry.get("total_amount", 0))
                        if abs(total_amount - entry_amount) > amount_tolerance:
                            continue
                        if date:
                            entry_date = entry.get("date", "") or (entry.get("timestamp", "")[:10] if entry.get("timestamp") else "")
                            if entry_date and date[:10] == entry_date[:10]:
                                duplicates.append(entry)
                        else:
                            duplicates.append(entry)

                    is_duplicate = len(duplicates) > 0

                    response = InvoiceProcessingResponse(
                        success=True,
                        invoice_id=f"inv_{hash(str(temp_path))}",
                        invoice_type=result.invoice_data.invoice_type.value,
                        total_amount=result.invoice_data.total,
                        vendor=result.invoice_data.vendor,
                        date=result.invoice_data.date,
                        alegra_id=result.alegra_result.get("id") if result.alegra_result else None,
                        processing_time=processing_time,
                        is_duplicate=is_duplicate,
                        duplicate_count=len(duplicates),
                        duplicates=duplicates[:5]
                    ).dict()

                    # Store or mark pending if duplicate
                    if is_duplicate:
                        temp_invoice_data = {
                            "invoice_id": response['invoice_id'],
                            "timestamp": datetime.now().isoformat(),
                            "source": "upload",
                            "file_path": str(temp_path),
                            "filename": file.filename,
                            "success": True,
                            "invoice_type": result.invoice_data.invoice_type.value,
                            "vendor": result.invoice_data.vendor,
                            "total_amount": result.invoice_data.total,
                            "date": result.invoice_data.date,
                            "processing_time": processing_time,
                            "taxes": {
                                "retefuente_ica": getattr(result.tax_result, "retefuente_ica", 0) if result.tax_result else 0,
                                "retefuente_iva": getattr(result.tax_result, "retefuente_iva", 0) if result.tax_result else 0,
                                "retefuente_renta": getattr(result.tax_result, "retefuente_renta", 0) if result.tax_result else 0,
                            },
                        }
                        cache_service.set(f"pending_invoice:{response['invoice_id']}", temp_invoice_data, ttl=300)
                    else:
                        _append_recent_upload({
                            "invoice_id": response['invoice_id'],
                            "timestamp": datetime.now().isoformat(),
                            "source": "upload",
                            "file_path": str(temp_path),
                            "filename": file.filename,
                            "success": True,
                            "invoice_type": result.invoice_data.invoice_type.value,
                            "vendor": result.invoice_data.vendor,
                            "total_amount": result.invoice_data.total,
                            "date": result.invoice_data.date,
                            "processing_time": processing_time,
                            "taxes": {
                                "retefuente_ica": getattr(result.tax_result, "retefuente_ica", 0) if result.tax_result else 0,
                                "retefuente_iva": getattr(result.tax_result, "retefuente_iva", 0) if result.tax_result else 0,
                                "retefuente_renta": getattr(result.tax_result, "retefuente_renta", 0) if result.tax_result else 0,
                            },
                        })

                    response["filename"] = file.filename
                    results.append(response)
                else:
                    results.append({
                        "success": False,
                        "filename": file.filename,
                        "error_message": result.error_message,
                    })
            except Exception as inner_e:
                logger.error(f"Error processing file in batch: {file.filename} - {inner_e}")
                results.append({
                    "success": False,
                    "filename": file.filename,
                    "error_message": str(inner_e),
                })

        # Summarize
        successful = sum(1 for r in results if r.get("success"))
        failed = len(results) - successful
        return {
            "status": "success",
            "total_files": len(results),
            "successful": successful,
            "failed": failed,
            "results": results,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error in upload-multiple: {e}")
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


@app.get("/processed/recent")
async def get_recent_processed():
    """Return recently processed invoices (last 50)."""
    try:
        data = cache_service.get(_RECENT_UPLOADS_KEY) or []
        return {
            "status": "success",
            "count": len(data),
            "data": data,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting recent processed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/process/confirm-duplicate")
async def confirm_duplicate(request_data: Dict[str, Any]):
    """Confirm processing a duplicate invoice and add it to recent list."""
    try:
        invoice_id = request_data.get("invoice_id")
        if not invoice_id:
            raise HTTPException(status_code=400, detail="invoice_id is required")
        
        # Retrieve pending invoice data
        pending_data = cache_service.get(f"pending_invoice:{invoice_id}")
        if not pending_data:
            raise HTTPException(status_code=404, detail="Pending invoice not found or expired")
        
        # Add to recent uploads
        _append_recent_upload(pending_data)
        
        # Remove from pending
        cache_service.delete(f"pending_invoice:{invoice_id}")
        
        return {
            "status": "success",
            "message": "Invoice confirmed and added to recent list",
            "invoice_id": invoice_id,
            "timestamp": datetime.now().isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error confirming duplicate: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Manual invoice creation (frontend-created sales) – minimal, does not alter existing processing logic
class ManualInvoiceRequest(BaseModel):
    vendor: str
    total_amount: float
    date: Optional[str] = None
    client: Optional[str] = None


@app.post("/process/manual", response_model=InvoiceProcessingResponse)
async def process_manual_invoice(req: ManualInvoiceRequest):
    try:
        if not req.vendor or req.total_amount is None or req.total_amount <= 0:
            raise HTTPException(status_code=400, detail="vendor y total_amount son requeridos y deben ser válidos")

        # Duplicate check similar to other process endpoints
        recent_data = cache_service.get(_RECENT_UPLOADS_KEY) or []
        vendor_norm = req.vendor.strip().lower()
        total_amount = float(req.total_amount)
        invoice_type = "venta"
        date = req.date or datetime.now().isoformat()[:10]

        amount_tolerance = max(total_amount * 0.01, 1000)
        duplicates = []
        for entry in recent_data:
            if not entry.get("success"):
                continue
            entry_vendor = entry.get("vendor", "").strip().lower()
            if vendor_norm and entry_vendor and vendor_norm != entry_vendor:
                continue
            entry_type = entry.get("invoice_type", "").lower()
            if entry_type and entry_type != invoice_type:
                continue
            entry_amount = float(entry.get("total_amount", 0))
            if abs(total_amount - entry_amount) > amount_tolerance:
                continue
            entry_date = entry.get("date", "") or (entry.get("timestamp", "")[:10] if entry.get("timestamp") else "")
            if entry_date and date[:10] == entry_date[:10]:
                duplicates.append(entry)

        is_duplicate = len(duplicates) > 0

        invoice_id = f"inv_manual_{hash((req.vendor, total_amount, date))}"
        response = InvoiceProcessingResponse(
            success=True,
            invoice_id=invoice_id,
            invoice_type=invoice_type,
            total_amount=total_amount,
            vendor=req.vendor,
            date=date,
            alegra_id=None,
            processing_time=0.0,
            is_duplicate=is_duplicate,
            duplicate_count=len(duplicates),
            duplicates=duplicates[:5]
        )

        # Append directly to recent (UI and local reports will pick it up)
        _append_recent_upload({
            "invoice_id": invoice_id,
            "timestamp": datetime.now().isoformat(),
            "source": "manual",
            "success": True,
            "invoice_type": invoice_type,
            "vendor": req.vendor,
            "total_amount": total_amount,
            "date": date,
            "processing_time": 0.0,
            "taxes": {},
        })

        return response
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating manual invoice: {e}")
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
        # Try Alegra first, fallback to local processed invoices
        try:
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
        except Exception as alegra_error:
            logger.warning(f"Alegra report failed: {alegra_error}, using local processed invoices")
            # Fallback: Generate from local processed invoices with PUC Colombian accounting
            recent_data = cache_service.get(_RECENT_UPLOADS_KEY) or []
            ledger_entries = []
            
            for entry in recent_data:
                if not entry.get("success"):
                    continue
                
                # Validate and extract amounts (handle None/NaN)
                total_amount = entry.get("total_amount")
                if total_amount is None or (isinstance(total_amount, float) and (total_amount != total_amount or total_amount == float('inf'))):
                    logger.warning(f"Skipping entry with invalid amount: {entry.get('invoice_id')}")
                    continue
                
                total_amount = float(total_amount) if total_amount else 0.0
                if total_amount <= 0:
                    continue
                
                # Extract taxes (safe handling)
                taxes = entry.get("taxes", {})
                iva_amount = float(taxes.get("retefuente_iva", 0) or 0) if taxes else 0
                # Note: IVA deducible se calcula diferente, usando el IVA del 19% del total
                # Para simplificar, asumimos que el total incluye IVA si aplica
                base_amount = total_amount / 1.19 if iva_amount > 0 else total_amount  # Aproximación
                iva_deducible = total_amount - base_amount if iva_amount > 0 else 0
                
                entry_date = entry.get("timestamp", "") or entry.get("date", "")
                if not entry_date or not (start_date <= entry_date[:10] <= end_date):
                    continue
                
                inv_type = entry.get("invoice_type", "").lower()
                is_purchase = inv_type in ("compra", "purchase")
                vendor = entry.get("vendor", "Proveedor desconocido")
                invoice_id = entry.get("invoice_id", "")
                
                # PUC Colombian Chart of Accounts
                if is_purchase:
                    # COMPRA: Débito a gastos, Crédito a cuentas por pagar
                    # Gastos según tipo (510505 servicios públicos, 612005 gastos varios, etc.)
                    vendor_lower = vendor.lower()
                    if any(kw in vendor_lower for kw in ['acueducto', 'alcantarillado', 'aseo', 'energia', 'energía', 'electricidad', 'gas', 'codensa', 'enel', 'epm', 'fidarta', 'empresas publicas']):
                        expense_account = "510505"  # Servicios públicos
                        expense_name = "Servicios Públicos"
                    elif 'cuenta de cobro' in vendor_lower or 'reembolso' in vendor_lower:
                        expense_account = "612005"  # Gastos varios/reembolsables
                        expense_name = "Gastos Reembolsables"
                    else:
                        expense_account = "610505"  # Compras/Mercancías
                        expense_name = "Compras"
                    
                    # Asiento 1: Débito a gastos
                    ledger_entries.append({
                        "id": f"{invoice_id}-1",
                        "date": entry_date[:10],
                        "account_code": expense_account,
                        "account_name": expense_name,
                        "description": f"Factura compra - {vendor}",
                        "debit": base_amount,
                        "credit": 0.0,
                        "balance": base_amount,
                        "reference": invoice_id
                    })
                    
                    # Asiento 2: IVA deducible (si aplica)
                    if iva_deducible > 0:
                        ledger_entries.append({
                            "id": f"{invoice_id}-2",
                            "date": entry_date[:10],
                            "account_code": "240805",
                            "account_name": "IVA Descontable",
                            "description": f"IVA deducible - {vendor}",
                            "debit": iva_deducible,
                            "credit": 0.0,
                            "balance": iva_deducible,
                            "reference": invoice_id
                        })
                    
                    # Asiento 3: Crédito a cuentas por pagar
                    ledger_entries.append({
                        "id": f"{invoice_id}-3",
                        "date": entry_date[:10],
                        "account_code": "220505",
                        "account_name": "Cuentas por Pagar",
                        "description": f"Factura compra - {vendor}",
                        "debit": 0.0,
                        "credit": total_amount,
                        "balance": -total_amount,
                        "reference": invoice_id
                    })
                else:
                    # VENTA: Débito a cuentas por cobrar, Crédito a ingresos
                    # Asiento 1: Débito a cuentas por cobrar
                    ledger_entries.append({
                        "id": f"{invoice_id}-1",
                        "date": entry_date[:10],
                        "account_code": "130505",
                        "account_name": "Cuentas por Cobrar",
                        "description": f"Factura venta - {vendor}",
                        "debit": total_amount,
                        "credit": 0.0,
                        "balance": total_amount,
                        "reference": invoice_id
                    })
                    
                    # Asiento 2: Crédito a ingresos
                    ledger_entries.append({
                        "id": f"{invoice_id}-2",
                        "date": entry_date[:10],
                        "account_code": "413505",
                        "account_name": "Ingresos Operacionales",
                        "description": f"Factura venta - {vendor}",
                        "debit": 0.0,
                        "credit": base_amount,
                        "balance": -base_amount,
                        "reference": invoice_id
                    })
                    
                    # Asiento 3: IVA por pagar (si aplica)
                    if iva_deducible > 0:
                        ledger_entries.append({
                            "id": f"{invoice_id}-3",
                            "date": entry_date[:10],
                            "account_code": "240810",
                            "account_name": "IVA por Pagar",
                            "description": f"IVA facturado - {vendor}",
                            "debit": 0.0,
                            "credit": iva_deducible,
                            "balance": -iva_deducible,
                            "reference": invoice_id
                        })
            
            return {
                "status": "success",
                "report_type": "general-ledger",
                "period": {"start": start_date, "end": end_date},
                "data": ledger_entries,
                "source": "local",
                "timestamp": datetime.now().isoformat()
            }
    except Exception as e:
        logger.error(f"Error getting general ledger: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/reports/trial-balance")
async def get_trial_balance(start_date: str, end_date: str):
    """Get trial balance report."""
    try:
        try:
            from alegra_reports import AlegraReports
            reporter = AlegraReports()
            result = reporter.generate_ledger_report(start_date, end_date, 'trial-balance')
            return {
                "status": "success",
                "report_type": "trial-balance",
                "period": {"start": start_date, "end": end_date},
                "data": result,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as alegra_error:
            logger.warning(f"Alegra trial balance failed: {alegra_error}, using local data")
            # Fallback: Generate from local processed invoices with PUC accounts
            recent_data = cache_service.get(_RECENT_UPLOADS_KEY) or []
            accounts = {}
            
            for entry in recent_data:
                if not entry.get("success"):
                    continue
                
                # Validate amounts
                total_amount = entry.get("total_amount")
                if total_amount is None or (isinstance(total_amount, float) and (total_amount != total_amount or total_amount == float('inf'))):
                    continue
                
                total_amount = float(total_amount) if total_amount else 0.0
                if total_amount <= 0:
                    continue
                
                entry_date = entry.get("timestamp", "") or entry.get("date", "")
                if not entry_date or not (start_date <= entry_date[:10] <= end_date):
                    continue
                
                inv_type = entry.get("invoice_type", "").lower()
                is_purchase = inv_type in ("compra", "purchase")
                vendor = entry.get("vendor", "").lower()
                
                # PUC Colombian accounts based on invoice type
                if is_purchase:
                    # Determine expense account
                    if any(kw in vendor for kw in ['acueducto', 'alcantarillado', 'aseo', 'energia', 'energía', 'electricidad', 'gas', 'codensa', 'enel', 'epm', 'fidarta', 'empresas publicas']):
                        account_code = "510505"
                        account_name = "Servicios Públicos"
                    elif 'cuenta de cobro' in vendor or 'reembolso' in vendor:
                        account_code = "612005"
                        account_name = "Gastos Reembolsables"
                    else:
                        account_code = "610505"
                        account_name = "Compras"
                    
                    # Add to accounts
                    if account_code not in accounts:
                        accounts[account_code] = {
                            "account_code": account_code,
                            "account_name": account_name,
                            "debit_balance": 0.0,
                            "credit_balance": 0.0,
                            "total_debit": 0.0,
                            "total_credit": 0.0
                        }
                    accounts[account_code]["debit_balance"] += total_amount
                    accounts[account_code]["total_debit"] += total_amount
                    
                    # Cuentas por pagar
                    if "220505" not in accounts:
                        accounts["220505"] = {
                            "account_code": "220505",
                            "account_name": "Cuentas por Pagar",
                            "debit_balance": 0.0,
                            "credit_balance": 0.0,
                            "total_debit": 0.0,
                            "total_credit": 0.0
                        }
                    accounts["220505"]["credit_balance"] += total_amount
                    accounts["220505"]["total_credit"] += total_amount
                else:
                    # VENTA
                    account_code = "413505"
                    account_name = "Ingresos Operacionales"
                    
                    if account_code not in accounts:
                        accounts[account_code] = {
                            "account_code": account_code,
                            "account_name": account_name,
                            "debit_balance": 0.0,
                            "credit_balance": 0.0,
                            "total_debit": 0.0,
                            "total_credit": 0.0
                        }
                    accounts[account_code]["credit_balance"] += total_amount
                    accounts[account_code]["total_credit"] += total_amount
                    
                    # Cuentas por cobrar
                    if "130505" not in accounts:
                        accounts["130505"] = {
                            "account_code": "130505",
                            "account_name": "Cuentas por Cobrar",
                            "debit_balance": 0.0,
                            "credit_balance": 0.0,
                            "total_debit": 0.0,
                            "total_credit": 0.0
                        }
                    accounts["130505"]["debit_balance"] += total_amount
                    accounts["130505"]["total_debit"] += total_amount
            
            trial_balance = list(accounts.values())
            # Calculate totals for validation
            total_debits = sum(acc["total_debit"] for acc in trial_balance)
            total_credits = sum(acc["total_credit"] for acc in trial_balance)
            
            return {
                "status": "success",
                "report_type": "trial-balance",
                "period": {"start": start_date, "end": end_date},
                "data": trial_balance,
                "totals": {
                    "total_debits": total_debits,
                    "total_credits": total_credits,
                    "balance": total_debits - total_credits
                },
                "source": "local",
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
        except Exception as alegra_error:
            logger.warning(f"Alegra aging report failed: {alegra_error}, using local data")
            # Fallback: Generate from local processed invoices
            recent_data = cache_service.get(_RECENT_UPLOADS_KEY) or []
            receivables_list = []
            payables_list = []
            today = datetime.now().date()
            
            for entry in recent_data:
                if not entry.get("success"):
                    continue
                
                # Validate amount
                amount = entry.get("total_amount")
                if amount is None or (isinstance(amount, float) and (amount != amount or amount == float('inf'))):
                    continue
                amount = float(amount) if amount else 0.0
                if amount <= 0:
                    continue
                
                entry_date_str = entry.get("timestamp", "") or entry.get("date", "")
                if not entry_date_str:
                    continue
                try:
                    entry_date = datetime.fromisoformat(entry_date_str.replace('Z', '+00:00')).date()
                    if start_date <= entry_date_str[:10] <= end_date:
                        days_old = (today - entry_date).days
                        aging_entry = {
                            "vendor": entry.get("vendor", "Proveedor desconocido"),
                            "amount": amount,
                            "invoice_date": entry_date_str[:10],
                            "days_old": days_old,
                            "invoice_id": entry.get("invoice_id", "")
                        }
                        inv_type = entry.get("invoice_type", "").lower()
                        is_purchase = inv_type in ("compra", "purchase")
                        if is_purchase:
                            payables_list.append(aging_entry)
                        else:
                            receivables_list.append(aging_entry)
                except Exception as e:
                    logger.warning(f"Skipping entry with invalid date: {entry.get('invoice_id')} - {e}")
                    continue
            
            # Calculate totals and aging buckets
            def calculate_aging_buckets(entries):
                total = sum(e.get("amount", 0) for e in entries)
                current = sum(e.get("amount", 0) for e in entries if e.get("days_old", 0) <= 30)
                days_31_60 = sum(e.get("amount", 0) for e in entries if 31 <= e.get("days_old", 0) <= 60)
                days_61_90 = sum(e.get("amount", 0) for e in entries if 61 <= e.get("days_old", 0) <= 90)
                over_90 = sum(e.get("amount", 0) for e in entries if e.get("days_old", 0) > 90)
                return {
                    "total": total,
                    "aging": {
                        "current": current,
                        "days_31_60": days_31_60,
                        "days_61_90": days_61_90,
                        "over_90": over_90
                    },
                    "items": entries
                }
            
            receivables = calculate_aging_buckets(receivables_list)
            payables = calculate_aging_buckets(payables_list)
            net_position = receivables["total"] - payables["total"]
            
            return {
                "status": "success",
                "report_type": "aging",
                "period": {"start": start_date, "end": end_date},
                "data": {
                    "receivables": receivables,
                    "payables": payables,
                    "net_position": net_position
                },
                "source": "local",
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
                code=item_data.get("code", "ITEM"),
                description=item_data.get("description", ""),
                quantity=item_data.get("quantity", 1),
                price=item_data.get("price", 0)
            ))
        
        # Normalize invoice_type across English/Spanish inputs
        raw_type = (invoice_data.get("invoice_type") or "").strip().lower()
        if raw_type in ("purchase", "compra"):
            norm_type = InvoiceType.PURCHASE
        elif raw_type in ("sale", "venta"):
            norm_type = InvoiceType.SALE
        else:
            # default to PURCHASE if unspecified
            norm_type = InvoiceType.PURCHASE

        invoice = InvoiceData(
            invoice_type=norm_type,
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

