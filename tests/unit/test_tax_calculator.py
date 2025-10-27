"""
Unit tests for tax calculator.
"""

import pytest
from unittest.mock import Mock, patch

from src.core.tax_calculator import ColombianTaxCalculator, InvoiceData, TaxResult


class TestColombianTaxCalculator:
    """Test Colombian tax calculator functionality."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.calculator = ColombianTaxCalculator()
    
    def test_initialization(self):
        """Test calculator initialization."""
        assert self.calculator.uvt_2025 > 0
        assert "iva_categories" in self.calculator.config
        assert "retefuente_renta" in self.calculator.config
    
    def test_categorize_item_pet_food(self):
        """Test pet food categorization."""
        result = self.calculator._categorize_item("product", "Royal Canin para gatos")
        assert result == "pet_food"
    
    def test_categorize_item_basic_food(self):
        """Test basic food categorization."""
        result = self.calculator._categorize_item("product", "Arroz blanco")
        assert result == "basic_food"
    
    def test_categorize_item_general(self):
        """Test general item categorization."""
        result = self.calculator._categorize_item("product", "Laptop Dell")
        assert result == "general"
    
    def test_classify_payment_type_honorarios(self):
        """Test honorarios payment type classification."""
        result = self.calculator._classify_payment_type("Honorarios profesionales")
        assert result == "honorarios"
    
    def test_classify_payment_type_compras(self):
        """Test compras payment type classification."""
        result = self.calculator._classify_payment_type("Compra de mercancía")
        assert result == "compras_bienes"
    
    def test_classify_payment_type_arrendamientos(self):
        """Test arrendamientos payment type classification."""
        result = self.calculator._classify_payment_type("Arrendamiento de oficina")
        assert result == "arrendamientos"
    
    def test_calculate_iva_general(self):
        """Test IVA calculation for general items."""
        invoice_data = InvoiceData(
            base_amount=100000,
            total_amount=119000,
            iva_amount=19000,
            iva_rate=0.19,
            item_type="general",
            description="Producto general",
            vendor_nit="12345678-9",
            vendor_regime="comun",
            vendor_city="bogota",
            buyer_nit="87654321-1",
            buyer_regime="comun",
            buyer_city="bogota",
            invoice_date="2024-01-01",
            invoice_number="001"
        )
        
        result = self.calculator._calculate_iva(invoice_data)
        
        assert result["amount"] == 19000.0
        assert result["rate"] == 0.19
        assert result["category"] == "general"
    
    def test_calculate_iva_pet_food(self):
        """Test IVA calculation for pet food."""
        invoice_data = InvoiceData(
            base_amount=100000,
            total_amount=105000,
            iva_amount=5000,
            iva_rate=0.05,
            item_type="pet_food",
            description="Royal Canin para gatos",
            vendor_nit="12345678-9",
            vendor_regime="comun",
            vendor_city="bogota",
            buyer_nit="87654321-1",
            buyer_regime="comun",
            buyer_city="bogota",
            invoice_date="2024-01-01",
            invoice_number="001"
        )
        
        result = self.calculator._calculate_iva(invoice_data)
        
        assert result["amount"] == 5000.0
        assert result["rate"] == 0.05
        assert result["category"] == "pet_food"
    
    def test_calculate_retefuente_renta_below_threshold(self):
        """Test ReteFuente Renta below threshold."""
        invoice_data = InvoiceData(
            base_amount=100000,  # Below threshold
            total_amount=119000,
            iva_amount=19000,
            iva_rate=0.19,
            item_type="general",
            description="Servicios generales",
            vendor_nit="12345678-9",
            vendor_regime="comun",
            vendor_city="bogota",
            buyer_nit="87654321-1",
            buyer_regime="comun",
            buyer_city="bogota",
            invoice_date="2024-01-01",
            invoice_number="001"
        )
        
        result = self.calculator._calculate_retefuente_renta(invoice_data)
        assert result == 0.0
    
    def test_calculate_retefuente_renta_above_threshold(self):
        """Test ReteFuente Renta above threshold."""
        invoice_data = InvoiceData(
            base_amount=1000000,  # Above threshold
            total_amount=1190000,
            iva_amount=190000,
            iva_rate=0.19,
            item_type="general",
            description="Servicios generales",
            vendor_nit="12345678-9",
            vendor_regime="comun",
            vendor_city="bogota",
            buyer_nit="87654321-1",
            buyer_regime="comun",
            buyer_city="bogota",
            invoice_date="2024-01-01",
            invoice_number="001"
        )
        
        result = self.calculator._calculate_retefuente_renta(invoice_data)
        assert result > 0
    
    def test_calculate_retefuente_iva_below_threshold(self):
        """Test ReteFuente IVA below threshold."""
        invoice_data = InvoiceData(
            base_amount=100000,  # Below threshold
            total_amount=119000,
            iva_amount=19000,
            iva_rate=0.19,
            item_type="general",
            description="Producto general",
            vendor_nit="12345678-9",
            vendor_regime="comun",
            vendor_city="bogota",
            buyer_nit="87654321-1",
            buyer_regime="comun",
            buyer_city="bogota",
            invoice_date="2024-01-01",
            invoice_number="001"
        )
        
        result = self.calculator._calculate_retefuente_iva(invoice_data, 19000)
        assert result == 0.0
    
    def test_calculate_retefuente_ica_same_city(self):
        """Test ReteFuente ICA same city."""
        invoice_data = InvoiceData(
            base_amount=1000000,
            total_amount=1190000,
            iva_amount=190000,
            iva_rate=0.19,
            item_type="general",
            description="Producto general",
            vendor_nit="12345678-9",
            vendor_regime="comun",
            vendor_city="bogota",
            buyer_nit="87654321-1",
            buyer_regime="comun",
            buyer_city="bogota",  # Same city
            invoice_date="2024-01-01",
            invoice_number="001"
        )
        
        result = self.calculator._calculate_retefuente_ica(invoice_data)
        assert result == 0.0
    
    def test_calculate_taxes_complete(self):
        """Test complete tax calculation."""
        invoice_data = InvoiceData(
            base_amount=1000000,
            total_amount=1190000,
            iva_amount=190000,
            iva_rate=0.19,
            item_type="general",
            description="Royal Canin para gatos",
            vendor_nit="12345678-9",
            vendor_regime="comun",
            vendor_city="bogota",
            buyer_nit="87654321-1",
            buyer_regime="comun",
            buyer_city="medellin",  # Different city
            invoice_date="2024-01-01",
            invoice_number="001"
        )
        
        result = self.calculator.calculate_taxes(invoice_data)
        
        assert isinstance(result, TaxResult)
        assert result.iva_amount > 0
        assert result.total_withholdings >= 0
        assert result.net_amount > 0
        assert result.compliance_status in ["COMPLIANT", "WARNING"]
    
    def test_validate_compliance_compliant(self):
        """Test compliance validation for compliant invoice."""
        invoice_data = InvoiceData(
            base_amount=100000,
            total_amount=119000,
            iva_amount=19000,
            iva_rate=0.19,
            item_type="general",
            description="Producto general",
            vendor_nit="12345678-9",
            vendor_regime="comun",
            vendor_city="bogota",
            buyer_nit="87654321-1",
            buyer_regime="comun",
            buyer_city="bogota",
            invoice_date="2024-01-01",
            invoice_number="001"
        )
        
        iva_result = {"amount": 19000, "rate": 0.19}
        total_withholdings = 0
        
        result = self.calculator._validate_compliance(invoice_data, iva_result, total_withholdings)
        assert result == "COMPLIANT"
    
    def test_validate_compliance_warning(self):
        """Test compliance validation with warning."""
        invoice_data = InvoiceData(
            base_amount=100000,
            total_amount=119000,
            iva_amount=19000,
            iva_rate=0.19,
            item_type="general",
            description="Producto general",
            vendor_nit="12345678-9",
            vendor_regime="comun",
            vendor_city="bogota",
            buyer_nit="87654321-1",
            buyer_regime="comun",
            buyer_city="bogota",
            invoice_date="2024-01-01",
            invoice_number="001"
        )
        
        iva_result = {"amount": 20000, "rate": 0.19}  # Different amount
        total_withholdings = 0
        
        result = self.calculator._validate_compliance(invoice_data, iva_result, total_withholdings)
        assert "WARNING" in result
    
    def test_get_tax_summary(self):
        """Test tax summary generation."""
        tax_result = TaxResult(
            iva_amount=19000,
            iva_rate=0.19,
            retefuente_renta=5000,
            retefuente_iva=2000,
            retefuente_ica=1000,
            total_withholdings=8000,
            net_amount=111000,
            compliance_status="COMPLIANT",
            tax_breakdown={
                "totals": {
                    "base_amount": 100000,
                    "total_amount": 119000
                }
            }
        )
        
        summary = self.calculator.get_tax_summary(tax_result)
        
        assert "TAX SUMMARY" in summary
        assert "$19,000" in summary
        assert "$8,000" in summary
        assert "COMPLIANT" in summary
