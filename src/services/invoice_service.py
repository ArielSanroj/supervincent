"""
Invoice processing service - main business logic.
"""

import logging
from pathlib import Path
from typing import Optional

from ..core.models import InvoiceData, ProcessingResult, InvoiceType
from ..core.parsers import InvoiceParserFactory
from .tax_service import TaxService
from .alegra_service import AlegraService

logger = logging.getLogger(__name__)


class InvoiceService:
    """Main invoice processing service."""
    
    def __init__(self, tax_service: TaxService, alegra_service: AlegraService):
        """Initialize invoice service with dependencies."""
        self.tax_service = tax_service
        self.alegra_service = alegra_service
    
    def process_invoice(self, file_path: str) -> ProcessingResult:
        """Process invoice file end-to-end."""
        logger.info(f"🚀 Processing invoice: {file_path}")
        
        try:
            # Validate file exists
            if not Path(file_path).exists():
                return ProcessingResult(
                    success=False,
                    invoice_data=None,
                    tax_result=None,
                    alegra_result=None,
                    error_message=f"File not found: {file_path}"
                )
            
            # Parse invoice data
            invoice_data = self._parse_invoice(file_path)
            if not invoice_data:
                return ProcessingResult(
                    success=False,
                    invoice_data=None,
                    tax_result=None,
                    alegra_result=None,
                    error_message="Failed to parse invoice data"
                )
            
            # Calculate taxes
            tax_result = self.tax_service.calculate_taxes(invoice_data)
            
            # Create in Alegra
            alegra_result = self._create_in_alegra(invoice_data, tax_result)
            
            return ProcessingResult(
                success=True,
                invoice_data=invoice_data,
                tax_result=tax_result,
                alegra_result=alegra_result
            )
            
        except Exception as e:
            logger.error(f"Error processing invoice {file_path}: {e}")
            return ProcessingResult(
                success=False,
                invoice_data=None,
                tax_result=None,
                alegra_result=None,
                error_message=str(e)
            )
    
    def _parse_invoice(self, file_path: str) -> Optional[InvoiceData]:
        """Parse invoice file."""
        return InvoiceParserFactory.parse_invoice(file_path)
    
    def _create_in_alegra(self, invoice_data: InvoiceData, tax_result) -> Optional[dict]:
        """Create invoice in Alegra."""
        if invoice_data.invoice_type == InvoiceType.PURCHASE:
            return self.alegra_service.create_purchase_bill(invoice_data, tax_result)
        else:
            return self.alegra_service.create_sale_invoice(invoice_data, tax_result)
