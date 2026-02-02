"""
Invoice processing routes.
"""

import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path

from fastapi import APIRouter, HTTPException, UploadFile, File, BackgroundTasks

from ..schemas import (
    InvoiceProcessingRequest,
    InvoiceProcessingResponse,
    BatchProcessingRequest,
    BatchProcessingResponse,
    ManualInvoiceRequest
)
from ..dependencies import (
    cache_service, invoice_cache, invoice_service,
    security_middleware, async_processor, RECENT_UPLOADS_KEY
)
from ..handlers.invoice_handlers import InvoiceHandlers
from ..handlers.duplicate_handlers import DuplicateHandlers

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/process", tags=["Invoice Processing"])


@router.post("", response_model=InvoiceProcessingResponse)
async def process_invoice(
    request: InvoiceProcessingRequest,
    background_tasks: BackgroundTasks
):
    """Process a single invoice."""
    try:
        result = InvoiceHandlers.process_single_invoice(
            request.file_path,
            request.user_id,
            source="path"
        )
        return result
    except Exception as e:
        logger.error(f"Error processing invoice: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/upload", response_model=InvoiceProcessingResponse)
async def process_invoice_upload(file: UploadFile = File(...)):
    """Upload and process a single invoice file."""
    try:
        uploads_dir = Path("uploads")
        uploads_dir.mkdir(parents=True, exist_ok=True)
        temp_path = uploads_dir / file.filename

        with temp_path.open("wb") as f:
            content = await file.read()
            f.write(content)

        result = InvoiceHandlers.process_single_invoice(
            str(temp_path),
            user_id=None,
            source="upload",
            filename=file.filename
        )
        return result
    except Exception as e:
        logger.error(f"Error processing uploaded invoice: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/upload-multiple")
@router.post("/upload/multiple")
@router.post("/multi-upload")
async def process_invoice_upload_multiple(files: List[UploadFile] = File(...)):
    """Upload and process multiple invoice files in one request."""
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

                result = InvoiceHandlers.process_single_invoice(
                    str(temp_path),
                    user_id=None,
                    source="upload",
                    filename=file.filename
                )
                result["filename"] = file.filename
                results.append(result)
            except Exception as inner_e:
                logger.error(f"Error processing file in batch: {file.filename} - {inner_e}")
                results.append({
                    "success": False,
                    "filename": file.filename,
                    "error_message": str(inner_e),
                })

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


@router.post("/batch", response_model=BatchProcessingResponse)
async def process_batch(request: BatchProcessingRequest):
    """Process multiple invoices."""
    try:
        validated_paths = []
        for file_path in request.file_paths:
            validated_request = security_middleware.validate_request(
                file_path, request.user_id
            )
            validated_paths.append(validated_request["file_path"])

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


@router.post("/directory")
async def process_directory(directory_path: str, user_id: Optional[str] = None):
    """Process all invoices in a directory."""
    try:
        directory = Path(directory_path)
        if not directory.exists():
            raise HTTPException(status_code=404, detail="Directory not found")

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


@router.post("/confirm-duplicate")
async def confirm_duplicate(request_data: Dict[str, Any]):
    """Confirm processing a duplicate invoice and add it to recent list."""
    try:
        invoice_id = request_data.get("invoice_id")
        if not invoice_id:
            raise HTTPException(status_code=400, detail="invoice_id is required")

        pending_data = cache_service.get(f"pending_invoice:{invoice_id}")
        if not pending_data:
            raise HTTPException(
                status_code=404,
                detail="Pending invoice not found or expired"
            )

        InvoiceHandlers.append_recent_upload(pending_data)
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


@router.post("/manual", response_model=InvoiceProcessingResponse)
async def process_manual_invoice(req: ManualInvoiceRequest):
    """Create a manual invoice entry."""
    try:
        if not req.vendor or req.total_amount is None or req.total_amount <= 0:
            raise HTTPException(
                status_code=400,
                detail="vendor y total_amount son requeridos y deben ser validos"
            )

        vendor_norm = req.vendor.strip().lower()
        total_amount = float(req.total_amount)
        invoice_type = "venta"
        date = req.date or datetime.now().isoformat()[:10]

        duplicates = DuplicateHandlers.check_duplicates(
            vendor_norm, total_amount, invoice_type, date
        )
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

        InvoiceHandlers.append_recent_upload({
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
