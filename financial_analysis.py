#!/usr/bin/env python3
"""
Financial Analysis Module for SuperBincent - Compatibility Wrapper.

This module maintains backwards compatibility while delegating to the
refactored financial_analysis package.
"""

# Re-export all components from the package
from financial_analysis import (
    FinancialAnalyzer,
    FinancialDataLoader,
    MetricsCalculator,
    ReportGenerator,
    ChartGenerator,
    EmailSender
)
from financial_analysis.analyzer import main

# For backwards compatibility, export FinancialAnalyzer at module level
__all__ = [
    "FinancialAnalyzer",
    "FinancialDataLoader",
    "MetricsCalculator",
    "ReportGenerator",
    "ChartGenerator",
    "EmailSender",
    "main"
]

if __name__ == "__main__":
    main()
