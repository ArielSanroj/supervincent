#!/usr/bin/env python3
"""
Procesador de Facturas con Cálculo de Impuestos Colombianos 2025
Integra el sistema de impuestos con el procesamiento de facturas
"""

import os
import sys
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Optional

# Importar módulos existentes
from tax_calculator import ColombianTaxCalculator, InvoiceData, create_invoice_data_from_pdf
from invoice_processor_enhanced import InvoiceProcessor

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TaxIntegratedInvoiceProcessor(InvoiceProcessor):
    """Procesador de facturas con integración completa de impuestos colombianos"""
    
    def __init__(self):
        """Inicializar procesador con calculador de impuestos"""
        super().__init__()
        self.tax_calculator = ColombianTaxCalculator()
        logger.info("🧮 Procesador con impuestos inicializado")
    
    def process_invoice_with_taxes(self, file_path: str) -> Dict:
        """Procesar factura con cálculo completo de impuestos"""
        logger.info(f"🚀 Procesando factura con impuestos: {file_path}")
        
        # 1. Extraer datos básicos de la factura
        if file_path.lower().endswith('.pdf'):
            invoice_data = self.extract_data_from_pdf(file_path)
        elif file_path.lower().endswith(('.jpg', '.jpeg', '.png')):
            invoice_data = self.extract_data_from_image(file_path)
        else:
            raise ValueError(f"Formato de archivo no soportado: {file_path}")
        
        if not invoice_data:
            logger.error("❌ No se pudieron extraer datos de la factura")
            return None
        
        # 2. Enriquecer datos con información fiscal
        enriched_data = self._enrich_invoice_data(invoice_data)
        
        # 3. Crear InvoiceData para cálculo de impuestos
        tax_invoice_data = create_invoice_data_from_pdf(enriched_data)
        
        # 4. Calcular impuestos
        tax_result = self.tax_calculator.calculate_taxes(tax_invoice_data)
        
        # 5. Mostrar resumen fiscal
        logger.info(self.tax_calculator.get_tax_summary(tax_result))
        
        # 6. Crear payload para Alegra con impuestos
        alegra_payload = self._create_alegra_payload_with_taxes(enriched_data, tax_result)
        
        # 7. Crear factura en Alegra
        alegra_result = self._create_invoice_in_alegra_with_taxes(alegra_payload)
        
        # 8. Preparar resultado completo
        result = {
            "invoice_data": enriched_data,
            "tax_calculation": {
                "iva_amount": tax_result.iva_amount,
                "iva_rate": tax_result.iva_rate,
                "retefuente_renta": tax_result.retefuente_renta,
                "retefuente_iva": tax_result.retefuente_iva,
                "retefuente_ica": tax_result.retefuente_ica,
                "total_withholdings": tax_result.total_withholdings,
                "net_amount": tax_result.net_amount,
                "compliance_status": tax_result.compliance_status
            },
            "alegra_payload": alegra_payload,
            "alegra_result": alegra_result,
            "processing_timestamp": datetime.now().isoformat()
        }
        
        return result
    
    def _enrich_invoice_data(self, invoice_data: Dict) -> Dict:
        """Enriquecer datos de factura con información fiscal"""
        logger.info("🔍 Enriqueciendo datos con información fiscal")
        
        # Detectar régimen fiscal del proveedor (simulado - en producción usar API DIAN)
        vendor_nit = invoice_data.get('proveedor_nit', '')
        vendor_regime = self._detect_vendor_regime(vendor_nit)
        
        # Detectar régimen fiscal del comprador
        buyer_nit = invoice_data.get('comprador_nit', '')
        buyer_regime = self._detect_buyer_regime(buyer_nit)
        
        # Detectar ciudades (simulado - en producción usar geocoding)
        vendor_city = self._detect_city_from_address(invoice_data.get('proveedor_direccion', ''))
        buyer_city = self._detect_city_from_address(invoice_data.get('comprador_direccion', ''))
        
        # Enriquecer datos
        enriched_data = invoice_data.copy()
        enriched_data.update({
            'proveedor_regime': vendor_regime,
            'proveedor_ciudad': vendor_city,
            'comprador_regime': buyer_regime,
            'comprador_ciudad': buyer_city,
            'fiscal_enrichment': True,
            'enrichment_timestamp': datetime.now().isoformat()
        })
        
        logger.info(f"✅ Datos enriquecidos - Proveedor: {vendor_regime}, Comprador: {buyer_regime}")
        return enriched_data
    
    def _detect_vendor_regime(self, nit: str) -> str:
        """Detectar régimen fiscal del proveedor"""
        if not nit:
            return "simplificado"
        
        # Simulación - en producción usar API DIAN
        # Por ahora, asumir que NITs con más de 8 dígitos son régimen común
        if len(nit.replace('-', '').replace('.', '')) > 8:
            return "comun"
        else:
            return "simplificado"
    
    def _detect_buyer_regime(self, nit: str) -> str:
        """Detectar régimen fiscal del comprador"""
        if not nit:
            return "simplificado"
        
        # Simulación - en producción usar API DIAN
        if len(nit.replace('-', '').replace('.', '')) > 8:
            return "comun"
        else:
            return "simplificado"
    
    def _detect_city_from_address(self, address: str) -> str:
        """Detectar ciudad desde dirección"""
        if not address:
            return "bogota"
        
        address_lower = address.lower()
        
        if any(city in address_lower for city in ['bogotá', 'bogota', 'dc']):
            return "bogota"
        elif any(city in address_lower for city in ['medellín', 'medellin', 'antioquia']):
            return "medellin"
        elif any(city in address_lower for city in ['cali', 'valle', 'cauca']):
            return "cali"
        elif any(city in address_lower for city in ['barranquilla', 'atlántico', 'atlantico']):
            return "barranquilla"
        else:
            return "bogota"  # Default
    
    def _create_alegra_payload_with_taxes(self, invoice_data: Dict, tax_result) -> Dict:
        """Crear payload para Alegra incluyendo información fiscal"""
        logger.info("📤 Creando payload para Alegra con impuestos")
        
        # Payload base
        payload = {
            "date": invoice_data.get('fecha', datetime.now().strftime('%Y-%m-%d')),
            "dueDate": self._calculate_due_date(invoice_data.get('fecha')),
            "client": {
                "name": invoice_data.get('cliente', 'Cliente desde PDF'),
                "identification": invoice_data.get('comprador_nit', '')
            },
            "items": self._format_items_for_alegra(invoice_data.get('items', [])),
            "observations": f"Factura procesada con cálculo de impuestos - {datetime.now().strftime('%Y-%m-%d %H:%M')}",
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
                "description": "Retención en la fuente por renta"
            })
        
        if tax_result.retefuente_iva > 0:
            payload["withholdings"].append({
                "type": "iva",
                "amount": tax_result.retefuente_iva,
                "description": "Retención en la fuente por IVA"
            })
        
        if tax_result.retefuente_ica > 0:
            payload["withholdings"].append({
                "type": "ica",
                "amount": tax_result.retefuente_ica,
                "description": "Retención en la fuente por ICA"
            })
        
        # Agregar información fiscal adicional
        payload["fiscal_info"] = {
            "vendor_regime": invoice_data.get('proveedor_regime'),
            "buyer_regime": invoice_data.get('comprador_regime'),
            "vendor_city": invoice_data.get('proveedor_ciudad'),
            "buyer_city": invoice_data.get('comprador_ciudad'),
            "compliance_status": tax_result.compliance_status,
            "net_amount": tax_result.net_amount
        }
        
        return payload
    
    def _format_items_for_alegra(self, items: list) -> list:
        """Formatear items para Alegra"""
        alegra_items = []
        
        for item in items:
            alegra_items.append({
                "name": item.get('descripcion', 'Producto no identificado'),
                "quantity": item.get('cantidad', 1),
                "price": item.get('precio', 0)
            })
        
        return alegra_items
    
    def _calculate_due_date(self, invoice_date: str) -> str:
        """Calcular fecha de vencimiento (30 días)"""
        try:
            if isinstance(invoice_date, str):
                if '-' in invoice_date:
                    if len(invoice_date.split('-')[0]) == 4:  # YYYY-MM-DD
                        date_obj = datetime.strptime(invoice_date, '%Y-%m-%d')
                    else:  # DD-MM-YYYY
                        date_obj = datetime.strptime(invoice_date, '%d-%m-%Y')
                else:
                    date_obj = datetime.now()
            else:
                date_obj = datetime.now()
            
            due_date = date_obj + timedelta(days=30)
            return due_date.strftime('%Y-%m-%d')
        except:
            return (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')
    
    def _create_invoice_in_alegra_with_taxes(self, payload: Dict) -> Optional[Dict]:
        """Crear factura en Alegra con información fiscal"""
        logger.info("🏢 Creando factura en Alegra con impuestos")
        
        try:
            # Usar el método existente de la clase padre
            response = requests.post(
                f'{self.base_url}/invoices',
                json=payload,
                headers=self.get_auth_headers(),
                timeout=30
            )
            
            if response.status_code == 201:
                result = response.json()
                logger.info(f"✅ Factura creada en Alegra con impuestos: {result.get('id')}")
                return result
            else:
                logger.error(f"❌ Error creando factura en Alegra: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Error en API Alegra: {e}")
            return None
    
    def generate_tax_report(self, processing_results: list) -> Dict:
        """Generar reporte fiscal consolidado"""
        logger.info("📊 Generando reporte fiscal consolidado")
        
        total_iva = sum(r.get('tax_calculation', {}).get('iva_amount', 0) for r in processing_results)
        total_retefuente = sum(r.get('tax_calculation', {}).get('total_withholdings', 0) for r in processing_results)
        total_net = sum(r.get('tax_calculation', {}).get('net_amount', 0) for r in processing_results)
        
        report = {
            "report_date": datetime.now().isoformat(),
            "total_invoices": len(processing_results),
            "summary": {
                "total_iva": total_iva,
                "total_withholdings": total_retefuente,
                "total_net_amount": total_net,
                "average_iva_rate": total_iva / sum(r.get('invoice_data', {}).get('subtotal', 0) for r in processing_results) if processing_results else 0
            },
            "breakdown": {
                "retefuente_renta": sum(r.get('tax_calculation', {}).get('retefuente_renta', 0) for r in processing_results),
                "retefuente_iva": sum(r.get('tax_calculation', {}).get('retefuente_iva', 0) for r in processing_results),
                "retefuente_ica": sum(r.get('tax_calculation', {}).get('retefuente_ica', 0) for r in processing_results)
            },
            "compliance": {
                "compliant_invoices": len([r for r in processing_results if r.get('tax_calculation', {}).get('compliance_status') == 'COMPLIANT']),
                "warning_invoices": len([r for r in processing_results if 'WARNING' in r.get('tax_calculation', {}).get('compliance_status', '')])
            }
        }
        
        return report

def main():
    """Función principal para testing"""
    processor = TaxIntegratedInvoiceProcessor()
    
    # Procesar factura de ejemplo
    test_files = [
        "/Users/arielsanroj/Downloads/testfactura.pdf",
        "/Users/arielsanroj/Downloads/testfactura2.jpg"
    ]
    
    results = []
    
    for file_path in test_files:
        if os.path.exists(file_path):
            print(f"\n🚀 Procesando: {file_path}")
            result = processor.process_invoice_with_taxes(file_path)
            if result:
                results.append(result)
                print("✅ Procesamiento completado")
            else:
                print("❌ Error en procesamiento")
        else:
            print(f"❌ Archivo no encontrado: {file_path}")
    
    # Generar reporte consolidado
    if results:
        report = processor.generate_tax_report(results)
        print(f"\n📊 REPORTE FISCAL CONSOLIDADO")
        print(f"Total facturas: {report['total_invoices']}")
        print(f"Total IVA: ${report['summary']['total_iva']:,.2f}")
        print(f"Total retenciones: ${report['summary']['total_withholdings']:,.2f}")
        print(f"Total neto: ${report['summary']['total_net_amount']:,.2f}")
        print(f"Facturas compliant: {report['compliance']['compliant_invoices']}")

if __name__ == "__main__":
    main()