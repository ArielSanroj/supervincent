"""
Duplicate detection handlers.
"""

import logging
from typing import Dict, Any, List, Optional

from ..dependencies import cache_service, RECENT_UPLOADS_KEY

logger = logging.getLogger(__name__)


class DuplicateHandlers:
    """Handlers for duplicate invoice detection."""

    @staticmethod
    def check_duplicates(
        vendor: str,
        total_amount: float,
        invoice_type: str,
        date: Optional[str]
    ) -> List[Dict[str, Any]]:
        """Check for duplicate invoices in recent uploads."""
        recent_data = cache_service.get(RECENT_UPLOADS_KEY) or []

        logger.info(
            f"Checking duplicates - Vendor: '{vendor}', "
            f"Total: {total_amount}, Type: '{invoice_type}', Date: '{date}'"
        )
        logger.info(f"Recent invoices count: {len(recent_data)}")

        amount_tolerance = max(total_amount * 0.01, 1000)
        duplicates = []

        for entry in recent_data:
            if not entry.get("success"):
                continue

            if not DuplicateHandlers._matches_vendor(vendor, entry):
                continue

            if not DuplicateHandlers._matches_type(invoice_type, entry):
                continue

            entry_amount = float(entry.get("total_amount", 0))
            if abs(total_amount - entry_amount) > amount_tolerance:
                continue

            duplicate = DuplicateHandlers._check_date_match(
                entry, date, entry_amount
            )
            if duplicate:
                duplicates.append(duplicate)

        logger.info(f"Duplicate check result: {len(duplicates)} matches")
        return duplicates

    @staticmethod
    def _matches_vendor(vendor: str, entry: Dict[str, Any]) -> bool:
        """Check if entry vendor matches."""
        entry_vendor = entry.get("vendor", "").strip().lower()
        if vendor and entry_vendor and vendor != entry_vendor:
            return False
        return True

    @staticmethod
    def _matches_type(invoice_type: str, entry: Dict[str, Any]) -> bool:
        """Check if entry type matches."""
        entry_type = entry.get("invoice_type", "").lower()
        if invoice_type and entry_type and invoice_type != entry_type:
            return False
        return True

    @staticmethod
    def _check_date_match(
        entry: Dict[str, Any],
        date: Optional[str],
        entry_amount: float
    ) -> Optional[Dict[str, Any]]:
        """Check date match and return duplicate info if matched."""
        entry_date = entry.get("date", "")
        if not entry_date and entry.get("timestamp"):
            entry_date = entry.get("timestamp", "")[:10]

        duplicate_info = {
            "invoice_id": entry.get("invoice_id"),
            "vendor": entry.get("vendor"),
            "total_amount": entry_amount,
            "invoice_type": entry.get("invoice_type"),
            "timestamp": entry.get("timestamp"),
            "date": entry_date or (entry.get("timestamp", "")[:10] if entry.get("timestamp") else "")
        }

        if date:
            if entry_date and date[:10] == entry_date[:10]:
                logger.info(f"Found duplicate: {entry.get('vendor')} - {entry_amount} - {entry_date}")
                return duplicate_info
            return None
        else:
            logger.info(f"Found duplicate (no date): {entry.get('vendor')} - {entry_amount}")
            return duplicate_info
