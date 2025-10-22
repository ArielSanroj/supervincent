"""
InvoiceBot - Sistema de procesamiento de facturas
Versión consolidada y optimizada
"""

__version__ = "2.0.0"
__author__ = "InvoiceBot Team"
__description__ = "Sistema de procesamiento de facturas con integración Alegra"

from .core import InvoiceProcessor
from .utils import ConfigManager, StructuredLogger

__all__ = [
    'InvoiceProcessor',
    'ConfigManager', 
    'StructuredLogger'
]

