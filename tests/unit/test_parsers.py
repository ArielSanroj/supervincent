"""
Unit tests for invoice parsers.
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch

from src.core.parsers import PDFParser, ImageParser, InvoiceParserFactory
from src.core.models import InvoiceType, InvoiceItem


class TestPDFParser:
    """Test PDF parser functionality."""
    
    def test_can_parse_pdf_files(self):
        """Test PDF parser can handle PDF files."""
        parser = PDFParser()
        
        assert parser.can_parse("test.pdf") is True
        assert parser.can_parse("test.PDF") is True
        assert parser.can_parse("test.jpg") is False
        assert parser.can_parse("test.png") is False
    
    def test_detect_invoice_type_purchase(self):
        """Test detection of purchase invoices."""
        parser = PDFParser()
        text = "Factura de compra Proveedor: Test Supplier"
        
        result = parser._detect_invoice_type(text)
        assert result == InvoiceType.PURCHASE
    
    def test_detect_invoice_type_sale(self):
        """Test detection of sale invoices."""
        parser = PDFParser()
        text = "Factura de venta Cliente: Test Customer"
        
        result = parser._detect_invoice_type(text)
        assert result == InvoiceType.SALE
    
    def test_extract_date_formats(self):
        """Test date extraction from various formats."""
        parser = PDFParser()
        
        # Test DD/MM/YYYY format
        text = "Fecha: 15/03/2024"
        result = parser._extract_date(text)
        assert result == "2024-03-15"
        
        # Test DD-MM-YYYY format
        text = "Fecha: 15-03-2024"
        result = parser._extract_date(text)
        assert result == "2024-03-15"
    
    def test_extract_vendor(self):
        """Test vendor extraction."""
        parser = PDFParser()
        text = "Proveedor: Test Supplier S.A.S."
        
        result = parser._extract_vendor(text)
        assert result == "Test Supplier S.A.S."
    
    def test_extract_items(self):
        """Test item extraction."""
        parser = PDFParser()
        text = """
        001 - Producto de prueba
        Cantidad: 2 Unidad
        Precio unit.: $100.000
        """
        
        items = parser._extract_items(text)
        assert len(items) == 1
        assert items[0].code == "001"
        assert "Producto de prueba" in items[0].description
    
    def test_extract_totals(self):
        """Test total extraction."""
        parser = PDFParser()
        text = """
        Subtotal: $200.000
        IVA: $38.000
        Total: $238.000
        """
        
        subtotal, taxes, total = parser._extract_totals(text)
        assert subtotal == 200000.0
        assert taxes == 38000.0
        assert total == 238000.0
    
    @patch('pdfplumber.open')
    def test_parse_pdf_success(self, mock_pdf_open):
        """Test successful PDF parsing."""
        # Mock PDF content
        mock_page = Mock()
        mock_page.extract_text.return_value = """
        Fecha: 15/03/2024
        Proveedor: Test Supplier
        Subtotal: $100.000
        IVA: $19.000
        Total: $119.000
        """
        
        mock_pdf = Mock()
        mock_pdf.pages = [mock_page]
        mock_pdf_open.return_value.__enter__.return_value = mock_pdf
        
        parser = PDFParser()
        result = parser.parse("test.pdf")
        
        assert result is not None
        assert result.date == "2024-03-15"
        assert result.vendor == "Test Supplier"
        assert result.total == 119000.0
    
    @patch('pdfplumber.open')
    def test_parse_pdf_no_text(self, mock_pdf_open):
        """Test PDF parsing with no extractable text."""
        mock_page = Mock()
        mock_page.extract_text.return_value = ""
        
        mock_pdf = Mock()
        mock_pdf.pages = [mock_page]
        mock_pdf_open.return_value.__enter__.return_value = mock_pdf
        
        parser = PDFParser()
        result = parser.parse("test.pdf")
        
        assert result is None


class TestImageParser:
    """Test image parser functionality."""
    
    def test_can_parse_image_files(self):
        """Test image parser can handle image files."""
        parser = ImageParser()
        
        assert parser.can_parse("test.jpg") is True
        assert parser.can_parse("test.jpeg") is True
        assert parser.can_parse("test.png") is True
        assert parser.can_parse("test.pdf") is False
    
    @patch('src.core.parsers.OCR_AVAILABLE', False)
    def test_parse_without_ocr(self):
        """Test parsing when OCR is not available."""
        parser = ImageParser()
        result = parser.parse("test.jpg")
        
        assert result is None


class TestInvoiceParserFactory:
    """Test parser factory functionality."""
    
    def test_get_parser_pdf(self):
        """Test getting PDF parser."""
        parser = InvoiceParserFactory.get_parser("test.pdf")
        assert parser is not None
        assert isinstance(parser, PDFParser)
    
    def test_get_parser_image(self):
        """Test getting image parser."""
        parser = InvoiceParserFactory.get_parser("test.jpg")
        assert parser is not None
        assert isinstance(parser, ImageParser)
    
    def test_get_parser_unsupported(self):
        """Test getting parser for unsupported file type."""
        parser = InvoiceParserFactory.get_parser("test.txt")
        assert parser is None
    
    @patch('src.core.parsers.InvoiceParserFactory.get_parser')
    def test_parse_invoice_success(self, mock_get_parser):
        """Test successful invoice parsing."""
        mock_parser = Mock()
        mock_parser.parse.return_value = Mock()
        mock_get_parser.return_value = mock_parser
        
        result = InvoiceParserFactory.parse_invoice("test.pdf")
        
        assert result is not None
        mock_parser.parse.assert_called_once_with("test.pdf")
    
    def test_parse_invoice_no_parser(self):
        """Test parsing with no available parser."""
        result = InvoiceParserFactory.parse_invoice("test.txt")
        assert result is None
