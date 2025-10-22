#!/usr/bin/env python3
"""
Tests end-to-end para flujo completo de procesamiento
"""

import pytest
from unittest.mock import Mock, patch
from pathlib import Path

from src.core.invoice_processor import InvoiceProcessor
from src.exceptions import ProcessingError


class TestFullWorkflow:
    """Tests E2E para flujo completo"""
    
    def test_process_purchase_invoice_workflow(self, mock_alegra, mock_requests, temp_dir):
        """Test flujo completo de procesamiento de factura de compra"""
        # Crear archivo de prueba
        test_file = temp_dir / "test_invoice.pdf"
        test_file.write_text("Mock PDF content")
        
        # Mock de parsing
        with patch('src.core.parsers.pdf_parser.PDFParser.parse_invoice_data') as mock_parse:
            mock_parse.return_value = {
                "type": "purchase",
                "number": "FAC-001",
                "date": "2025-01-10",
                "total": 100000.0,
                "client": {
                    "name": "Proveedor Test",
                    "identification": "123456789",
                    "email": "proveedor@test.com"
                },
                "items": [
                    {
                        "name": "Producto Test",
                        "quantity": 1.0,
                        "price": 100000.0,
                        "total": 100000.0
                    }
                ]
            }
            
            # Mock de respuestas de Alegra
            mock_response = Mock()
            mock_response.status_code = 201
            mock_response.json.return_value = {"id": "123", "status": "success"}
            mock_requests.return_value.request.return_value = mock_response
            
            # Procesar factura
            processor = InvoiceProcessor()
            result = processor.process_invoice(str(test_file), "purchase")
            
            # Verificar resultado
            assert result is not None
            assert result["type"] == "purchase"
            assert result["total"] == 100000.0
            assert "client_id" in result
            assert "items" in result
    
    def test_process_sale_invoice_workflow(self, mock_alegra, mock_requests, temp_dir):
        """Test flujo completo de procesamiento de factura de venta"""
        # Crear archivo de prueba
        test_file = temp_dir / "test_invoice.pdf"
        test_file.write_text("Mock PDF content")
        
        # Mock de parsing
        with patch('src.core.parsers.pdf_parser.PDFParser.parse_invoice_data') as mock_parse:
            mock_parse.return_value = {
                "type": "sale",
                "number": "INV-001",
                "date": "2025-01-10",
                "total": 119000.0,
                "client": {
                    "name": "Cliente Test",
                    "identification": "987654321",
                    "email": "cliente@test.com"
                },
                "items": [
                    {
                        "name": "Producto Test",
                        "quantity": 1.0,
                        "price": 100000.0,
                        "total": 100000.0
                    }
                ],
                "taxes": {
                    "iva_rate": 0.19,
                    "iva_amount": 19000.0
                }
            }
            
            # Mock de respuestas de Alegra
            mock_response = Mock()
            mock_response.status_code = 201
            mock_response.json.return_value = {"id": "456", "status": "success"}
            mock_requests.return_value.request.return_value = mock_response
            
            # Procesar factura
            processor = InvoiceProcessor()
            result = processor.process_invoice(str(test_file), "sale")
            
            # Verificar resultado
            assert result is not None
            assert result["type"] == "sale"
            assert result["total"] == 119000.0
            assert "client_id" in result
            assert "items" in result
            assert "taxes" in result
    
    def test_process_image_invoice_workflow(self, mock_alegra, mock_requests, temp_dir):
        """Test flujo completo de procesamiento de factura desde imagen"""
        # Crear archivo de prueba
        test_file = temp_dir / "test_invoice.jpg"
        test_file.write_text("Mock image content")
        
        # Mock de OCR
        with patch('src.core.parsers.image_parser.ImageParser.parse_invoice_data') as mock_parse:
            mock_parse.return_value = {
                "type": "purchase",
                "number": "FAC-002",
                "date": "2025-01-10",
                "total": 200000.0,
                "client": {
                    "name": "Proveedor Imagen",
                    "identification": "111222333",
                    "email": "proveedor@imagen.com"
                },
                "items": [
                    {
                        "name": "Producto Imagen",
                        "quantity": 2.0,
                        "price": 100000.0,
                        "total": 200000.0
                    }
                ]
            }
            
            # Mock de respuestas de Alegra
            mock_response = Mock()
            mock_response.status_code = 201
            mock_response.json.return_value = {"id": "789", "status": "success"}
            mock_requests.return_value.request.return_value = mock_response
            
            # Procesar factura
            processor = InvoiceProcessor()
            result = processor.process_invoice(str(test_file), "auto")
            
            # Verificar resultado
            assert result is not None
            assert result["type"] == "purchase"
            assert result["total"] == 200000.0
            assert "client_id" in result
            assert "items" in result
    
    def test_error_handling_workflow(self, mock_alegra, mock_requests, temp_dir):
        """Test manejo de errores en flujo completo"""
        # Crear archivo de prueba
        test_file = temp_dir / "test_invoice.pdf"
        test_file.write_text("Mock PDF content")
        
        # Mock de error en parsing
        with patch('src.core.parsers.pdf_parser.PDFParser.parse_invoice_data') as mock_parse:
            mock_parse.side_effect = Exception("Parsing error")
            
            # Procesar factura
            processor = InvoiceProcessor()
            
            with pytest.raises(ProcessingError):
                processor.process_invoice(str(test_file), "purchase")
    
    def test_alegra_api_error_workflow(self, mock_alegra, mock_requests, temp_dir):
        """Test manejo de errores de API de Alegra"""
        # Crear archivo de prueba
        test_file = temp_dir / "test_invoice.pdf"
        test_file.write_text("Mock PDF content")
        
        # Mock de parsing exitoso
        with patch('src.core.parsers.pdf_parser.PDFParser.parse_invoice_data') as mock_parse:
            mock_parse.return_value = {
                "type": "purchase",
                "number": "FAC-003",
                "date": "2025-01-10",
                "total": 100000.0,
                "client": {
                    "name": "Proveedor Error",
                    "identification": "999888777",
                    "email": "proveedor@error.com"
                },
                "items": [
                    {
                        "name": "Producto Error",
                        "quantity": 1.0,
                        "price": 100000.0,
                        "total": 100000.0
                    }
                ]
            }
            
            # Mock de error en Alegra
            mock_response = Mock()
            mock_response.status_code = 500
            mock_response.text = "Internal Server Error"
            mock_requests.return_value.request.return_value = mock_response
            
            # Procesar factura
            processor = InvoiceProcessor()
            
            with pytest.raises(ProcessingError):
                processor.process_invoice(str(test_file), "purchase")
    
    def test_circuit_breaker_workflow(self, mock_alegra, mock_requests, temp_dir):
        """Test circuit breaker en flujo completo"""
        # Crear archivo de prueba
        test_file = temp_dir / "test_invoice.pdf"
        test_file.write_text("Mock PDF content")
        
        # Mock de parsing exitoso
        with patch('src.core.parsers.pdf_parser.PDFParser.parse_invoice_data') as mock_parse:
            mock_parse.return_value = {
                "type": "purchase",
                "number": "FAC-004",
                "date": "2025-01-10",
                "total": 100000.0,
                "client": {
                    "name": "Proveedor Circuit",
                    "identification": "555666777",
                    "email": "proveedor@circuit.com"
                },
                "items": [
                    {
                        "name": "Producto Circuit",
                        "quantity": 1.0,
                        "price": 100000.0,
                        "total": 100000.0
                    }
                ]
            }
            
            # Mock de múltiples errores para activar circuit breaker
            mock_response = Mock()
            mock_response.status_code = 500
            mock_response.text = "Internal Server Error"
            mock_requests.return_value.request.return_value = mock_response
            
            # Procesar factura múltiples veces
            processor = InvoiceProcessor()
            
            # Simular múltiples fallos
            for _ in range(6):  # Más que el threshold
                try:
                    processor.process_invoice(str(test_file), "purchase")
                except ProcessingError:
                    pass
            
            # Verificar que el circuit breaker está abierto
            assert processor.alegra_client.circuit_state.value == "open"
    
    def test_cache_workflow(self, mock_alegra, mock_requests, temp_dir):
        """Test caché en flujo completo"""
        # Crear archivo de prueba
        test_file = temp_dir / "test_invoice.pdf"
        test_file.write_text("Mock PDF content")
        
        # Mock de parsing exitoso
        with patch('src.core.parsers.pdf_parser.PDFParser.parse_invoice_data') as mock_parse:
            mock_parse.return_value = {
                "type": "purchase",
                "number": "FAC-005",
                "date": "2025-01-10",
                "total": 100000.0,
                "client": {
                    "name": "Proveedor Cache",
                    "identification": "333444555",
                    "email": "proveedor@cache.com"
                },
                "items": [
                    {
                        "name": "Producto Cache",
                        "quantity": 1.0,
                        "price": 100000.0,
                        "total": 100000.0
                    }
                ]
            }
            
            # Mock de respuestas de Alegra
            mock_response = Mock()
            mock_response.status_code = 201
            mock_response.json.return_value = {"id": "999", "status": "success"}
            mock_requests.return_value.request.return_value = mock_response
            
            # Procesar factura
            processor = InvoiceProcessor()
            result1 = processor.process_invoice(str(test_file), "purchase")
            
            # Procesar la misma factura nuevamente (debería usar caché)
            result2 = processor.process_invoice(str(test_file), "purchase")
            
            # Verificar que ambos resultados son iguales
            assert result1 == result2
            
            # Verificar que se usó caché (menos llamadas a la API)
            assert mock_requests.return_value.request.call_count < 4  # Sin caché serían 4 llamadas

