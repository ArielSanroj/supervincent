#!/usr/bin/env python3
"""
SuperVincent InvoiceBot - Canonical Invoice Processor
Consolidated from 11 versions with best features and modern architecture.
"""

import argparse
import logging
import os
import sys
from pathlib import Path
from typing import Optional

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from dotenv import load_dotenv
from src.core.models import InvoiceData, ProcessingResult
from src.services.invoice_service import InvoiceService
from src.services.tax_service import TaxService
from src.services.alegra_service import AlegraService
from src.core.config import Settings

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/invoicebot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class InvoiceProcessor:
    """Canonical invoice processor with modern architecture."""
    
    def __init__(self, settings: Optional[Settings] = None):
        """Initialize invoice processor with dependency injection."""
        self.settings = settings or Settings()
        
        # Initialize services
        self.tax_service = TaxService()
        self.alegra_service = AlegraService(
            base_url=self.settings.alegra_base_url,
            email=self.settings.alegra_email,
            token=self.settings.alegra_token
        )
        self.invoice_service = InvoiceService(
            tax_service=self.tax_service,
            alegra_service=self.alegra_service
        )
        
        logger.info("🚀 InvoiceProcessor initialized with modern architecture")
    
    def process_invoice(self, file_path: str) -> ProcessingResult:
        """Process invoice file end-to-end."""
        logger.info(f"📄 Processing invoice: {file_path}")
        
        # Validate file exists
        if not Path(file_path).exists():
            logger.error(f"File not found: {file_path}")
            return ProcessingResult(
                success=False,
                invoice_data=None,
                tax_result=None,
                alegra_result=None,
                error_message=f"File not found: {file_path}"
            )
        
        # Process invoice
        result = self.invoice_service.process_invoice(file_path)
        
        if result.success:
            logger.info("✅ Invoice processed successfully")
            self._log_processing_summary(result)
        else:
            logger.error(f"❌ Invoice processing failed: {result.error_message}")
        
        return result
    
    def _log_processing_summary(self, result: ProcessingResult) -> None:
        """Log processing summary."""
        if result.invoice_data:
            logger.info(f"📊 Invoice Type: {result.invoice_data.invoice_type.value}")
            logger.info(f"📅 Date: {result.invoice_data.date}")
            logger.info(f"🏪 Vendor: {result.invoice_data.vendor}")
            logger.info(f"💰 Total: ${result.invoice_data.total:,.2f}")
        
        if result.tax_result:
            logger.info(f"🧾 IVA: ${result.tax_result.iva_amount:,.2f}")
            logger.info(f"💸 Net Amount: ${result.tax_result.net_amount:,.2f}")
            logger.info(f"✅ Compliance: {result.tax_result.compliance_status}")
        
        if result.alegra_result:
            logger.info(f"🔗 Alegra ID: {result.alegra_result.get('id', 'N/A')}")
            logger.info(f"📄 Number: {result.alegra_result.get('number', 'N/A')}")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description='SuperVincent InvoiceBot - Intelligent Invoice Processing'
    )
    parser.add_argument('command', choices=['process', 'report'], 
                       help='Command to execute')
    parser.add_argument('file_path', nargs='?', 
                       help='Path to invoice file (PDF, JPG, PNG)')
    parser.add_argument('--start-date', 
                       help='Start date for reports (YYYY-MM-DD)')
    parser.add_argument('--end-date', 
                       help='End date for reports (YYYY-MM-DD)')
    parser.add_argument('--config', 
                       help='Path to configuration file')
    
    args = parser.parse_args()
    
    try:
        # Load settings
        settings = Settings()
        
        # Initialize processor
        processor = InvoiceProcessor(settings)
        
        if args.command == 'process':
            if not args.file_path:
                print("❌ File path required for processing")
                return 1
            
            # Process invoice
            result = processor.process_invoice(args.file_path)
            
            if result.success:
                print("\n🎉 Invoice processed successfully!")
                print(f"✅ Type: {result.invoice_data.invoice_type.value}")
                print(f"✅ Total: ${result.invoice_data.total:,.2f}")
                if result.alegra_result:
                    print(f"✅ Created in Alegra: {result.alegra_result.get('number', 'N/A')}")
                return 0
        else:
                print(f"\n❌ Processing failed: {result.error_message}")
                return 1
        
        if args.command == 'report':
            if not args.start_date or not args.end_date:
                print("❌ Start and end dates required for reports")
                return 1
            
            # TODO: Implement report generation
            print("📊 Report generation not yet implemented")
            return 0
    
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        print(f"❌ Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())