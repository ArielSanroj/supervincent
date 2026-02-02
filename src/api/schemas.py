"""
Pydantic schemas for API request/response models.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


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


class ManualInvoiceRequest(BaseModel):
    """Request model for manual invoice creation."""
    vendor: str
    total_amount: float
    date: Optional[str] = None
    client: Optional[str] = None
