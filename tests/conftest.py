"""
Pytest configuration and shared fixtures for SuperVincent InvoiceBot tests.
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path
from typing import Dict, Any, Generator
from unittest.mock import Mock, patch

import pytest
from dotenv import load_dotenv

# Add src to Python path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Load test environment variables
load_dotenv(".env.test", override=True)


@pytest.fixture(scope="session")
def test_data_dir() -> Path:
    """Directory containing test data files."""
    return Path(__file__).parent / "fixtures"


@pytest.fixture(scope="session")
def sample_invoices_dir() -> Path:
    """Directory containing sample invoice files."""
    return Path(__file__).parent / "fixtures" / "sample_invoices"


@pytest.fixture(scope="session")
def mock_responses_dir() -> Path:
    """Directory containing mock API responses."""
    return Path(__file__).parent / "fixtures" / "mock_responses"


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for test files."""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    shutil.rmtree(temp_path, ignore_errors=True)


@pytest.fixture
def mock_env_vars() -> Dict[str, str]:
    """Mock environment variables for testing."""
    return {
        "ALEGRA_USER": "test@example.com",
        "ALEGRA_TOKEN": "test_token_123",
        "ALEGRA_BASE_URL": "https://api.alegra.com/api/v1",
        "LOG_LEVEL": "DEBUG",
        "REDIS_URL": "redis://localhost:6379/0",
    }


@pytest.fixture
def mock_alegra_credentials(mock_env_vars: Dict[str, str]) -> None:
    """Mock Alegra API credentials."""
    with patch.dict(os.environ, mock_env_vars):
        yield


@pytest.fixture
def mock_alegra_api() -> Mock:
    """Mock Alegra API responses."""
    mock_api = Mock()
    
    # Mock successful contact creation
    mock_api.post.return_value.status_code = 201
    mock_api.post.return_value.json.return_value = {
        "id": "123",
        "name": "Test Contact",
        "type": "client"
    }
    
    # Mock successful item creation
    mock_api.post.return_value.status_code = 201
    mock_api.post.return_value.json.return_value = {
        "id": "456",
        "name": "Test Item",
        "price": 100.0
    }
    
    # Mock successful invoice creation
    mock_api.post.return_value.status_code = 201
    mock_api.post.return_value.json.return_value = {
        "id": "789",
        "number": "INV-001",
        "total": 100.0,
        "date": "2024-01-01"
    }
    
    return mock_api


@pytest.fixture
def sample_invoice_data() -> Dict[str, Any]:
    """Sample invoice data for testing."""
    return {
        "tipo": "compra",
        "fecha": "2024-01-01",
        "proveedor": "Test Supplier",
        "cliente": "Test Client",
        "items": [
            {
                "codigo": "001",
                "descripcion": "Test Product",
                "cantidad": 1.0,
                "precio": 100.0
            }
        ],
        "subtotal": 100.0,
        "impuestos": 19.0,
        "total": 119.0
    }


@pytest.fixture
def sample_pdf_content() -> str:
    """Sample PDF text content for testing."""
    return """
    FACTURA ELECTRÓNICA DE VENTA #12345
    Fecha: 01-01-2024
    Proveedor: Test Supplier S.A.S.
    NIT: 12345678-9
    
    Descripción: Test Product
    Cantidad: 1 Unidad
    Precio unit.: $100.000
    Subtotal: $100.000
    IVA: $19.000
    Total: $119.000
    """


@pytest.fixture
def mock_tax_calculation() -> Dict[str, Any]:
    """Mock tax calculation result."""
    return {
        "iva_amount": 19.0,
        "iva_rate": 0.19,
        "retefuente_renta": 0.0,
        "retefuente_iva": 0.0,
        "retefuente_ica": 0.0,
        "total_withholdings": 0.0,
        "net_amount": 119.0,
        "compliance_status": "COMPLIANT"
    }


@pytest.fixture(autouse=True)
def setup_test_environment(mock_alegra_credentials: None) -> None:
    """Setup test environment before each test."""
    # Ensure test environment is clean
    pass


@pytest.fixture
def mock_redis() -> Mock:
    """Mock Redis client for testing."""
    mock_redis = Mock()
    mock_redis.get.return_value = None
    mock_redis.set.return_value = True
    mock_redis.delete.return_value = True
    return mock_redis


@pytest.fixture
def mock_celery() -> Mock:
    """Mock Celery for testing."""
    with patch("celery.Celery") as mock_celery:
        mock_app = Mock()
        mock_celery.return_value = mock_app
        yield mock_app


# Pytest markers
def pytest_configure(config):
    """Configure pytest markers."""
    config.addinivalue_line("markers", "unit: Unit tests")
    config.addinivalue_line("markers", "integration: Integration tests")
    config.addinivalue_line("markers", "e2e: End-to-end tests")
    config.addinivalue_line("markers", "performance: Performance tests")
    config.addinivalue_line("markers", "slow: Slow tests")
