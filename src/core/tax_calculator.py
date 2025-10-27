"""
Tax calculation module - consolidated from existing tax_calculator.py
"""

import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class TaxResult:
    """Result of tax calculation."""
    iva_amount: float
    iva_rate: float
    retefuente_renta: float
    retefuente_iva: float
    retefuente_ica: float
    total_withholdings: float
    net_amount: float
    tax_breakdown: Dict
    compliance_status: str


@dataclass
class InvoiceData:
    """Invoice data for tax calculation."""
    base_amount: float
    total_amount: float
    iva_amount: float
    iva_rate: float
    item_type: str
    description: str
    vendor_nit: str
    vendor_regime: str
    vendor_city: str
    buyer_nit: str
    buyer_regime: str
    buyer_city: str
    invoice_date: str
    invoice_number: str


class ColombianTaxCalculator:
    """Colombian tax calculator for 2025."""
    
    def __init__(self, config_path: str = "config/tax_rules_CO_2025.json"):
        """Initialize tax calculator."""
        self.config_path = config_path
        self.config = self._load_config()
        self.uvt_2025 = self.config.get("uvt_2025", 50000)
        
        logger.info(f"✅ Tax calculator initialized - UVT 2025: ${self.uvt_2025:,}")
    
    def _load_config(self) -> Dict:
        """Load tax configuration."""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            logger.info(f"📋 Tax configuration loaded: {config.get('version', 'unknown')}")
            return config
        except FileNotFoundError:
            logger.error(f"❌ Tax config file not found: {self.config_path}")
            return self._get_default_config()
        except json.JSONDecodeError as e:
            logger.error(f"❌ Invalid tax config JSON: {e}")
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict:
        """Get default tax configuration."""
        return {
            "version": "2025-default",
            "uvt_2025": 50000,
            "iva_categories": {
                "general": {"rate": 0.19, "description": "General (19%)"},
                "pet_food": {"rate": 0.05, "description": "Alimentos para mascotas (5%)"},
                "basic_food": {"rate": 0.0, "description": "Alimentos básicos (0%)"},
            },
            "retefuente_renta": {
                "thresholds": {
                    "honorarios": {"uvt_min": 10, "rate_low": 0.10, "rate_high": 0.15},
                    "compras_bienes": {"uvt_min": 5, "rate_declarante": 0.035, "rate_no_declarante": 0.07},
                }
            },
            "retefuente_iva": {
                "rates": {"comun": 0.15, "gran_contribuyente": 0.20}
            },
            "retefuente_ica": {
                "cities": {
                    "bogota": {"threshold_uvt": 5, "rates": {"comercio": 0.00966, "industria": 0.00966, "servicios": 0.00966}}
                }
            },
            "validation_rules": {"tolerance_amount": 1.0}
        }
    
    def calculate_taxes(self, invoice_data: InvoiceData) -> TaxResult:
        """Calculate all applicable taxes."""
        logger.info(f"🧮 Calculating taxes for invoice #{invoice_data.invoice_number}")
        
        # Calculate IVA
        iva_result = self._calculate_iva(invoice_data)
        
        # Calculate ReteFuente Renta
        retefuente_renta = self._calculate_retefuente_renta(invoice_data)
        
        # Calculate ReteFuente IVA
        retefuente_iva = self._calculate_retefuente_iva(invoice_data, iva_result['amount'])
        
        # Calculate ReteFuente ICA
        retefuente_ica = self._calculate_retefuente_ica(invoice_data)
        
        # Calculate totals
        total_withholdings = retefuente_renta + retefuente_iva + retefuente_ica
        net_amount = invoice_data.total_amount - total_withholdings
        
        # Validate compliance
        compliance_status = self._validate_compliance(invoice_data, iva_result, total_withholdings)
        
        # Create tax breakdown
        tax_breakdown = {
            "iva": iva_result,
            "retefuente": {
                "renta": {"amount": retefuente_renta, "rate": self._get_retefuente_renta_rate(invoice_data)},
                "iva": {"amount": retefuente_iva, "rate": self._get_retefuente_iva_rate(invoice_data)},
                "ica": {"amount": retefuente_ica, "rate": self._get_retefuente_ica_rate(invoice_data)},
            },
            "totals": {
                "base_amount": invoice_data.base_amount,
                "iva_amount": iva_result['amount'],
                "total_amount": invoice_data.total_amount,
                "total_withholdings": total_withholdings,
                "net_amount": net_amount
            }
        }
        
        result = TaxResult(
            iva_amount=iva_result['amount'],
            iva_rate=iva_result['rate'],
            retefuente_renta=retefuente_renta,
            retefuente_iva=retefuente_iva,
            retefuente_ica=retefuente_ica,
            total_withholdings=total_withholdings,
            net_amount=net_amount,
            tax_breakdown=tax_breakdown,
            compliance_status=compliance_status
        )
        
        logger.info(f"✅ Tax calculation completed - IVA: ${iva_result['amount']:,.2f}, Retenciones: ${total_withholdings:,.2f}")
        return result
    
    def _calculate_iva(self, invoice_data: InvoiceData) -> Dict:
        """Calculate IVA based on item category."""
        item_category = self._categorize_item(invoice_data.item_type, invoice_data.description)
        iva_rate = self.config["iva_categories"][item_category]["rate"]
        iva_amount = invoice_data.base_amount * iva_rate
        
        return {
            "amount": iva_amount,
            "rate": iva_rate,
            "category": item_category,
            "description": self.config["iva_categories"][item_category]["description"]
        }
    
    def _categorize_item(self, item_type: str, description: str) -> str:
        """Categorize item for IVA calculation."""
        desc_lower = description.lower()
        
        if any(word in desc_lower for word in ['royal canin', 'gato', 'perro', 'mascota', 'pet', 'alimento']):
            return "pet_food"
        elif any(word in desc_lower for word in ['arroz', 'leche', 'pan', 'huevos', 'pollo', 'carne']):
            return "basic_food"
        else:
            return "general"
    
    def _calculate_retefuente_renta(self, invoice_data: InvoiceData) -> float:
        """Calculate ReteFuente Renta."""
        if invoice_data.buyer_regime != "comun":
            return 0.0
        
        payment_type = self._classify_payment_type(invoice_data.description)
        threshold_config = self.config["retefuente_renta"]["thresholds"].get(payment_type)
        
        if not threshold_config:
            return 0.0
        
        threshold_amount = threshold_config["uvt_min"] * self.uvt_2025
        if invoice_data.base_amount < threshold_amount:
            return 0.0
        
        if payment_type == "honorarios":
            if invoice_data.base_amount <= 27 * self.uvt_2025:
                rate = threshold_config["rate_low"]
            else:
                rate = threshold_config["rate_high"]
        elif payment_type == "compras_bienes":
            if invoice_data.vendor_regime == "comun":
                rate = threshold_config["rate_declarante"]
            else:
                rate = threshold_config["rate_no_declarante"]
        else:
            rate = threshold_config["rate"]
        
        return invoice_data.base_amount * rate
    
    def _classify_payment_type(self, description: str) -> str:
        """Classify payment type for ReteFuente."""
        desc_lower = description.lower()
        
        if any(word in desc_lower for word in ['honorario', 'comisión', 'profesional', 'consultoría']):
            return "honorarios"
        elif any(word in desc_lower for word in ['arrendamiento', 'alquiler', 'renta']):
            return "arrendamientos"
        elif any(word in desc_lower for word in ['compra', 'mercancía', 'producto', 'bien']):
            return "compras_bienes"
        else:
            return "servicios_generales"
    
    def _calculate_retefuente_iva(self, invoice_data: InvoiceData, iva_amount: float) -> float:
        """Calculate ReteFuente IVA."""
        if invoice_data.buyer_regime != "comun" or iva_amount == 0:
            return 0.0
        
        threshold_amount = 10 * self.uvt_2025
        if invoice_data.base_amount < threshold_amount:
            return 0.0
        
        if invoice_data.buyer_regime == "comun":
            rate = self.config["retefuente_iva"]["rates"]["comun"]
        else:
            rate = self.config["retefuente_iva"]["rates"]["gran_contribuyente"]
        
        return iva_amount * rate
    
    def _calculate_retefuente_ica(self, invoice_data: InvoiceData) -> float:
        """Calculate ReteFuente ICA."""
        if invoice_data.buyer_regime != "comun":
            return 0.0
        
        if invoice_data.vendor_city == invoice_data.buyer_city:
            return 0.0
        
        city_config = self.config["retefuente_ica"]["cities"].get(invoice_data.buyer_city.lower())
        if not city_config:
            return 0.0
        
        threshold_amount = city_config["threshold_uvt"] * self.uvt_2025
        if invoice_data.base_amount < threshold_amount:
            return 0.0
        
        activity = self._classify_activity(invoice_data.description)
        rate = city_config["rates"].get(activity, city_config["rates"]["comercio"])
        
        return invoice_data.base_amount * rate
    
    def _classify_activity(self, description: str) -> str:
        """Classify activity for ICA."""
        desc_lower = description.lower()
        
        if any(word in desc_lower for word in ['fábrica', 'producción', 'manufactura', 'industrial']):
            return "industria"
        elif any(word in desc_lower for word in ['servicio', 'consultoría', 'asesoría', 'profesional']):
            return "servicios"
        else:
            return "comercio"
    
    def _get_retefuente_renta_rate(self, invoice_data: InvoiceData) -> float:
        """Get ReteFuente Renta rate."""
        payment_type = self._classify_payment_type(invoice_data.description)
        threshold_config = self.config["retefuente_renta"]["thresholds"].get(payment_type)
        
        if not threshold_config:
            return 0.0
        
        if payment_type == "honorarios":
            if invoice_data.base_amount <= 27 * self.uvt_2025:
                return threshold_config["rate_low"]
            else:
                return threshold_config["rate_high"]
        elif payment_type == "compras_bienes":
            if invoice_data.vendor_regime == "comun":
                return threshold_config["rate_declarante"]
            else:
                return threshold_config["rate_no_declarante"]
        else:
            return threshold_config["rate"]
    
    def _get_retefuente_iva_rate(self, invoice_data: InvoiceData) -> float:
        """Get ReteFuente IVA rate."""
        if invoice_data.buyer_regime == "comun":
            return self.config["retefuente_iva"]["rates"]["comun"]
        else:
            return self.config["retefuente_iva"]["rates"]["gran_contribuyente"]
    
    def _get_retefuente_ica_rate(self, invoice_data: InvoiceData) -> float:
        """Get ReteFuente ICA rate."""
        city_config = self.config["retefuente_ica"]["cities"].get(invoice_data.buyer_city.lower())
        if not city_config:
            return 0.0
        
        activity = self._classify_activity(invoice_data.description)
        return city_config["rates"].get(activity, city_config["rates"]["comercio"])
    
    def _validate_compliance(self, invoice_data: InvoiceData, iva_result: Dict, total_withholdings: float) -> str:
        """Validate tax compliance."""
        tolerance = self.config["validation_rules"]["tolerance_amount"]
        
        # Validate IVA
        iva_difference = abs(iva_result['amount'] - invoice_data.iva_amount)
        if iva_difference > tolerance:
            return f"WARNING: IVA difference ${iva_difference:.2f} > tolerance ${tolerance}"
        
        # Validate totals
        expected_total = invoice_data.base_amount + iva_result['amount']
        total_difference = abs(expected_total - invoice_data.total_amount)
        if total_difference > tolerance:
            return f"WARNING: Total difference ${total_difference:.2f} > tolerance ${tolerance}"
        
        return "COMPLIANT"
    
    def get_tax_summary(self, tax_result: TaxResult) -> str:
        """Generate tax summary for logging."""
        return f"""
📊 TAX SUMMARY
==============
💰 Base: ${tax_result.tax_breakdown['totals']['base_amount']:,.2f}
🧾 IVA ({tax_result.iva_rate*100:.1f}%): ${tax_result.iva_amount:,.2f}
💵 Total: ${tax_result.tax_breakdown['totals']['total_amount']:,.2f}

📋 WITHHOLDINGS:
   • Renta: ${tax_result.retefuente_renta:,.2f}
   • IVA: ${tax_result.retefuente_iva:,.2f}
   • ICA: ${tax_result.retefuente_ica:,.2f}
   • Total: ${tax_result.total_withholdings:,.2f}

💸 NET AMOUNT: ${tax_result.net_amount:,.2f}
✅ Status: {tax_result.compliance_status}
        """.strip()


def create_invoice_data_from_pdf(pdf_data: Dict) -> InvoiceData:
    """Create InvoiceData from PDF data."""
    return InvoiceData(
        base_amount=pdf_data.get('subtotal', 0),
        total_amount=pdf_data.get('total', 0),
        iva_amount=pdf_data.get('impuestos', 0),
        iva_rate=pdf_data.get('impuestos', 0) / pdf_data.get('subtotal', 1) if pdf_data.get('subtotal', 0) > 0 else 0,
        item_type=pdf_data.get('tipo', 'general'),
        description=pdf_data.get('items', [{}])[0].get('descripcion', '') if pdf_data.get('items') else '',
        vendor_nit=pdf_data.get('proveedor_nit', ''),
        vendor_regime=pdf_data.get('proveedor_regime', 'comun'),
        vendor_city=pdf_data.get('proveedor_ciudad', 'bogota'),
        buyer_nit=pdf_data.get('comprador_nit', ''),
        buyer_regime=pdf_data.get('comprador_regime', 'comun'),
        buyer_city=pdf_data.get('comprador_ciudad', 'bogota'),
        invoice_date=pdf_data.get('fecha', ''),
        invoice_number=pdf_data.get('numero_factura', '')
    )
