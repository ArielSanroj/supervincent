"""
Integration tests for complete invoice processing flow.
"""

import pytest
import tempfile
import os
from unittest.mock import Mock, patch
from pathlib import Path

from src.core.models import InvoiceData, InvoiceType, InvoiceItem
from src.services.invoice_service import InvoiceService
from src.services.tax_service import TaxService
from src.services.alegra_service import AlegraService
from src.core.security import SecurityMiddleware, InputValidator, RateLimiter


class TestInvoiceProcessingFlow:
    """Test complete invoice processing flow."""
    
    @pytest.fixture
    def sample_invoice_data(self):
        """Sample invoice data for testing."""
        return InvoiceData(
            invoice_type=InvoiceType.COMPRA,
            date="2025-01-10",
            vendor="ROYAL CANIN COLOMBIA S.A.S.",
            client="Cliente Test",
            items=[
                InvoiceItem(
                    code="1",
                    description="ROYAL CANIN GATO GASTROINTESTINAL FIBRE x2KG",
                    quantity=1.0,
                    price=203343.81
                )
            ],
            subtotal=203343.81,
            taxes=10167.19,
            total=213511.00,
            vendor_nit="52147745-1",
            vendor_regime="comun",
            vendor_city="bogota",
            buyer_nit="1136886917",
            buyer_regime="comun",
            buyer_city="bogota",
            invoice_number="21488"
        )
    
    @pytest.fixture
    def mock_tax_service(self):
        """Mock tax service."""
        tax_service = Mock(spec=TaxService)
        tax_service.calculate_taxes.return_value = Mock(
            iva_amount=10167.19,
            iva_rate=0.05,
            retefuente_renta=0.0,
            retefuente_iva=0.0,
            retefuente_ica=0.0,
            total_withholdings=0.0,
            net_amount=213511.00,
            compliance_status="COMPLIANT"
        )
        return tax_service
    
    @pytest.fixture
    def mock_alegra_service(self):
        """Mock Alegra service."""
        alegra_service = Mock(spec=AlegraService)
        alegra_service.create_purchase_bill.return_value = {
            "id": "bill_123",
            "status": "created",
            "total": 213511.00
        }
        return alegra_service
    
    def test_complete_invoice_processing(self, sample_invoice_data, mock_tax_service, mock_alegra_service):
        """Test complete invoice processing flow."""
        # Create invoice service with mocked dependencies
        invoice_service = InvoiceService(mock_tax_service, mock_alegra_service)
        
        # Mock the parser to return our sample data
        with patch('src.services.invoice_service.InvoiceParserFactory') as mock_parser:
            mock_parser.parse_invoice.return_value = sample_invoice_data
            
            # Process invoice
            result = invoice_service.process_invoice("/test/invoice.pdf")
            
            # Verify result
            assert result.success is True
            assert result.invoice_data == sample_invoice_data
            assert result.tax_result is not None
            assert result.alegra_result is not None
            assert result.alegra_result["id"] == "bill_123"
            
            # Verify service calls
            mock_tax_service.calculate_taxes.assert_called_once_with(sample_invoice_data)
            mock_alegra_service.create_purchase_bill.assert_called_once()
    
    def test_invoice_processing_with_errors(self, mock_tax_service, mock_alegra_service):
        """Test invoice processing with errors."""
        invoice_service = InvoiceService(mock_tax_service, mock_alegra_service)
        
        # Mock parser to return None (parsing error)
        with patch('src.services.invoice_service.InvoiceParserFactory') as mock_parser:
            mock_parser.parse_invoice.return_value = None
            
            # Process invoice
            result = invoice_service.process_invoice("/test/invoice.pdf")
            
            # Verify error handling
            assert result.success is False
            assert result.invoice_data is None
            assert result.error_message == "Failed to parse invoice"
            
            # Verify services were not called
            mock_tax_service.calculate_taxes.assert_not_called()
            mock_alegra_service.create_purchase_bill.assert_not_called()
    
    def test_tax_calculation_integration(self, sample_invoice_data):
        """Test tax calculation integration."""
        tax_service = TaxService()
        
        # Calculate taxes
        tax_result = tax_service.calculate_taxes(sample_invoice_data)
        
        # Verify tax calculation
        assert tax_result.iva_amount == pytest.approx(10167.19, rel=1e-2)
        assert tax_result.iva_rate == pytest.approx(0.05)
        assert tax_result.compliance_status == "COMPLIANT"
    
    @patch('requests.post')
    def test_alegra_integration(self, mock_post, sample_invoice_data):
        """Test Alegra API integration."""
        # Mock successful API response
        mock_response = Mock()
        mock_response.json.return_value = {
            "id": "bill_123",
            "status": "created",
            "total": 213511.00
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response
        
        # Create Alegra service
        alegra_service = AlegraService(
            base_url="https://api.alegra.com/api/v1",
            email="test@example.com",
            token="test_token"
        )
        
        # Create purchase bill
        result = alegra_service.create_purchase_bill(sample_invoice_data, Mock())
        
        # Verify API call
        assert result is not None
        assert result["id"] == "bill_123"
        mock_post.assert_called_once()
    
    def test_security_middleware_integration(self):
        """Test security middleware integration."""
        # Create temporary file for testing
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
            tmp.write(b'test content')
            tmp_path = tmp.name
        
        try:
            # Mock rate limiter and validator
            mock_rate_limiter = Mock()
            mock_rate_limiter.is_allowed.return_value = (True, {"limit": 100, "remaining": 99})
            
            mock_validator = Mock()
            mock_validator.validate_file_path.return_value = Path(tmp_path)
            
            # Create security middleware
            middleware = SecurityMiddleware(mock_rate_limiter, mock_validator)
            
            # Validate request
            result = middleware.validate_request(tmp_path, "user123")
            
            # Verify validation
            assert result["validated"] is True
            assert result["file_path"] == tmp_path
            assert "rate_info" in result
            
            # Verify method calls
            mock_rate_limiter.is_allowed.assert_called_once_with("rate_limit:user123")
            mock_validator.validate_file_path.assert_called_once_with(tmp_path)
            
        finally:
            os.unlink(tmp_path)
    
    def test_error_handling_flow(self, mock_tax_service, mock_alegra_service):
        """Test error handling throughout the flow."""
        invoice_service = InvoiceService(mock_tax_service, mock_alegra_service)
        
        # Mock parser to raise exception
        with patch('src.services.invoice_service.InvoiceParserFactory') as mock_parser:
            mock_parser.parse_invoice.side_effect = Exception("Parsing error")
            
            # Process invoice
            result = invoice_service.process_invoice("/test/invoice.pdf")
            
            # Verify error handling
            assert result.success is False
            assert result.error_message == "Parsing error"
    
    def test_concurrent_processing(self, sample_invoice_data, mock_tax_service, mock_alegra_service):
        """Test concurrent invoice processing."""
        import asyncio
        from src.services.async_service import AsyncInvoiceProcessor
        
        # Create async processor
        async_processor = AsyncInvoiceProcessor(mock_tax_service, mock_alegra_service)
        
        # Mock parser
        with patch('src.services.async_service.InvoiceParserFactory') as mock_parser:
            mock_parser.parse_invoice.return_value = sample_invoice_data
            
            # Test concurrent processing
            async def test_concurrent():
                file_paths = ["/test/invoice1.pdf", "/test/invoice2.pdf"]
                results = await async_processor.process_batch_async(file_paths)
                
                assert len(results) == 2
                assert all(result.success for result in results)
            
            # Run async test
            asyncio.run(test_concurrent())
    
    def test_caching_integration(self, sample_invoice_data):
        """Test caching integration."""
        from src.services.cache_service import CacheService, InvoiceCacheService
        
        # Mock Redis client
        with patch('redis.Redis') as mock_redis:
            mock_redis_client = Mock()
            mock_redis_client.ping.return_value = True
            mock_redis_client.get.return_value = None
            mock_redis_client.setex.return_value = True
            mock_redis.return_value = mock_redis_client
            
            # Create cache service
            cache_service = CacheService()
            invoice_cache = InvoiceCacheService(cache_service)
            
            # Test caching
            file_path = "/test/invoice.pdf"
            invoice_cache.cache_invoice_data(file_path, sample_invoice_data)
            
            # Verify cache operations
            mock_redis_client.setex.assert_called()
    
    def test_end_to_end_processing(self, sample_invoice_data):
        """Test complete end-to-end processing."""
        # This would test the complete flow from file upload to Alegra creation
        # For now, we'll test the main components
        
        # Test data validation
        assert sample_invoice_data.invoice_type == InvoiceType.COMPRA
        assert sample_invoice_data.total == 213511.00
        assert len(sample_invoice_data.items) == 1
        
        # Test tax calculation
        tax_service = TaxService()
        tax_result = tax_service.calculate_taxes(sample_invoice_data)
        assert tax_result.compliance_status == "COMPLIANT"
        
        # Test data serialization
        invoice_dict = sample_invoice_data.to_dict()
        assert invoice_dict["invoice_type"] == "compra"
        assert invoice_dict["total"] == 213511.00

