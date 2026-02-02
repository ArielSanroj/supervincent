"""
Invoice processing handlers.
"""

import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path

from ..schemas import InvoiceProcessingResponse
from ..dependencies import (
    cache_service, invoice_cache, invoice_service,
    security_middleware, RECENT_UPLOADS_KEY
)
from .duplicate_handlers import DuplicateHandlers

logger = logging.getLogger(__name__)


class InvoiceHandlers:
    """Handlers for invoice processing operations."""

    @staticmethod
    def append_recent_upload(entry: Dict[str, Any]) -> None:
        """Append entry to recent uploads list in cache."""
        try:
            current = cache_service.get(RECENT_UPLOADS_KEY) or []
            current.append(entry)
            current = current[-50:]  # Keep only last 50
            cache_service.set(RECENT_UPLOADS_KEY, current, ttl=24 * 3600)
        except Exception as e:
            logger.warning(f"Could not append recent upload: {e}")

    @staticmethod
    def process_single_invoice(
        file_path: str,
        user_id: Optional[str] = None,
        source: str = "path",
        filename: Optional[str] = None
    ) -> Dict[str, Any]:
        """Process a single invoice and return response dict."""
        validated_request = security_middleware.validate_request(file_path, user_id)

        start_time = datetime.now()
        result = invoice_service.process_invoice(validated_request["file_path"])
        processing_time = (datetime.now() - start_time).total_seconds()

        if not result.success:
            InvoiceHandlers._track_failure(file_path, source, filename,
                                          result.error_message, processing_time)
            return InvoiceProcessingResponse(
                success=False,
                error_message=result.error_message,
                processing_time=processing_time
            ).dict()

        return InvoiceHandlers._handle_successful_result(
            result, file_path, source, filename, processing_time
        )

    @staticmethod
    def _handle_successful_result(
        result,
        file_path: str,
        source: str,
        filename: Optional[str],
        processing_time: float
    ) -> Dict[str, Any]:
        """Handle successful invoice processing result."""
        vendor = result.invoice_data.vendor.strip().lower() if result.invoice_data.vendor else ""
        total_amount = result.invoice_data.total
        invoice_type = result.invoice_data.invoice_type.value.lower()
        date = result.invoice_data.date

        duplicates = DuplicateHandlers.check_duplicates(
            vendor, total_amount, invoice_type, date
        )
        is_duplicate = len(duplicates) > 0

        invoice_cache.cache_invoice_data(file_path, result.invoice_data)

        invoice_id = f"inv_{hash(file_path)}"
        response = InvoiceProcessingResponse(
            success=True,
            invoice_id=invoice_id,
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

        response_dict = response.dict()
        entry_data = InvoiceHandlers._build_entry_data(
            invoice_id, source, file_path, filename,
            result, processing_time
        )

        if is_duplicate:
            cache_service.set(f"pending_invoice:{invoice_id}", entry_data, ttl=300)
        else:
            InvoiceHandlers.append_recent_upload(entry_data)

        return response_dict

    @staticmethod
    def _build_entry_data(
        invoice_id: str,
        source: str,
        file_path: str,
        filename: Optional[str],
        result,
        processing_time: float
    ) -> Dict[str, Any]:
        """Build entry data for caching."""
        entry = {
            "invoice_id": invoice_id,
            "timestamp": datetime.now().isoformat(),
            "source": source,
            "file_path": file_path,
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
        if filename:
            entry["filename"] = filename
        return entry

    @staticmethod
    def _track_failure(
        file_path: str,
        source: str,
        filename: Optional[str],
        error_message: str,
        processing_time: float
    ) -> None:
        """Track failed invoice processing."""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "source": source,
            "file_path": file_path,
            "success": False,
            "error_message": error_message,
            "processing_time": processing_time,
        }
        if filename:
            entry["filename"] = filename
        InvoiceHandlers.append_recent_upload(entry)
