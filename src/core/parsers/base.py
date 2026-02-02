"""
Base parser interface for invoice parsers.
"""

from abc import ABC, abstractmethod
from typing import Optional

from ..models import InvoiceData


class BaseParser(ABC):
    """Abstract base class for invoice parsers."""

    @abstractmethod
    def parse(self, file_path: str) -> Optional[InvoiceData]:
        """Parse invoice file and return structured data."""
        pass

    @abstractmethod
    def can_parse(self, file_path: str) -> bool:
        """Check if parser can handle the file type."""
        pass
