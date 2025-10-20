#!/usr/bin/env python3
"""
Calculador de Impuestos Colombianos 2025
Implementa ReteFuente (Renta, IVA, ICA), Impuesto a la Renta e IVA
Basado en normativa DIAN 2025 y Reforma Tributaria 2022/2023
"""

import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class TaxResult:
    """Resultado del cálculo de impuestos"""
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
    """Datos de la factura para cálculo de impuestos"""
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
    """Calculador de impuestos colombianos para 2025"""
    
    def __init__(self, config_path: str = "config/tax_rules_CO_2025.json"):
        """Inicializar calculador con configuración fiscal 2025"""
        self.config_path = config_path
        self.config = self._load_config()
        self.uvt_2025 = self.config["uvt_2025"]
        
        logger.info(f"✅ Calculador de impuestos inicializado - UVT 2025: ${self.uvt_2025:,}")
    
    def _load_config(self) -> Dict:
        """Cargar configuración fiscal"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            logger.info(f"📋 Configuración fiscal cargada: {config['version']}")
            return config
        except FileNotFoundError:
            logger.error(f"❌ Archivo de configuración no encontrado: {self.config_path}")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"❌ Error en configuración JSON: {e}")
            raise
    
    def calculate_taxes(self, invoice_data: InvoiceData) -> TaxResult:
        """Calcular todos los impuestos aplicables a la factura"""
        logger.info(f"🧮 Calculando impuestos para factura #{invoice_data.invoice_number}")
        
        # 1. Calcular IVA
        iva_result = self._calculate_iva(invoice_data)
        
        # 2. Calcular ReteFuente Renta
        retefuente_renta = self._calculate_retefuente_renta(invoice_data)
        
        # 3. Calcular ReteFuente IVA
        retefuente_iva = self._calculate_retefuente_iva(invoice_data, iva_result['amount'])
        
        # 4. Calcular ReteFuente ICA
        retefuente_ica = self._calculate_retefuente_ica(invoice_data)
        
        # 5. Calcular totales
        total_withholdings = retefuente_renta + retefuente_iva + retefuente_ica
        net_amount = invoice_data.total_amount - total_withholdings
        
        # 6. Validar compliance
        compliance_status = self._validate_compliance(invoice_data, iva_result, total_withholdings)
        
        # 7. Crear breakdown detallado
        tax_breakdown = {
            "iva": iva_result,
            "retefuente": {
                "renta": {
                    "amount": retefuente_renta,
                    "rate": self._get_retefuente_renta_rate(invoice_data),
                    "description": "Retención en la fuente por renta"
                },
                "iva": {
                    "amount": retefuente_iva,
                    "rate": self._get_retefuente_iva_rate(invoice_data),
                    "description": "Retención en la fuente por IVA"
                },
                "ica": {
                    "amount": retefuente_ica,
                    "rate": self._get_retefuente_ica_rate(invoice_data),
                    "description": "Retención en la fuente por ICA"
                }
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
        
        logger.info(f"✅ Cálculo completado - IVA: ${iva_result['amount']:,.2f}, Retenciones: ${total_withholdings:,.2f}")
        return result
    
    def _calculate_iva(self, invoice_data: InvoiceData) -> Dict:
        """Calcular IVA según categoría del producto/servicio"""
        # Determinar tasa de IVA según tipo de item
        item_category = self._categorize_item(invoice_data.item_type, invoice_data.description)
        iva_rate = self.config["iva_categories"][item_category]["rate"]
        
        # Calcular IVA
        iva_amount = invoice_data.base_amount * iva_rate
        
        return {
            "amount": iva_amount,
            "rate": iva_rate,
            "category": item_category,
            "description": self.config["iva_categories"][item_category]["description"]
        }
    
    def _categorize_item(self, item_type: str, description: str) -> str:
        """Categorizar item para determinar tasa de IVA"""
        description_lower = description.lower()
        
        # Alimentos para mascotas (5% IVA)
        if any(word in description_lower for word in ['royal canin', 'gato', 'perro', 'mascota', 'pet', 'alimento']):
            return "pet_food"
        
        # Alimentos básicos (0% IVA)
        elif any(word in description_lower for word in ['arroz', 'leche', 'pan', 'huevos', 'pollo', 'carne']):
            return "basic_food"
        
        # Electrónicos (19% IVA)
        elif any(word in description_lower for word in ['celular', 'computador', 'laptop', 'tablet', 'electrónico']):
            return "electronics"
        
        # Ropa (19% IVA)
        elif any(word in description_lower for word in ['camisa', 'pantalón', 'zapatos', 'ropa', 'vestido']):
            return "clothing"
        
        # Vehículos eléctricos (5% IVA)
        elif any(word in description_lower for word in ['vehículo eléctrico', 'carro eléctrico', 'moto eléctrica']):
            return "vehicles_electric"
        
        # General (19% IVA)
        else:
            return "general"
    
    def _calculate_retefuente_renta(self, invoice_data: InvoiceData) -> float:
        """Calcular ReteFuente por Renta"""
        if invoice_data.buyer_regime != "comun":
            return 0.0
        
        # Determinar tipo de pago y umbral
        payment_type = self._classify_payment_type(invoice_data.description)
        threshold_config = self.config["retefuente_renta"]["thresholds"].get(payment_type)
        
        if not threshold_config:
            return 0.0
        
        # Verificar umbral mínimo
        threshold_uvt = threshold_config["uvt_min"]
        threshold_amount = threshold_uvt * self.uvt_2025
        
        if invoice_data.base_amount < threshold_amount:
            return 0.0
        
        # Calcular tasa
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
        
        # Calcular retención
        retefuente_amount = invoice_data.base_amount * rate
        
        logger.info(f"💰 ReteFuente Renta: ${retefuente_amount:,.2f} ({rate*100:.1f}%)")
        return retefuente_amount
    
    def _classify_payment_type(self, description: str) -> str:
        """Clasificar tipo de pago para ReteFuente"""
        desc_lower = description.lower()
        
        if any(word in desc_lower for word in ['honorario', 'comisión', 'profesional', 'consultoría']):
            return "honorarios"
        elif any(word in desc_lower for word in ['arrendamiento', 'alquiler', 'renta']):
            return "arrendamientos"
        elif any(word in desc_lower for word in ['compra', 'mercancía', 'producto', 'bien', 'royal canin', 'alimento']):
            return "compras_bienes"
        else:
            return "servicios_generales"
    
    def _calculate_retefuente_iva(self, invoice_data: InvoiceData, iva_amount: float) -> float:
        """Calcular ReteFuente por IVA"""
        if invoice_data.buyer_regime != "comun" or iva_amount == 0:
            return 0.0
        
        # Verificar umbral (10 UVT desde 2025)
        threshold_amount = 10 * self.uvt_2025
        if invoice_data.base_amount < threshold_amount:
            return 0.0
        
        # Determinar tasa según régimen del comprador
        if invoice_data.buyer_regime == "comun":
            rate = self.config["retefuente_iva"]["rates"]["comun"]
        else:
            rate = self.config["retefuente_iva"]["rates"]["gran_contribuyente"]
        
        retefuente_amount = iva_amount * rate
        
        logger.info(f"💰 ReteFuente IVA: ${retefuente_amount:,.2f} ({rate*100:.1f}%)")
        return retefuente_amount
    
    def _calculate_retefuente_ica(self, invoice_data: InvoiceData) -> float:
        """Calcular ReteFuente por ICA"""
        if invoice_data.buyer_regime != "comun":
            return 0.0
        
        # Verificar si aplica (diferente ciudad o contrato >1 año)
        if invoice_data.vendor_city == invoice_data.buyer_city:
            return 0.0
        
        # Obtener configuración de la ciudad del comprador
        city_config = self.config["retefuente_ica"]["cities"].get(invoice_data.buyer_city.lower())
        if not city_config:
            return 0.0
        
        # Verificar umbral
        threshold_amount = city_config["threshold_uvt"] * self.uvt_2025
        if invoice_data.base_amount < threshold_amount:
            return 0.0
        
        # Determinar actividad (simplificado)
        activity = self._classify_activity(invoice_data.description)
        rate = city_config["rates"].get(activity, city_config["rates"]["comercio"])
        
        retefuente_amount = invoice_data.base_amount * rate
        
        logger.info(f"💰 ReteFuente ICA: ${retefuente_amount:,.2f} ({rate*100:.3f}%)")
        return retefuente_amount
    
    def _classify_activity(self, description: str) -> str:
        """Clasificar actividad para ICA"""
        desc_lower = description.lower()
        
        if any(word in desc_lower for word in ['fábrica', 'producción', 'manufactura', 'industrial']):
            return "industria"
        elif any(word in desc_lower for word in ['servicio', 'consultoría', 'asesoría', 'profesional']):
            return "servicios"
        else:
            return "comercio"
    
    def _get_retefuente_renta_rate(self, invoice_data: InvoiceData) -> float:
        """Obtener tasa de ReteFuente Renta aplicada"""
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
        """Obtener tasa de ReteFuente IVA aplicada"""
        if invoice_data.buyer_regime == "comun":
            return self.config["retefuente_iva"]["rates"]["comun"]
        else:
            return self.config["retefuente_iva"]["rates"]["gran_contribuyente"]
    
    def _get_retefuente_ica_rate(self, invoice_data: InvoiceData) -> float:
        """Obtener tasa de ReteFuente ICA aplicada"""
        city_config = self.config["retefuente_ica"]["cities"].get(invoice_data.buyer_city.lower())
        if not city_config:
            return 0.0
        
        activity = self._classify_activity(invoice_data.description)
        return city_config["rates"].get(activity, city_config["rates"]["comercio"])
    
    def _validate_compliance(self, invoice_data: InvoiceData, iva_result: Dict, total_withholdings: float) -> str:
        """Validar compliance fiscal"""
        tolerance = self.config["validation_rules"]["tolerance_amount"]
        
        # Validar IVA calculado vs extraído
        iva_difference = abs(iva_result['amount'] - invoice_data.iva_amount)
        if iva_difference > tolerance:
            return f"WARNING: Diferencia en IVA ${iva_difference:.2f} > tolerancia ${tolerance}"
        
        # Validar totales
        expected_total = invoice_data.base_amount + iva_result['amount']
        total_difference = abs(expected_total - invoice_data.total_amount)
        if total_difference > tolerance:
            return f"WARNING: Diferencia en total ${total_difference:.2f} > tolerancia ${tolerance}"
        
        return "COMPLIANT"
    
    def create_alegra_payload(self, tax_result: TaxResult) -> Dict:
        """Crear payload para Alegra con información fiscal"""
        payload = {
            "tax": [
                {
                    "rate": tax_result.iva_rate * 100,
                    "amount": tax_result.iva_amount,
                    "type": "iva",
                    "description": "IVA"
                }
            ],
            "withholdings": []
        }
        
        # Agregar retenciones si aplican
        if tax_result.retefuente_renta > 0:
            payload["withholdings"].append({
                "type": "renta",
                "amount": tax_result.retefuente_renta,
                "rate": 0.0,  # Se calculará dinámicamente
                "description": "Retención en la fuente por renta"
            })
        
        if tax_result.retefuente_iva > 0:
            payload["withholdings"].append({
                "type": "iva",
                "amount": tax_result.retefuente_iva,
                "rate": 0.0,  # Se calculará dinámicamente
                "description": "Retención en la fuente por IVA"
            })
        
        if tax_result.retefuente_ica > 0:
            payload["withholdings"].append({
                "type": "ica",
                "amount": tax_result.retefuente_ica,
                "rate": 0.0,  # Se calculará dinámicamente
                "description": "Retención en la fuente por ICA"
            })
        
        return payload
    
    def get_tax_summary(self, tax_result: TaxResult) -> str:
        """Generar resumen de impuestos para logging"""
        summary = f"""
📊 RESUMEN FISCAL
================
💰 Base: ${tax_result.tax_breakdown['totals']['base_amount']:,.2f}
🧾 IVA ({tax_result.iva_rate*100:.1f}%): ${tax_result.iva_amount:,.2f}
💵 Total: ${tax_result.tax_breakdown['totals']['total_amount']:,.2f}

📋 RETENCIONES:
   • Renta: ${tax_result.retefuente_renta:,.2f}
   • IVA: ${tax_result.retefuente_iva:,.2f}
   • ICA: ${tax_result.retefuente_ica:,.2f}
   • Total: ${tax_result.total_withholdings:,.2f}

💸 NETO A PAGAR: ${tax_result.net_amount:,.2f}
✅ Estado: {tax_result.compliance_status}
        """
        return summary.strip()

# Funciones de utilidad
def create_invoice_data_from_pdf(pdf_data: Dict) -> InvoiceData:
    """Crear InvoiceData desde datos extraídos del PDF"""
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

def main():
    """Función principal para testing"""
    # Ejemplo de uso
    calculator = ColombianTaxCalculator()
    
    # Datos de ejemplo basados en la factura de Royal Canin
    invoice_data = InvoiceData(
        base_amount=203343.81,
        total_amount=213511.00,
        iva_amount=10167.19,
        iva_rate=0.05,
        item_type="pet_food",
        description="ROYAL CANIN GATO GASTROINTESTINAL FIBRE x2KG",
        vendor_nit="52147745-1",
        vendor_regime="comun",
        vendor_city="bogota",
        buyer_nit="1136886917",
        buyer_regime="comun",
        buyer_city="bogota",
        invoice_date="2025-10-10",
        invoice_number="21488"
    )
    
    # Calcular impuestos
    tax_result = calculator.calculate_taxes(invoice_data)
    
    # Mostrar resultados
    print(calculator.get_tax_summary(tax_result))
    
    # Crear payload para Alegra
    alegra_payload = calculator.create_alegra_payload(tax_result)
    print("\n📤 Payload para Alegra:")
    print(json.dumps(alegra_payload, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()