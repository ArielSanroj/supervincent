"""
Helper functions for report generation.
"""

import logging
from datetime import datetime
from typing import Dict, List

from ..dependencies import cache_service, RECENT_UPLOADS_KEY
from ..handlers.report_handlers import ReportHandlers

logger = logging.getLogger(__name__)


def generate_local_trial_balance(start_date: str, end_date: str) -> Dict:
    """Generate trial balance from local processed invoices."""
    recent_data = cache_service.get(RECENT_UPLOADS_KEY) or []
    accounts = {}

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
        vendor = entry.get("vendor", "").lower()

        if is_purchase:
            account_code, account_name = ReportHandlers._get_expense_account(vendor)
            _add_to_account(accounts, account_code, account_name, total_amount, is_debit=True)
            _add_to_account(accounts, "220505", "Cuentas por Pagar", total_amount, is_debit=False)
        else:
            _add_to_account(accounts, "413505", "Ingresos Operacionales", total_amount, is_debit=False)
            _add_to_account(accounts, "130505", "Cuentas por Cobrar", total_amount, is_debit=True)

    trial_balance = list(accounts.values())
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


def _add_to_account(
    accounts: Dict,
    account_code: str,
    account_name: str,
    amount: float,
    is_debit: bool
) -> None:
    """Add amount to account in trial balance."""
    if account_code not in accounts:
        accounts[account_code] = {
            "account_code": account_code,
            "account_name": account_name,
            "debit_balance": 0.0,
            "credit_balance": 0.0,
            "total_debit": 0.0,
            "total_credit": 0.0
        }
    if is_debit:
        accounts[account_code]["debit_balance"] += amount
        accounts[account_code]["total_debit"] += amount
    else:
        accounts[account_code]["credit_balance"] += amount
        accounts[account_code]["total_credit"] += amount


def generate_local_aging_report(start_date: str, end_date: str) -> Dict:
    """Generate aging report from local processed invoices."""
    recent_data = cache_service.get(RECENT_UPLOADS_KEY) or []
    receivables_list = []
    payables_list = []
    today = datetime.now().date()

    for entry in recent_data:
        if not entry.get("success"):
            continue

        amount = ReportHandlers._validate_amount(entry)
        if amount is None or amount <= 0:
            continue

        entry_date_str = entry.get("timestamp", "") or entry.get("date", "")
        if not entry_date_str:
            continue

        try:
            entry_date = datetime.fromisoformat(
                entry_date_str.replace('Z', '+00:00')
            ).date()
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
            logger.warning(
                f"Skipping entry with invalid date: {entry.get('invoice_id')} - {e}"
            )
            continue

    receivables = _calculate_aging_buckets(receivables_list)
    payables = _calculate_aging_buckets(payables_list)
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


def _calculate_aging_buckets(entries: List) -> Dict:
    """Calculate aging buckets for entries."""
    total = sum(e.get("amount", 0) for e in entries)
    current = sum(e.get("amount", 0) for e in entries if e.get("days_old", 0) <= 30)
    days_31_60 = sum(
        e.get("amount", 0) for e in entries if 31 <= e.get("days_old", 0) <= 60
    )
    days_61_90 = sum(
        e.get("amount", 0) for e in entries if 61 <= e.get("days_old", 0) <= 90
    )
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
