"""
Financial report handlers.
"""

import logging
from datetime import datetime
from typing import Dict, Any, List, Optional

from ..dependencies import cache_service, RECENT_UPLOADS_KEY

logger = logging.getLogger(__name__)


class ReportHandlers:
    """Handlers for financial report generation."""

    @staticmethod
    def generate_local_ledger(
        start_date: str,
        end_date: str
    ) -> List[Dict[str, Any]]:
        """Generate ledger entries from local processed invoices."""
        recent_data = cache_service.get(RECENT_UPLOADS_KEY) or []
        ledger_entries = []

        for entry in recent_data:
            if not entry.get("success"):
                continue

            total_amount = ReportHandlers._validate_amount(entry)
            if total_amount is None or total_amount <= 0:
                continue

            entry_date = entry.get("timestamp", "") or entry.get("date", "")
            if not entry_date or not (start_date <= entry_date[:10] <= end_date):
                continue

            inv_type = entry.get("invoice_type", "").lower()
            is_purchase = inv_type in ("compra", "purchase")
            vendor = entry.get("vendor", "Proveedor desconocido")
            invoice_id = entry.get("invoice_id", "")

            taxes = entry.get("taxes", {})
            iva_amount = float(taxes.get("retefuente_iva", 0) or 0) if taxes else 0
            base_amount = total_amount / 1.19 if iva_amount > 0 else total_amount
            iva_deducible = total_amount - base_amount if iva_amount > 0 else 0

            if is_purchase:
                ledger_entries.extend(
                    ReportHandlers._create_purchase_entries(
                        invoice_id, entry_date, vendor, base_amount,
                        iva_deducible, total_amount
                    )
                )
            else:
                ledger_entries.extend(
                    ReportHandlers._create_sale_entries(
                        invoice_id, entry_date, vendor, base_amount,
                        iva_deducible, total_amount
                    )
                )

        return ledger_entries

    @staticmethod
    def _validate_amount(entry: Dict[str, Any]) -> Optional[float]:
        """Validate and extract amount from entry."""
        total_amount = entry.get("total_amount")
        if total_amount is None:
            return None
        if isinstance(total_amount, float):
            if total_amount != total_amount or total_amount == float('inf'):
                return None
        return float(total_amount) if total_amount else 0.0

    @staticmethod
    def _get_expense_account(vendor: str) -> tuple:
        """Determine expense account based on vendor."""
        vendor_lower = vendor.lower()
        utility_keywords = [
            'acueducto', 'alcantarillado', 'aseo', 'energia', 'energia',
            'electricidad', 'gas', 'codensa', 'enel', 'epm', 'fidarta',
            'empresas publicas'
        ]
        if any(kw in vendor_lower for kw in utility_keywords):
            return "510505", "Servicios Publicos"
        elif 'cuenta de cobro' in vendor_lower or 'reembolso' in vendor_lower:
            return "612005", "Gastos Reembolsables"
        else:
            return "610505", "Compras"

    @staticmethod
    def _create_purchase_entries(
        invoice_id: str,
        entry_date: str,
        vendor: str,
        base_amount: float,
        iva_deducible: float,
        total_amount: float
    ) -> List[Dict[str, Any]]:
        """Create ledger entries for a purchase invoice."""
        entries = []
        expense_account, expense_name = ReportHandlers._get_expense_account(vendor)

        entries.append({
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

        if iva_deducible > 0:
            entries.append({
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

        entries.append({
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

        return entries

    @staticmethod
    def _create_sale_entries(
        invoice_id: str,
        entry_date: str,
        vendor: str,
        base_amount: float,
        iva_deducible: float,
        total_amount: float
    ) -> List[Dict[str, Any]]:
        """Create ledger entries for a sale invoice."""
        entries = []

        entries.append({
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

        entries.append({
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

        if iva_deducible > 0:
            entries.append({
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

        return entries
