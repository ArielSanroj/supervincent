"""
Financial reports routes.
"""

import logging
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException

from ..dependencies import cache_service, RECENT_UPLOADS_KEY
from ..handlers.report_handlers import ReportHandlers
from .reports_helpers import (
    generate_local_trial_balance,
    generate_local_aging_report
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/reports", tags=["Financial Reports"])


@router.get("/general-ledger")
async def get_general_ledger(
    start_date: str,
    end_date: str,
    account_id: Optional[str] = None
):
    """Get general ledger report."""
    try:
        try:
            from alegra_reports import AlegraReports
            reporter = AlegraReports()
            result = reporter.generate_ledger_report(
                start_date, end_date, 'general-ledger', account_id
            )
            return {
                "status": "success",
                "report_type": "general-ledger",
                "period": {"start": start_date, "end": end_date},
                "data": result,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as alegra_error:
            logger.warning(
                f"Alegra report failed: {alegra_error}, using local processed invoices"
            )
            ledger_entries = ReportHandlers.generate_local_ledger(start_date, end_date)
            return {
                "status": "success",
                "report_type": "general-ledger",
                "period": {"start": start_date, "end": end_date},
                "data": ledger_entries,
                "source": "local",
                "timestamp": datetime.now().isoformat()
            }
    except Exception as e:
        logger.error(f"Error getting general ledger: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/trial-balance")
async def get_trial_balance(start_date: str, end_date: str):
    """Get trial balance report."""
    try:
        try:
            from alegra_reports import AlegraReports
            reporter = AlegraReports()
            result = reporter.generate_ledger_report(start_date, end_date, 'trial-balance')
            return {
                "status": "success",
                "report_type": "trial-balance",
                "period": {"start": start_date, "end": end_date},
                "data": result,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as alegra_error:
            logger.warning(f"Alegra trial balance failed: {alegra_error}, using local data")
            return generate_local_trial_balance(start_date, end_date)
    except Exception as e:
        logger.error(f"Error getting trial balance: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/journal")
async def get_journal_entries(start_date: str, end_date: str):
    """Get journal entries report."""
    try:
        from alegra_reports import AlegraReports
        reporter = AlegraReports()
        result = reporter.generate_ledger_report(start_date, end_date, 'journal')
        return {
            "status": "success",
            "report_type": "journal",
            "period": {"start": start_date, "end": end_date},
            "data": result,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting journal entries: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/aging")
async def get_aging_report(start_date: str, end_date: str):
    """Get aging report for accounts receivable and payable."""
    try:
        try:
            from alegra_reports import AlegraReports
            reporter = AlegraReports()
            result = reporter.generate_aging_report(start_date, end_date)
            return {
                "status": "success",
                "report_type": "aging",
                "period": {"start": start_date, "end": end_date},
                "data": result,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as alegra_error:
            logger.warning(f"Alegra aging report failed: {alegra_error}, using local data")
            return generate_local_aging_report(start_date, end_date)
    except Exception as e:
        logger.error(f"Error getting aging report: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/cash-flow")
async def get_cash_flow_report(start_date: str, end_date: str):
    """Get cash flow report."""
    try:
        from alegra_reports import AlegraReports
        reporter = AlegraReports()
        result = reporter.generate_cash_flow_report(start_date, end_date)
        return {
            "status": "success",
            "report_type": "cash-flow",
            "period": {"start": start_date, "end": end_date},
            "data": result,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting cash flow report: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/processed/recent")
async def get_recent_processed():
    """Return recently processed invoices (last 50)."""
    try:
        data = cache_service.get(RECENT_UPLOADS_KEY) or []
        return {
            "status": "success",
            "count": len(data),
            "data": data,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting recent processed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
