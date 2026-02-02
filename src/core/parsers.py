"""
Invoice parsing modules - Compatibility Wrapper.

This module maintains backwards compatibility while delegating to the
refactored parsers package.
"""

# Re-export all components from the parsers package
from .parsers import (
    BaseParser,
    PDFParser,
    ImageParser,
    InvoiceParserFactory
)

# For backwards compatibility
__all__ = [
    "BaseParser",
    "PDFParser",
    "ImageParser",
    "InvoiceParserFactory"
]
