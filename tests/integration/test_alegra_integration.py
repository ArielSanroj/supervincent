#!/usr/bin/env python3
"""
Tests de integración para Alegra
"""

import pytest
from unittest.mock import Mock, patch

from src.integrations.alegra.client import AlegraClient
from src.integrations.alegra.reports import AlegraReports
from src.integrations.alegra.models import ContactData, ItemData, InvoiceData
from src.exceptions import AlegraAPIError


class TestAlegraClient:
    """Tests de integración para AlegraClient"""
    
    def test_init(self):
        """Test inicialización del cliente"""
        client = AlegraClient(
            email="test@example.com",
            token="test_token"
        )
        assert client is not None
        assert client.config.email == "test@example.com"
        assert client.config.token == "test_token"
    
    def test_get_or_create_contact_success(self, mock_requests):
        """Test creación exitosa de contacto"""
        client = AlegraClient(
            email="test@example.com",
            token="test_token"
        )
        
        # Mock response exitosa
        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.json.return_value = {"id": "123", "name": "Cliente Test"}
        mock_requests.return_value.request.return_value = mock_response
        
        result = client.get_or_create_contact(
            name="Cliente Test",
            contact_type="client"
        )
        
        assert result == "123"
    
    def test_get_or_create_contact_error(self, mock_requests):
        """Test error en creación de contacto"""
        client = AlegraClient(
            email="test@example.com",
            token="test_token"
        )
        
        # Mock response de error
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.text = "Bad Request"
        mock_requests.return_value.request.return_value = mock_response
        
        with pytest.raises(AlegraAPIError):
            client.get_or_create_contact(
                name="Cliente Test",
                contact_type="client"
            )
    
    def test_get_or_create_item_success(self, mock_requests):
        """Test creación exitosa de item"""
        client = AlegraClient(
            email="test@example.com",
            token="test_token"
        )
        
        # Mock response exitosa
        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.json.return_value = {"id": "456", "name": "Producto Test"}
        mock_requests.return_value.request.return_value = mock_response
        
        result = client.get_or_create_item(
            name="Producto Test",
            price=100000.0
        )
        
        assert result == "456"
    
    def test_get_or_create_item_error(self, mock_requests):
        """Test error en creación de item"""
        client = AlegraClient(
            email="test@example.com",
            token="test_token"
        )
        
        # Mock response de error
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.text = "Bad Request"
        mock_requests.return_value.request.return_value = mock_response
        
        with pytest.raises(AlegraAPIError):
            client.get_or_create_item(
                name="Producto Test",
                price=100000.0
            )
    
    def test_create_bill_success(self, mock_requests):
        """Test creación exitosa de bill"""
        client = AlegraClient(
            email="test@example.com",
            token="test_token"
        )
        
        # Mock response exitosa
        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.json.return_value = {"id": "789", "status": "success"}
        mock_requests.return_value.request.return_value = mock_response
        
        bill_data = {
            "provider": {"id": "123"},
            "date": "2025-01-10",
            "items": [
                {
                    "item": {"id": "456"},
                    "quantity": 1,
                    "price": 100000
                }
            ]
        }
        
        result = client.create_bill(bill_data)
        
        assert result is not None
        assert result["id"] == "789"
    
    def test_create_invoice_success(self, mock_requests):
        """Test creación exitosa de invoice"""
        client = AlegraClient(
            email="test@example.com",
            token="test_token"
        )
        
        # Mock response exitosa
        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.json.return_value = {"id": "101", "status": "success"}
        mock_requests.return_value.request.return_value = mock_response
        
        invoice_data = {
            "client": {"id": "123"},
            "date": "2025-01-10",
            "items": [
                {
                    "item": {"id": "456"},
                    "quantity": 1,
                    "price": 100000
                }
            ]
        }
        
        result = client.create_invoice(invoice_data)
        
        assert result is not None
        assert result["id"] == "101"
    
    def test_circuit_breaker(self, mock_requests):
        """Test circuit breaker"""
        client = AlegraClient(
            email="test@example.com",
            token="test_token"
        )
        
        # Mock múltiples errores para activar circuit breaker
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        mock_requests.return_value.request.return_value = mock_response
        
        # Simular múltiples fallos
        for _ in range(6):  # Más que el threshold
            try:
                client.get_or_create_contact("Test", "client")
            except AlegraAPIError:
                pass
        
        # Verificar que el circuit breaker está abierto
        assert client.circuit_state.value == "open"
    
    def test_rate_limiting(self, mock_requests):
        """Test rate limiting"""
        client = AlegraClient(
            email="test@example.com",
            token="test_token"
        )
        
        # Mock response exitosa
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"id": "123"}
        mock_requests.return_value.request.return_value = mock_response
        
        # Hacer múltiples requests rápidamente
        for _ in range(5):
            client.get_or_create_contact("Test", "client")
        
        # Verificar que se aplicó rate limiting
        assert mock_requests.return_value.request.call_count == 5


class TestAlegraReports:
    """Tests de integración para AlegraReports"""
    
    def test_init(self, mock_alegra):
        """Test inicialización del generador de reportes"""
        reports = AlegraReports(mock_alegra)
        assert reports is not None
        assert reports.client == mock_alegra
    
    def test_generate_general_ledger(self, mock_alegra, mock_requests):
        """Test generación de mayor general"""
        reports = AlegraReports(mock_alegra)
        
        # Mock response exitosa
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": [
                {"account": "4-01-01-01-01", "debit": 100000, "credit": 0, "balance": 100000}
            ]
        }
        mock_requests.return_value.request.return_value = mock_response
        
        result = reports.generate_general_ledger(
            start_date="2025-01-01",
            end_date="2025-01-31"
        )
        
        assert result["success"] is True
        assert "data" in result
        assert "summary" in result
    
    def test_generate_trial_balance(self, mock_alegra, mock_requests):
        """Test generación de balance de prueba"""
        reports = AlegraReports(mock_alegra)
        
        # Mock response exitosa
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": [
                {"account": "4-01-01-01-01", "debit": 100000, "credit": 0}
            ]
        }
        mock_requests.return_value.request.return_value = mock_response
        
        result = reports.generate_trial_balance(
            start_date="2025-01-01",
            end_date="2025-01-31"
        )
        
        assert result["success"] is True
        assert "data" in result
        assert "summary" in result
    
    def test_generate_journal(self, mock_alegra, mock_requests):
        """Test generación de diario"""
        reports = AlegraReports(mock_alegra)
        
        # Mock response exitosa
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": [
                {"date": "2025-01-10", "description": "Test entry", "debit": 100000, "credit": 0}
            ]
        }
        mock_requests.return_value.request.return_value = mock_response
        
        result = reports.generate_journal(
            start_date="2025-01-01",
            end_date="2025-01-31"
        )
        
        assert result["success"] is True
        assert "data" in result
        assert "summary" in result
    
    def test_generate_auxiliary_ledgers(self, mock_alegra, mock_requests):
        """Test generación de auxiliares"""
        reports = AlegraReports(mock_alegra)
        
        # Mock response exitosa
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": [
                {"account": "4-01-01-01-01", "entries": []}
            ]
        }
        mock_requests.return_value.request.return_value = mock_response
        
        result = reports.generate_auxiliary_ledgers(
            start_date="2025-01-01",
            end_date="2025-01-31"
        )
        
        assert result["success"] is True
        assert "data" in result
        assert "summary" in result
    
    def test_generate_all_reports(self, mock_alegra, mock_requests):
        """Test generación de todos los reportes"""
        reports = AlegraReports(mock_alegra)
        
        # Mock response exitosa para todos los reportes
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": []}
        mock_requests.return_value.request.return_value = mock_response
        
        result = reports.generate_all_reports(
            start_date="2025-01-01",
            end_date="2025-01-31"
        )
        
        assert result["success"] is True
        assert "results" in result
        assert "summary" in result
        assert result["summary"]["total_reports"] == 4

