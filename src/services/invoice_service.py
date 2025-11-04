"""
Invoice processing service - main business logic.
"""

import logging
from pathlib import Path
from typing import Optional

from ..core.models import InvoiceData, ProcessingResult, InvoiceType
from ..core.parsers import InvoiceParserFactory
from .tax_service import TaxService
from .ollama_service import OllamaService  # optional
from ..core.config import Settings
from .alegra_service import AlegraService

logger = logging.getLogger(__name__)


class InvoiceService:
    """Main invoice processing service."""
    
    def __init__(self, tax_service: TaxService, alegra_service: AlegraService, ollama_service: Optional[OllamaService] = None, settings: Optional[Settings] = None):
        """Initialize invoice service with dependencies."""
        self.tax_service = tax_service
        self.alegra_service = alegra_service
        self.ollama_service = ollama_service
        self.settings = settings or Settings()
    
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
            # If totals are zero and Ollama is enabled, try LLM post-processing
            if (
                self.settings.ollama_enabled and
                self.ollama_service is not None and
                (invoice_data.total == 0.0 or invoice_data.subtotal == 0.0)
            ):
                try:
                    enhanced: Optional[InvoiceData] = None
                    if invoice_data.raw_text:
                        enhanced = self.ollama_service.parse_text_to_invoice(invoice_data.raw_text)
                    else:
                        # Choose method based on extension
                        lower = file_path.lower()
                        if lower.endswith(('.jpg', '.jpeg', '.png')):
                            enhanced = self.ollama_service.parse_image_to_invoice(file_path)
                        else:
                            # For PDFs without raw_text, skip (already extracted text earlier)
                            pass
                    if enhanced and (enhanced.total > 0 or enhanced.subtotal > 0):
                        invoice_data = enhanced
                except Exception:
                    pass
            
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
