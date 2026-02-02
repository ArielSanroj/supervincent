"""
PDF invoice parser.
"""

import logging
from typing import Optional

import pdfplumber

from ..models import InvoiceData, InvoiceType
from .base import BaseParser
from .text_extractor import TextExtractor

logger = logging.getLogger(__name__)


class PDFParser(BaseParser):
    """PDF invoice parser."""

    def __init__(self):
        """Initialize PDF parser."""
        self.text_extractor = TextExtractor()

    def can_parse(self, file_path: str) -> bool:
        """Check if file is a PDF."""
        return file_path.lower().endswith('.pdf')

    def parse(self, file_path: str) -> Optional[InvoiceData]:
        """Parse PDF invoice."""
        logger.info(f"Parsing PDF: {file_path}")

        try:
            with pdfplumber.open(file_path) as pdf:
                text = ''
                for page in pdf.pages:
                    text += page.extract_text() or ''

            if not text.strip():
                logger.error("No text extracted from PDF")
                return None

            return self.parse_text(text)

        except Exception as e:
            logger.error(f"Error parsing PDF {file_path}: {e}")
            return None

    def parse_text(self, text: str) -> Optional[InvoiceData]:
        """Parse already-extracted invoice text into structured data."""
        try:
            invoice_type = self.text_extractor.detect_invoice_type(text)
            date = self.text_extractor.extract_date(text)
            vendor = self.text_extractor.extract_vendor(text)
            items = self.text_extractor.extract_items(text)
            subtotal, taxes, total = self.text_extractor.extract_totals(text)

            return InvoiceData(
                invoice_type=invoice_type,
                date=date,
                vendor=vendor,
                client="Cliente desde PDF" if invoice_type == InvoiceType.SALE else vendor,
                items=items,
                subtotal=subtotal,
                taxes=taxes,
                total=total,
                raw_text=text
            )
        except Exception as e:
            logger.error(f"Error parsing text: {e}")
            return None
