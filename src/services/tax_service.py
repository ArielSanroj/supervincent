"""
Tax calculation service.
"""

import logging
from typing import Optional

from ..core.models import InvoiceData, TaxResult
from ..core.tax_calculator import ColombianTaxCalculator

logger = logging.getLogger(__name__)


class TaxService:
    """Tax calculation service."""
    
    def __init__(self):
        """Initialize tax service."""
        self.calculator = ColombianTaxCalculator()
        logger.info("🧮 Tax service initialized")
    
    def calculate_taxes(self, invoice_data: InvoiceData) -> Optional[TaxResult]:
        """Calculate taxes for invoice."""
        try:
            # Convert InvoiceData to tax calculator format
            tax_invoice_data = self._convert_to_tax_format(invoice_data)
            
            # Calculate taxes
            result = self.calculator.calculate_taxes(tax_invoice_data)
            
            # Convert to our TaxResult format
            return TaxResult(
                iva_amount=result.iva_amount,
                iva_rate=result.iva_rate,
                retefuente_renta=result.retefuente_renta,
                retefuente_iva=result.retefuente_iva,
                retefuente_ica=result.retefuente_ica,
                total_withholdings=result.total_withholdings,
                net_amount=result.net_amount,
                compliance_status=result.compliance_status,
                tax_breakdown=result.tax_breakdown
            )
            
        except Exception as e:
            logger.error(f"Error calculating taxes: {e}")
            return None
    
    def _convert_to_tax_format(self, invoice_data: InvoiceData):
        """Convert InvoiceData to tax calculator format."""
        from ..core.tax_calculator import InvoiceData as TaxInvoiceData
        
        return TaxInvoiceData(
            base_amount=invoice_data.subtotal,
            total_amount=invoice_data.total,
            iva_amount=invoice_data.taxes,
            iva_rate=invoice_data.taxes / invoice_data.subtotal if invoice_data.subtotal > 0 else 0,
            item_type="general",
            description=invoice_data.items[0].description if invoice_data.items else "",
            vendor_nit=invoice_data.vendor_nit or "",
            vendor_regime=invoice_data.vendor_regime,
            vendor_city=invoice_data.vendor_city,
            buyer_nit=invoice_data.buyer_nit or "",
            buyer_regime=invoice_data.buyer_regime,
            buyer_city=invoice_data.buyer_city,
            invoice_date=invoice_data.date,
            invoice_number=invoice_data.invoice_number or ""
        )
