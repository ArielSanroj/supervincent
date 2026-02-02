"""
Main Financial Analyzer class - orchestrates all analysis components.
"""

import os
import logging
from typing import Dict

from .data_loader import FinancialDataLoader
from .metrics_calculator import MetricsCalculator
from .report_generator import ReportGenerator
from .chart_generator import ChartGenerator
from .email_sender import EmailSender
from .constants import DEFAULT_BUDGET, DEFAULT_EMAIL_CONFIG

logger = logging.getLogger(__name__)


class FinancialAnalyzer:
    """Main orchestrator for financial analysis."""

    def __init__(self, downloads_dir: str = None):
        self.downloads_dir = downloads_dir or os.path.expanduser("~/Downloads")
        self.reports_dir = os.path.join(self.downloads_dir, "superbincent_reports")

        self.data_loader = FinancialDataLoader(self.downloads_dir)
        self.metrics_calculator = MetricsCalculator(DEFAULT_BUDGET)
        self.report_generator = ReportGenerator(self.reports_dir, DEFAULT_BUDGET)
        self.chart_generator = ChartGenerator(self.reports_dir, DEFAULT_BUDGET)
        self.email_sender = EmailSender(DEFAULT_EMAIL_CONFIG)

        self.consolidated_data = {}

        logger.info("Financial analyzer initialized")

    def run_full_analysis(self) -> Dict:
        """Execute complete financial analysis."""
        try:
            logger.info("Starting full financial analysis")

            file_path = self.data_loader.detect_latest_file()
            if not file_path:
                raise ValueError("No financial file found")

            self.consolidated_data = self.data_loader.load_data(file_path)
            metrics = self.metrics_calculator.calculate_metrics(self.consolidated_data)
            reports = self.report_generator.generate_all_reports(metrics, self.consolidated_data)
            chart_files = self.chart_generator.generate_all_charts(metrics, self.consolidated_data)

            if chart_files:
                reports['graficos'] = chart_files

            email_sent = self.email_sender.send_report(reports, metrics)

            result = {
                'status': 'success',
                'metrics': metrics,
                'reports': reports,
                'email_sent': email_sent,
                'files_generated': len([f for f in reports.values() if f and (isinstance(f, str) and os.path.exists(f))])
            }

            logger.info(f"Analysis complete - {result['files_generated']} files generated")
            return result

        except Exception as e:
            logger.error(f"Error in full analysis: {e}")
            return {'status': 'error', 'error': str(e)}

    def update_from_entry(self, invoice_data: Dict) -> Dict:
        """Update financial analysis from invoice entry."""
        try:
            logger.info("Updating financial analysis from invoice entry")

            file_path = self.data_loader.detect_latest_file()
            if not file_path:
                logger.warning("No financial file found for update")
                return {}

            self.consolidated_data = self.data_loader.load_data(file_path)
            metrics = self.metrics_calculator.calculate_metrics(self.consolidated_data)
            reports = self.report_generator.generate_all_reports(metrics, self.consolidated_data)

            logger.info("Financial analysis updated successfully")
            return {
                'metrics': metrics,
                'reports': reports,
                'status': 'success'
            }

        except Exception as e:
            logger.error(f"Error updating financial analysis: {e}")
            return {'status': 'error', 'error': str(e)}


def main():
    """Main function to run financial analysis."""
    print("SuperBincent - Financial Analysis")
    print("=" * 50)

    analyzer = FinancialAnalyzer()
    result = analyzer.run_full_analysis()

    if result['status'] == 'success':
        print("Financial analysis completed successfully")
        print(f"Metrics calculated for {result['metrics']['current_month']}")
        print(f"{result['files_generated']} files generated")
        print(f"Email sent: {'Yes' if result['email_sent'] else 'No'}")
    else:
        print(f"Error in analysis: {result['error']}")


if __name__ == "__main__":
    main()
