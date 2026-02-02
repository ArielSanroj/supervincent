"""
Factory for creating appropriate invoice parsers.
"""

import logging
from typing import Optional

from ..models import InvoiceData
from .base import BaseParser
from .pdf_parser import PDFParser
from .image_parser import ImageParser

logger = logging.getLogger(__name__)


class InvoiceParserFactory:
    """Factory for creating appropriate invoice parsers."""

    _parsers = [
        PDFParser(),
        ImageParser(),
    ]

    @classmethod
    def get_parser(cls, file_path: str) -> Optional[BaseParser]:
        """Get appropriate parser for file type."""
        for parser in cls._parsers:
            if parser.can_parse(file_path):
                return parser

        logger.error(f"No parser available for file: {file_path}")
        return None

    @classmethod
    def parse_invoice(cls, file_path: str) -> Optional[InvoiceData]:
        """Parse invoice using appropriate parser."""
        parser = cls.get_parser(file_path)
        if parser:
            return parser.parse(file_path)
        return None
