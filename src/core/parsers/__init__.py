"""
Parsers especializados para diferentes tipos de documentos
"""

from .pdf_parser import PDFParser
from .image_parser import ImageParser

__all__ = ['PDFParser', 'ImageParser']

