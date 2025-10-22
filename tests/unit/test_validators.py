#!/usr/bin/env python3
"""
Tests unitarios para validadores
"""

import pytest
from decimal import Decimal

from src.core.validators.input_validator import InputValidator
from src.core.validators.tax_validator import TaxValidator
from src.exceptions import ValidationError


class TestInputValidator:
    """Tests para InputValidator"""
    
    def test_init(self):
        """Test inicialización del validador"""
        validator = InputValidator()
        assert validator is not None
    
    def test_validate_file_path(self):
        """Test validación de ruta de archivo"""
        validator = InputValidator()
        
        # Test ruta válida
        valid_path = "test.pdf"
        result = validator.validate_file_path(valid_path)
        assert result is True
        
        # Test ruta inválida
        invalid_path = "../../../etc/passwd"
        with pytest.raises(ValidationError):
            validator.validate_file_path(invalid_path)
    
    def test_validate_file_extension(self):
        """Test validación de extensión de archivo"""
        validator = InputValidator()
        
        # Test extensiones válidas
        valid_extensions = ["test.pdf", "test.jpg", "test.png", "test.jpeg"]
        for ext in valid_extensions:
            result = validator.validate_file_extension(ext)
            assert result is True
        
        # Test extensiones inválidas
        invalid_extensions = ["test.exe", "test.bat", "test.sh"]
        for ext in invalid_extensions:
            with pytest.raises(ValidationError):
                validator.validate_file_extension(ext)
    
    def test_validate_file_size(self):
        """Test validación de tamaño de archivo"""
        validator = InputValidator()
        
        # Test tamaño válido
        valid_size = 1024 * 1024  # 1MB
        result = validator.validate_file_size(valid_size)
        assert result is True
        
        # Test tamaño inválido
        invalid_size = 100 * 1024 * 1024  # 100MB
        with pytest.raises(ValidationError):
            validator.validate_file_size(invalid_size)
    
    def test_validate_contact_name(self):
        """Test validación de nombre de contacto"""
        validator = InputValidator()
        
        # Test nombres válidos
        valid_names = ["Cliente Test", "Proveedor ABC", "Empresa XYZ"]
        for name in valid_names:
            result = validator.validate_contact_name(name)
            assert result is True
        
        # Test nombres inválidos
        invalid_names = ["", "   ", "A" * 256, "Cliente<script>"]
        for name in invalid_names:
            with pytest.raises(ValidationError):
                validator.validate_contact_name(name)
    
    def test_validate_contact_identification(self):
        """Test validación de identificación de contacto"""
        validator = InputValidator()
        
        # Test identificaciones válidas
        valid_ids = ["123456789", "900123456-1", "12345678-9"]
        for id_num in valid_ids:
            result = validator.validate_contact_identification(id_num)
            assert result is True
        
        # Test identificaciones inválidas
        invalid_ids = ["", "abc123", "123-abc", "1234567890"]
        for id_num in invalid_ids:
            with pytest.raises(ValidationError):
                validator.validate_contact_identification(id_num)
    
    def test_validate_item_name(self):
        """Test validación de nombre de item"""
        validator = InputValidator()
        
        # Test nombres válidos
        valid_names = ["Producto Test", "Servicio ABC", "Item XYZ"]
        for name in valid_names:
            result = validator.validate_item_name(name)
            assert result is True
        
        # Test nombres inválidos
        invalid_names = ["", "   ", "A" * 256, "Producto<script>"]
        for name in invalid_names:
            with pytest.raises(ValidationError):
                validator.validate_item_name(name)
    
    def test_validate_amount(self):
        """Test validación de monto"""
        validator = InputValidator()
        
        # Test montos válidos
        valid_amounts = [0, 1000, 100000.50, 1000000]
        for amount in valid_amounts:
            result = validator.validate_amount(amount)
            assert result is True
        
        # Test montos inválidos
        invalid_amounts = [-1, -100, 10000000, "abc"]
        for amount in invalid_amounts:
            with pytest.raises(ValidationError):
                validator.validate_amount(amount)


class TestTaxValidator:
    """Tests para TaxValidator"""
    
    def test_init(self):
        """Test inicialización del validador"""
        validator = TaxValidator()
        assert validator is not None
    
    def test_validate_iva_rate(self):
        """Test validación de tasa de IVA"""
        validator = TaxValidator()
        
        # Test tasas válidas
        valid_rates = [0, 0.05, 0.19, 0.21]
        for rate in valid_rates:
            result = validator.validate_iva_rate(rate)
            assert result is True
        
        # Test tasas inválidas
        invalid_rates = [-0.1, 1.1, 2.0, "abc"]
        for rate in invalid_rates:
            with pytest.raises(ValidationError):
                validator.validate_iva_rate(rate)
    
    def test_validate_rete_fuente_rate(self):
        """Test validación de tasa de retención en la fuente"""
        validator = TaxValidator()
        
        # Test tasas válidas
        valid_rates = [0, 0.01, 0.05, 0.1]
        for rate in valid_rates:
            result = validator.validate_rete_fuente_rate(rate)
            assert result is True
        
        # Test tasas inválidas
        invalid_rates = [-0.1, 1.1, 2.0, "abc"]
        for rate in invalid_rates:
            with pytest.raises(ValidationError):
                validator.validate_rete_fuente_rate(rate)
    
    def test_validate_tax_calculation(self):
        """Test validación de cálculo de impuestos"""
        validator = TaxValidator()
        
        # Test cálculo válido
        valid_calculation = {
            "subtotal": 100000,
            "iva_rate": 0.19,
            "iva_amount": 19000,
            "total": 119000
        }
        result = validator.validate_tax_calculation(valid_calculation)
        assert result is True
        
        # Test cálculo inválido
        invalid_calculation = {
            "subtotal": 100000,
            "iva_rate": 0.19,
            "iva_amount": 20000,  # Incorrecto
            "total": 119000
        }
        with pytest.raises(ValidationError):
            validator.validate_tax_calculation(invalid_calculation)
    
    def test_validate_uvt_value(self):
        """Test validación de valor UVT"""
        validator = TaxValidator()
        
        # Test valores válidos
        valid_values = [50000, 100000, 200000]
        for value in valid_values:
            result = validator.validate_uvt_value(value)
            assert result is True
        
        # Test valores inválidos
        invalid_values = [-1, 0, 10000000, "abc"]
        for value in invalid_values:
            with pytest.raises(ValidationError):
                validator.validate_uvt_value(value)
    
    def test_validate_tax_rules(self):
        """Test validación de reglas fiscales"""
        validator = TaxValidator()
        
        # Test reglas válidas
        valid_rules = {
            "uvt_value": 50000,
            "iva_rate": 0.19,
            "rete_fuente_renta": 0.05,
            "rete_fuente_iva": 0.03,
            "rete_fuente_ica": 0.01
        }
        result = validator.validate_tax_rules(valid_rules)
        assert result is True
        
        # Test reglas inválidas
        invalid_rules = {
            "uvt_value": -1,
            "iva_rate": 1.5,
            "rete_fuente_renta": -0.1,
            "rete_fuente_iva": 2.0,
            "rete_fuente_ica": "abc"
        }
        with pytest.raises(ValidationError):
            validator.validate_tax_rules(invalid_rules)

