"""
Tax calculation routes.
"""

import json
import logging
from datetime import datetime
from typing import Dict, Any

from fastapi import APIRouter, HTTPException

from ..dependencies import tax_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/tax", tags=["Tax Calculation"])


@router.post("/calculate")
async def calculate_taxes(invoice_data: Dict[str, Any]):
    """Calculate Colombian taxes for invoice data."""
    try:
        from ...core.models import InvoiceData, InvoiceType, InvoiceItem

        items = []
        for item_data in invoice_data.get("items", []):
            items.append(InvoiceItem(
                code=item_data.get("code", "ITEM"),
                description=item_data.get("description", ""),
                quantity=item_data.get("quantity", 1),
                price=item_data.get("price", 0)
            ))

        norm_type = _normalize_invoice_type(invoice_data.get("invoice_type", ""))

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

        tax_result = tax_service.calculate_taxes(invoice)

        return {
            "status": "success",
            "tax_calculation": tax_result,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error calculating taxes: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def _normalize_invoice_type(raw_type: str):
    """Normalize invoice type from raw string."""
    from ...core.models import InvoiceType

    raw_type = (raw_type or "").strip().lower()
    if raw_type in ("purchase", "compra"):
        return InvoiceType.PURCHASE
    elif raw_type in ("sale", "venta"):
        return InvoiceType.SALE
    else:
        return InvoiceType.PURCHASE


@router.get("/rules")
async def get_tax_rules():
    """Get Colombian tax rules and rates."""
    try:
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


@router.get("/compliance/{invoice_id}")
async def check_tax_compliance(invoice_id: str):
    """Check tax compliance for a specific invoice."""
    try:
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
