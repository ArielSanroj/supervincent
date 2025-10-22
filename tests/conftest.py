#!/usr/bin/env python3
"""
Configuración global de pytest para BetiBot
"""

import pytest
import os
import tempfile
import shutil
from unittest.mock import Mock, patch
from pathlib import Path

# Configurar variables de entorno para tests
os.environ['ALEGRA_EMAIL'] = 'test@example.com'
os.environ['ALEGRA_TOKEN'] = 'test_token'
os.environ['REDIS_HOST'] = 'localhost'
os.environ['REDIS_PORT'] = '6379'
os.environ['REDIS_DB'] = '1'

@pytest.fixture
def mock_alegra():
    """Mock del cliente Alegra"""
    with patch('src.integrations.alegra.client.AlegraClient') as mock:
        mock_instance = Mock()
        mock_instance.get_or_create_contact.return_value = "123"
        mock_instance.get_or_create_item.return_value = "456"
        mock_instance.create_bill.return_value = {"id": "789", "status": "success"}
        mock_instance.create_invoice.return_value = {"id": "101", "status": "success"}
        mock.return_value = mock_instance
        yield mock_instance

@pytest.fixture
def mock_redis():
    """Mock de Redis"""
    with patch('src.utils.cache.redis.Redis') as mock:
        mock_instance = Mock()
        mock_instance.ping.return_value = True
        mock_instance.get.return_value = None
        mock_instance.set.return_value = True
        mock_instance.delete.return_value = True
        mock_instance.exists.return_value = False
        mock_instance.ttl.return_value = -1
        mock_instance.flushdb.return_value = True
        mock_instance.info.return_value = {
            'connected_clients': 1,
            'used_memory_human': '1M',
            'keyspace_hits': 100,
            'keyspace_misses': 10,
            'total_commands_processed': 1000
        }
        mock.return_value = mock_instance
        yield mock_instance

@pytest.fixture
def mock_tesseract():
    """Mock de Tesseract OCR"""
    with patch('pytesseract.image_to_string') as mock:
        mock.return_value = "Mock OCR text"
        yield mock

@pytest.fixture
def mock_pdfplumber():
    """Mock de pdfplumber"""
    with patch('pdfplumber.open') as mock:
        mock_pdf = Mock()
        mock_pdf.pages = [Mock()]
        mock_pdf.pages[0].extract_text.return_value = "Mock PDF text"
        mock.return_value.__enter__.return_value = mock_pdf
        yield mock

@pytest.fixture
def mock_requests():
    """Mock de requests"""
    with patch('requests.Session') as mock:
        mock_session = Mock()
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"success": True}
        mock_session.request.return_value = mock_response
        mock.return_value = mock_session
        yield mock_session

@pytest.fixture
def temp_dir():
    """Directorio temporal para tests"""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)

@pytest.fixture
def sample_pdf():
    """Archivo PDF de muestra para tests"""
    return Path("tests/fixtures/sample_invoice.pdf")

@pytest.fixture
def sample_image():
    """Archivo de imagen de muestra para tests"""
    return Path("tests/fixtures/sample_invoice.jpg")

@pytest.fixture
def sample_config():
    """Configuración de muestra para tests"""
    return {
        "alegra": {
            "email": "test@example.com",
            "token": "test_token",
            "base_url": "https://api.alegra.com/api/v1"
        },
        "parsing": {
            "keywords": {
                "purchase": ["compra", "factura de compra", "bill"],
                "sale": ["venta", "factura de venta", "invoice"]
            }
        },
        "logging": {
            "level": "INFO",
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        }
    }

@pytest.fixture
def sample_invoice_data():
    """Datos de factura de muestra para tests"""
    return {
        "type": "purchase",
        "number": "FAC-001",
        "date": "2025-01-10",
        "total": 100000.0,
        "client": {
            "name": "Cliente Test",
            "identification": "123456789",
            "email": "cliente@test.com"
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

@pytest.fixture
def sample_contact_data():
    """Datos de contacto de muestra para tests"""
    return {
        "name": "Cliente Test",
        "type": "client",
        "identification": "123456789",
        "email": "cliente@test.com",
        "phone": "3001234567",
        "address": "Calle 123 #45-67"
    }

@pytest.fixture
def sample_item_data():
    """Datos de item de muestra para tests"""
    return {
        "name": "Producto Test",
        "price": 100000.0,
        "unit": "unidad",
        "initial_quantity": 1.0,
        "accounting_account": "4-01-01-01-01"
    }

@pytest.fixture
def sample_tax_data():
    """Datos de impuestos de muestra para tests"""
    return {
        "iva_rate": 0.19,
        "rete_fuente_renta": 0.0,
        "rete_fuente_iva": 0.0,
        "rete_fuente_ica": 0.0,
        "rete_iva": 0.0
    }

@pytest.fixture
def mock_feature_flags():
    """Mock de feature flags"""
    with patch('src.utils.feature_flags.feature_flags') as mock:
        mock.is_enabled.return_value = True
        mock.is_experimental.return_value = False
        mock.is_beta.return_value = False
        mock.is_deprecated.return_value = False
        yield mock

@pytest.fixture
def mock_metrics_collector():
    """Mock del recolector de métricas"""
    with patch('src.utils.monitoring.get_metrics_collector') as mock:
        mock_instance = Mock()
        mock_instance.increment_counter.return_value = None
        mock_instance.record_processing_time.return_value = None
        mock_instance.record_api_request.return_value = None
        mock_instance.record_error.return_value = None
        mock.return_value = mock_instance
        yield mock_instance

@pytest.fixture
def mock_structured_logger():
    """Mock del logger estructurado"""
    with patch('src.utils.monitoring.get_structured_logger') as mock:
        mock_instance = Mock()
        mock_instance.info.return_value = None
        mock_instance.error.return_value = None
        mock_instance.warning.return_value = None
        mock_instance.debug.return_value = None
        mock.return_value = mock_instance
        yield mock_instance

@pytest.fixture
def mock_health_checker():
    """Mock del health checker"""
    with patch('src.utils.monitoring.get_health_checker') as mock:
        mock_instance = Mock()
        mock_instance.check_service.return_value = {
            'service': 'test',
            'status': 'healthy',
            'duration': 0.1,
            'timestamp': '2025-01-10T10:00:00Z'
        }
        mock_instance.get_overall_status.return_value = {
            'status': 'healthy',
            'healthy_services': 1,
            'total_services': 1,
            'services': {},
            'timestamp': '2025-01-10T10:00:00Z'
        }
        mock.return_value = mock_instance
        yield mock_instance

@pytest.fixture
def mock_cache_manager():
    """Mock del gestor de caché"""
    with patch('src.utils.cache.CacheManager') as mock:
        mock_instance = Mock()
        mock_instance.get_ocr_result.return_value = None
        mock_instance.set_ocr_result.return_value = True
        mock_instance.get_contact_id.return_value = None
        mock_instance.set_contact_id.return_value = True
        mock_instance.get_item_id.return_value = None
        mock_instance.set_item_id.return_value = True
        mock_instance.clear_all_caches.return_value = True
        mock_instance.get_stats.return_value = {
            'main_cache': {'type': 'redis', 'available': True},
            'ocr_cache': {'type': 'redis', 'available': True},
            'alegra_cache': {'type': 'redis', 'available': True}
        }
        mock.return_value = mock_instance
        yield mock_instance

