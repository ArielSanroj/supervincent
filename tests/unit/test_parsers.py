#!/usr/bin/env python3
"""
Tests unitarios para parsers
"""

import pytest
from unittest.mock import Mock, patch
from pathlib import Path

from src.core.parsers.pdf_parser import PDFParser
from src.core.parsers.image_parser import ImageParser
from src.exceptions import ParsingError


class TestPDFParser:
    """Tests para PDFParser"""
    
    def test_init(self):
        """Test inicialización del parser"""
        parser = PDFParser()
        assert parser is not None
    
    def test_parse_invoice_data(self, mock_pdfplumber, sample_pdf):
        """Test parsing de datos de factura"""
        parser = PDFParser()
        
        with patch.object(parser, '_extract_text_from_pdf') as mock_extract:
            mock_extract.return_value = "Factura de compra #FAC-001 Total: $100,000"
            
            result = parser.parse_invoice_data(str(sample_pdf))
            
            assert result is not None
            assert 'type' in result
            assert 'total' in result
    
    def test_extract_text_from_pdf(self, mock_pdfplumber):
        """Test extracción de texto de PDF"""
        parser = PDFParser()
        
        with patch('pdfplumber.open') as mock_open:
            mock_pdf = Mock()
            mock_pdf.pages = [Mock()]
            mock_pdf.pages[0].extract_text.return_value = "Test PDF content"
            mock_open.return_value.__enter__.return_value = mock_pdf
            
            result = parser._extract_text_from_pdf("test.pdf")
            
            assert result == "Test PDF content"
    
    def test_parse_invoice_data_error(self, sample_pdf):
        """Test error en parsing de datos"""
        parser = PDFParser()
        
        with patch.object(parser, '_extract_text_from_pdf', side_effect=Exception("PDF error")):
            with pytest.raises(ParsingError):
                parser.parse_invoice_data(str(sample_pdf))
    
    def test_detect_invoice_type(self):
        """Test detección de tipo de factura"""
        parser = PDFParser()
        
        # Test factura de compra
        purchase_text = "Factura de compra #FAC-001"
        result = parser._detect_invoice_type(purchase_text)
        assert result == "purchase"
        
        # Test factura de venta
        sale_text = "Factura de venta #INV-001"
        result = parser._detect_invoice_type(sale_text)
        assert result == "sale"
        
        # Test tipo desconocido
        unknown_text = "Documento desconocido"
        result = parser._detect_invoice_type(unknown_text)
        assert result == "unknown"


class TestImageParser:
    """Tests para ImageParser"""
    
    def test_init(self):
        """Test inicialización del parser"""
        parser = ImageParser()
        assert parser is not None
    
    def test_parse_invoice_data(self, mock_tesseract, sample_image):
        """Test parsing de datos de factura desde imagen"""
        parser = ImageParser()
        
        with patch.object(parser, '_extract_text_from_image') as mock_extract:
            mock_extract.return_value = "Factura de compra #FAC-001 Total: $100,000"
            
            result = parser.parse_invoice_data(str(sample_image))
            
            assert result is not None
            assert 'type' in result
            assert 'total' in result
    
    def test_extract_text_from_image(self, mock_tesseract):
        """Test extracción de texto de imagen"""
        parser = ImageParser()
        
        with patch('pytesseract.image_to_string') as mock_ocr:
            mock_ocr.return_value = "Test OCR content"
            
            result = parser._extract_text_from_image("test.jpg")
            
            assert result == "Test OCR content"
    
    def test_parse_invoice_data_error(self, sample_image):
        """Test error en parsing de datos desde imagen"""
        parser = ImageParser()
        
        with patch.object(parser, '_extract_text_from_image', side_effect=Exception("OCR error")):
            with pytest.raises(ParsingError):
                parser.parse_invoice_data(str(sample_image))
    
    def test_preprocess_image(self):
        """Test preprocesamiento de imagen"""
        parser = ImageParser()
        
        with patch('cv2.imread') as mock_imread, \
             patch('cv2.cvtColor') as mock_cvtcolor, \
             patch('cv2.threshold') as mock_threshold:
            
            mock_imread.return_value = Mock()
            mock_cvtcolor.return_value = Mock()
            mock_threshold.return_value = (Mock(), Mock())
            
            result = parser._preprocess_image("test.jpg")
            
            assert result is not None
    
    def test_detect_invoice_type(self):
        """Test detección de tipo de factura desde imagen"""
        parser = ImageParser()
        
        # Test factura de compra
        purchase_text = "Factura de compra #FAC-001"
        result = parser._detect_invoice_type(purchase_text)
        assert result == "purchase"
        
        # Test factura de venta
        sale_text = "Factura de venta #INV-001"
        result = parser._detect_invoice_type(sale_text)
        assert result == "sale"
        
        # Test tipo desconocido
        unknown_text = "Documento desconocido"
        result = parser._detect_invoice_type(unknown_text)
        assert result == "unknown"

