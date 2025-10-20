#!/usr/bin/env python3
"""
Integración de Impuestos con Nanobot
Maneja casos ambiguos y validaciones fiscales complejas
"""

import json
import logging
from typing import Dict, List, Optional
from tax_calculator import ColombianTaxCalculator, InvoiceData, TaxResult

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TaxNanobotIntegration:
    """Integración de impuestos con Nanobot para casos complejos"""
    
    def __init__(self):
        """Inicializar integración con Nanobot"""
        self.tax_calculator = ColombianTaxCalculator()
        self.nanobot_client = None  # Se inicializará cuando esté disponible
        logger.info("🤖 Integración Tax-Nanobot inicializada")
    
    def process_ambiguous_tax_case(self, invoice_data: InvoiceData, ambiguity_type: str) -> Dict:
        """Procesar caso fiscal ambiguo usando Nanobot"""
        logger.info(f"🔍 Procesando caso ambiguo: {ambiguity_type}")
        
        # Casos de ambigüedad comunes
        if ambiguity_type == "item_category":
            return self._handle_item_category_ambiguity(invoice_data)
        elif ambiguity_type == "regime_detection":
            return self._handle_regime_detection_ambiguity(invoice_data)
        elif ambiguity_type == "city_detection":
            return self._handle_city_detection_ambiguity(invoice_data)
        elif ambiguity_type == "tax_validation":
            return self._handle_tax_validation_ambiguity(invoice_data)
        else:
            return self._handle_generic_ambiguity(invoice_data, ambiguity_type)
    
    def _handle_item_category_ambiguity(self, invoice_data: InvoiceData) -> Dict:
        """Manejar ambigüedad en categorización de items"""
        logger.info("📦 Resolviendo ambigüedad de categoría de item")
        
        # Crear prompt para Nanobot
        prompt = f"""
        Analiza la siguiente descripción de producto/servicio y determina la categoría fiscal correcta para IVA en Colombia:
        
        Descripción: "{invoice_data.description}"
        Tipo actual: "{invoice_data.item_type}"
        
        Categorías disponibles:
        - pet_food: Alimentos para mascotas (5% IVA)
        - basic_food: Alimentos básicos (0% IVA)
        - electronics: Electrónicos (19% IVA)
        - clothing: Ropa (19% IVA)
        - vehicles_electric: Vehículos eléctricos (5% IVA)
        - general: General (19% IVA)
        
        Responde con el nombre de la categoría correcta y una breve justificación.
        """
        
        # Simular respuesta de Nanobot (en producción usar API real)
        nanobot_response = self._simulate_nanobot_response(prompt, "item_category")
        
        # Actualizar categoría basada en respuesta
        new_category = nanobot_response.get("category", "general")
        invoice_data.item_type = new_category
        
        # Recalcular impuestos
        tax_result = self.tax_calculator.calculate_taxes(invoice_data)
        
        return {
            "original_category": invoice_data.item_type,
            "resolved_category": new_category,
            "justification": nanobot_response.get("justification", ""),
            "tax_result": tax_result,
            "confidence": nanobot_response.get("confidence", 0.8)
        }
    
    def _handle_regime_detection_ambiguity(self, invoice_data: InvoiceData) -> Dict:
        """Manejar ambigüedad en detección de régimen fiscal"""
        logger.info("🏢 Resolviendo ambigüedad de régimen fiscal")
        
        prompt = f"""
        Analiza el NIT del proveedor y determina su régimen fiscal en Colombia:
        
        NIT Proveedor: "{invoice_data.vendor_nit}"
        NIT Comprador: "{invoice_data.buyer_nit}"
        
        Regímenes disponibles:
        - comun: Régimen común (cobra/deduce IVA, aplica retenciones)
        - simplificado: Régimen simplificado (no cobra IVA, no aplica retenciones)
        
        Considera:
        - Longitud del NIT
        - Formato del NIT
        - Tipo de actividad (si se puede inferir)
        
        Responde con el régimen correcto y nivel de confianza.
        """
        
        nanobot_response = self._simulate_nanobot_response(prompt, "regime_detection")
        
        # Actualizar régimen
        new_vendor_regime = nanobot_response.get("vendor_regime", "comun")
        new_buyer_regime = nanobot_response.get("buyer_regime", "comun")
        
        invoice_data.vendor_regime = new_vendor_regime
        invoice_data.buyer_regime = new_buyer_regime
        
        # Recalcular impuestos
        tax_result = self.tax_calculator.calculate_taxes(invoice_data)
        
        return {
            "original_vendor_regime": "unknown",
            "resolved_vendor_regime": new_vendor_regime,
            "original_buyer_regime": "unknown",
            "resolved_buyer_regime": new_buyer_regime,
            "justification": nanobot_response.get("justification", ""),
            "tax_result": tax_result,
            "confidence": nanobot_response.get("confidence", 0.7)
        }
    
    def _handle_city_detection_ambiguity(self, invoice_data: InvoiceData) -> Dict:
        """Manejar ambigüedad en detección de ciudad"""
        logger.info("🏙️ Resolviendo ambigüedad de ciudad")
        
        prompt = f"""
        Analiza la dirección del proveedor y determina la ciudad correcta para cálculo de ICA:
        
        Dirección: "{getattr(invoice_data, 'vendor_address', 'No disponible')}"
        Ciudad actual: "{invoice_data.vendor_city}"
        
        Ciudades disponibles con tasas ICA:
        - bogota: Bogotá (0.414% comercio, 1.104% industria)
        - medellin: Medellín (0.35% comercio, 0.95% industria)
        - cali: Cali (0.38% comercio, 1.02% industria)
        - barranquilla: Barranquilla (0.32% comercio, 0.85% industria)
        
        Responde con la ciudad correcta y justificación.
        """
        
        nanobot_response = self._simulate_nanobot_response(prompt, "city_detection")
        
        # Actualizar ciudad
        new_city = nanobot_response.get("city", "bogota")
        invoice_data.vendor_city = new_city
        
        # Recalcular impuestos
        tax_result = self.tax_calculator.calculate_taxes(invoice_data)
        
        return {
            "original_city": "unknown",
            "resolved_city": new_city,
            "justification": nanobot_response.get("justification", ""),
            "tax_result": tax_result,
            "confidence": nanobot_response.get("confidence", 0.8)
        }
    
    def _handle_tax_validation_ambiguity(self, invoice_data: InvoiceData) -> Dict:
        """Manejar ambigüedad en validación de impuestos"""
        logger.info("✅ Resolviendo ambigüedad de validación fiscal")
        
        # Calcular impuestos
        tax_result = self.tax_calculator.calculate_taxes(invoice_data)
        
        prompt = f"""
        Valida el cálculo de impuestos para esta factura:
        
        Datos de la factura:
        - Base: ${invoice_data.base_amount:,.2f}
        - IVA calculado: ${tax_result.iva_amount:,.2f} ({tax_result.iva_rate*100:.1f}%)
        - IVA en factura: ${invoice_data.iva_amount:,.2f}
        - Total calculado: ${invoice_data.base_amount + tax_result.iva_amount:,.2f}
        - Total en factura: ${invoice_data.total_amount:,.2f}
        
        Estado de compliance: {tax_result.compliance_status}
        
        Verifica:
        1. ¿El IVA calculado coincide con el de la factura?
        2. ¿El total calculado coincide con el de la factura?
        3. ¿Las retenciones aplican correctamente?
        4. ¿Hay algún error en la configuración fiscal?
        
        Responde con el estado de validación y recomendaciones.
        """
        
        nanobot_response = self._simulate_nanobot_response(prompt, "tax_validation")
        
        return {
            "tax_result": tax_result,
            "validation_status": nanobot_response.get("status", "unknown"),
            "recommendations": nanobot_response.get("recommendations", []),
            "confidence": nanobot_response.get("confidence", 0.9)
        }
    
    def _handle_generic_ambiguity(self, invoice_data: InvoiceData, ambiguity_type: str) -> Dict:
        """Manejar ambigüedad genérica"""
        logger.info(f"❓ Resolviendo ambigüedad genérica: {ambiguity_type}")
        
        prompt = f"""
        Analiza el siguiente caso fiscal ambiguo:
        
        Tipo de ambigüedad: {ambiguity_type}
        Datos de la factura:
        - Descripción: "{invoice_data.description}"
        - Proveedor: {invoice_data.vendor_nit}
        - Comprador: {invoice_data.buyer_nit}
        - Base: ${invoice_data.base_amount:,.2f}
        
        Proporciona una resolución y justificación para este caso.
        """
        
        nanobot_response = self._simulate_nanobot_response(prompt, "generic")
        
        return {
            "ambiguity_type": ambiguity_type,
            "resolution": nanobot_response.get("resolution", "No resuelto"),
            "justification": nanobot_response.get("justification", ""),
            "confidence": nanobot_response.get("confidence", 0.5)
        }
    
    def _simulate_nanobot_response(self, prompt: str, case_type: str) -> Dict:
        """Simular respuesta de Nanobot (en producción usar API real)"""
        logger.info(f"🤖 Simulando respuesta de Nanobot para: {case_type}")
        
        # Simulaciones basadas en el tipo de caso
        if case_type == "item_category":
            return {
                "category": "pet_food",
                "justification": "La descripción contiene 'ROYAL CANIN GATO' que claramente indica alimento para mascotas",
                "confidence": 0.95
            }
        elif case_type == "regime_detection":
            return {
                "vendor_regime": "comun",
                "buyer_regime": "comun",
                "justification": "NITs con formato estándar sugieren régimen común",
                "confidence": 0.8
            }
        elif case_type == "city_detection":
            return {
                "city": "bogota",
                "justification": "Dirección con código postal de Bogotá",
                "confidence": 0.9
            }
        elif case_type == "tax_validation":
            return {
                "status": "valid",
                "recommendations": ["Verificar CUFE", "Confirmar régimen fiscal"],
                "confidence": 0.85
            }
        else:
            return {
                "resolution": "Aplicar reglas por defecto",
                "justification": "Caso no específico, usar configuración estándar",
                "confidence": 0.6
            }
    
    def create_tax_decision_tree(self, invoice_data: InvoiceData) -> Dict:
        """Crear árbol de decisiones fiscales"""
        logger.info("🌳 Creando árbol de decisiones fiscales")
        
        decisions = {
            "iva_applicable": invoice_data.buyer_regime == "comun",
            "retefuente_renta_applicable": self._should_apply_retefuente_renta(invoice_data),
            "retefuente_iva_applicable": self._should_apply_retefuente_iva(invoice_data),
            "retefuente_ica_applicable": self._should_apply_retefuente_ica(invoice_data),
            "requires_validation": self._requires_validation(invoice_data)
        }
        
        return decisions
    
    def _should_apply_retefuente_renta(self, invoice_data: InvoiceData) -> bool:
        """Determinar si aplica ReteFuente Renta"""
        return (invoice_data.buyer_regime == "comun" and 
                invoice_data.base_amount > 2 * self.tax_calculator.uvt_2025)
    
    def _should_apply_retefuente_iva(self, invoice_data: InvoiceData) -> bool:
        """Determinar si aplica ReteFuente IVA"""
        return (invoice_data.buyer_regime == "comun" and 
                invoice_data.base_amount > 10 * self.tax_calculator.uvt_2025)
    
    def _should_apply_retefuente_ica(self, invoice_data: InvoiceData) -> bool:
        """Determinar si aplica ReteFuente ICA"""
        return (invoice_data.buyer_regime == "comun" and 
                invoice_data.vendor_city != invoice_data.buyer_city and
                invoice_data.base_amount > 5 * self.tax_calculator.uvt_2025)
    
    def _requires_validation(self, invoice_data: InvoiceData) -> bool:
        """Determinar si requiere validación especial"""
        return (invoice_data.iva_amount > 100000 or  # Montos altos
                invoice_data.base_amount > 5000000 or  # Operaciones grandes
                invoice_data.vendor_regime == "unknown" or  # Régimen desconocido
                invoice_data.buyer_regime == "unknown")

def main():
    """Función principal para testing"""
    integration = TaxNanobotIntegration()
    
    # Crear datos de prueba
    invoice_data = InvoiceData(
        base_amount=203343.81,
        total_amount=213511.00,
        iva_amount=10167.19,
        iva_rate=0.05,
        item_type="unknown",  # Categoría ambigua
        description="ROYAL CANIN GATO GASTROINTESTINAL FIBRE x2KG",
        vendor_nit="52147745-1",
        vendor_regime="unknown",  # Régimen ambiguo
        vendor_city="unknown",  # Ciudad ambigua
        buyer_nit="1136886917",
        buyer_regime="unknown",
        buyer_city="unknown",
        invoice_date="2025-10-10",
        invoice_number="21488"
    )
    
    # Procesar casos ambiguos
    print("🔍 Procesando casos ambiguos...")
    
    # Caso 1: Categoría de item
    result1 = integration.process_ambiguous_tax_case(invoice_data, "item_category")
    print(f"✅ Categoría resuelta: {result1['resolved_category']}")
    
    # Caso 2: Régimen fiscal
    result2 = integration.process_ambiguous_tax_case(invoice_data, "regime_detection")
    print(f"✅ Régimen proveedor: {result2['resolved_vendor_regime']}")
    
    # Caso 3: Ciudad
    result3 = integration.process_ambiguous_tax_case(invoice_data, "city_detection")
    print(f"✅ Ciudad resuelta: {result3['resolved_city']}")
    
    # Crear árbol de decisiones
    decisions = integration.create_tax_decision_tree(invoice_data)
    print(f"\n🌳 Árbol de decisiones: {decisions}")

if __name__ == "__main__":
    main()