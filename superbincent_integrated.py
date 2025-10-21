#!/usr/bin/env python3
"""
SuperBincent - Sistema Integrado de Impuestos y Análisis Financiero
Combina procesamiento de facturas, cálculo de impuestos y análisis financiero
"""

import os
import sys
import logging
from datetime import datetime
from typing import Dict, Optional
from pathlib import Path

# Importar módulos del sistema
from tax_calculator import ColombianTaxCalculator, InvoiceData
from invoice_processor_with_taxes import TaxIntegratedInvoiceProcessor
from financial_analysis import FinancialAnalyzer

class SuperBincentIntegrated:
    """Sistema integrado SuperBincent - Impuestos + Análisis Financiero"""
    
    def __init__(self, downloads_dir: str = None):
        self.downloads_dir = downloads_dir or os.path.expanduser("~/Downloads")
        self.logger = logging.getLogger(__name__)
        
        # Inicializar componentes
        self.tax_processor = TaxIntegratedInvoiceProcessor()
        self.financial_analyzer = FinancialAnalyzer(self.downloads_dir)
        
        # Configurar logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        self.logger.info("🚀 SuperBincent Sistema Integrado inicializado")
    
    def process_invoice_with_financial_analysis(self, file_path: str) -> Dict:
        """Procesar factura con impuestos y actualizar análisis financiero"""
        try:
            self.logger.info(f"📄 Procesando factura: {file_path}")
            
            # 1. Procesar factura con impuestos
            tax_result = self.tax_processor.process_invoice_with_taxes(file_path)
            
            if not tax_result:
                return {
                    'status': 'error',
                    'message': 'Error procesando factura con impuestos',
                    'tax_result': None,
                    'financial_update': None
                }
            
            # 2. Actualizar análisis financiero
            financial_update = self.financial_analyzer.update_from_entry(tax_result['invoice_data'])
            
            # 3. Consolidar resultados
            result = {
                'status': 'success',
                'timestamp': datetime.now().isoformat(),
                'file_processed': file_path,
                'tax_result': tax_result,
                'financial_update': financial_update,
                'summary': self._create_summary(tax_result, financial_update)
            }
            
            self.logger.info("✅ Procesamiento integrado completado exitosamente")
            return result
            
        except Exception as e:
            self.logger.error(f"❌ Error en procesamiento integrado: {e}")
            return {
                'status': 'error',
                'message': str(e),
                'tax_result': None,
                'financial_update': None
            }
    
    def _create_summary(self, tax_result: Dict, financial_update: Dict) -> Dict:
        """Crear resumen consolidado"""
        try:
            invoice_data = tax_result.get('invoice_data', {})
            tax_calc = tax_result.get('tax_calculation', {})
            financial_metrics = financial_update.get('metrics', {})
            
            summary = {
                'invoice_summary': {
                    'numero': invoice_data.get('numero_factura', 'N/A'),
                    'fecha': invoice_data.get('fecha', 'N/A'),
                    'proveedor': invoice_data.get('proveedor', 'N/A'),
                    'total': invoice_data.get('total', 0),
                    'iva': invoice_data.get('impuestos', 0)
                },
                'tax_summary': {
                    'iva_calculado': tax_calc.get('iva_amount', 0),
                    'retefuente_renta': tax_calc.get('retefuente_renta', 0),
                    'retefuente_iva': tax_calc.get('retefuente_iva', 0),
                    'retefuente_ica': tax_calc.get('retefuente_ica', 0),
                    'total_retenciones': tax_calc.get('total_withholdings', 0),
                    'compliance_status': tax_calc.get('compliance_status', 'UNKNOWN')
                },
                'financial_summary': {
                    'current_month': financial_metrics.get('current_month', 'N/A'),
                    'ingresos_totales': financial_metrics.get('ingresos', 0),
                    'gastos_totales': financial_metrics.get('gastos_totales', 0),
                    'current_ratio': financial_metrics.get('kpis', {}).get('current_ratio', 0),
                    'ebitda': financial_metrics.get('kpis', {}).get('ebitda', 0),
                    'margen_neto': financial_metrics.get('kpis', {}).get('margen_neto', 0)
                }
            }
            
            return summary
            
        except Exception as e:
            self.logger.error(f"Error creando resumen: {e}")
            return {}
    
    def run_financial_analysis_only(self) -> Dict:
        """Ejecutar solo análisis financiero (sin procesar facturas)"""
        try:
            self.logger.info("📊 Ejecutando análisis financiero independiente")
            
            result = self.financial_analyzer.run_full_analysis()
            
            if result['status'] == 'success':
                self.logger.info("✅ Análisis financiero completado")
            else:
                self.logger.error(f"❌ Error en análisis financiero: {result['error']}")
            
            return result
            
        except Exception as e:
            self.logger.error(f"❌ Error ejecutando análisis financiero: {e}")
            return {'status': 'error', 'error': str(e)}
    
    def process_multiple_invoices(self, file_paths: list) -> Dict:
        """Procesar múltiples facturas y actualizar análisis financiero"""
        try:
            self.logger.info(f"📄 Procesando {len(file_paths)} facturas")
            
            results = []
            successful = 0
            failed = 0
            
            for file_path in file_paths:
                result = self.process_invoice_with_financial_analysis(file_path)
                results.append(result)
                
                if result['status'] == 'success':
                    successful += 1
                else:
                    failed += 1
            
            # Resumen final
            summary = {
                'status': 'completed',
                'total_processed': len(file_paths),
                'successful': successful,
                'failed': failed,
                'results': results,
                'timestamp': datetime.now().isoformat()
            }
            
            self.logger.info(f"✅ Procesamiento masivo completado: {successful} exitosos, {failed} fallidos")
            return summary
            
        except Exception as e:
            self.logger.error(f"❌ Error en procesamiento masivo: {e}")
            return {'status': 'error', 'error': str(e)}
    
    def get_system_status(self) -> Dict:
        """Obtener estado del sistema"""
        try:
            # Verificar archivos financieros disponibles
            financial_files = self.financial_analyzer.detect_latest_financial_file()
            
            # Verificar directorio de reportes
            reports_dir = self.financial_analyzer.reports_dir
            reports_count = len([f for f in os.listdir(reports_dir) if os.path.isfile(os.path.join(reports_dir, f))]) if os.path.exists(reports_dir) else 0
            
            status = {
                'system': 'SuperBincent Integrated',
                'version': '1.0.0',
                'timestamp': datetime.now().isoformat(),
                'components': {
                    'tax_processor': 'active',
                    'financial_analyzer': 'active'
                },
                'financial_files': {
                    'latest_detected': financial_files is not None,
                    'latest_file': financial_files
                },
                'reports': {
                    'directory': reports_dir,
                    'files_count': reports_count
                },
                'directories': {
                    'downloads': self.downloads_dir,
                    'reports': reports_dir
                }
            }
            
            return status
            
        except Exception as e:
            self.logger.error(f"Error obteniendo estado del sistema: {e}")
            return {'status': 'error', 'error': str(e)}
    
    def generate_comprehensive_report(self) -> Dict:
        """Generar reporte comprensivo del sistema"""
        try:
            self.logger.info("📊 Generando reporte comprensivo")
            
            # Obtener estado del sistema
            system_status = self.get_system_status()
            
            # Ejecutar análisis financiero
            financial_analysis = self.run_financial_analysis_only()
            
            # Crear reporte comprensivo
            comprehensive_report = {
                'report_type': 'comprehensive',
                'timestamp': datetime.now().isoformat(),
                'system_status': system_status,
                'financial_analysis': financial_analysis,
                'recommendations': self._generate_recommendations(system_status, financial_analysis)
            }
            
            self.logger.info("✅ Reporte comprensivo generado")
            return comprehensive_report
            
        except Exception as e:
            self.logger.error(f"❌ Error generando reporte comprensivo: {e}")
            return {'status': 'error', 'error': str(e)}
    
    def _generate_recommendations(self, system_status: Dict, financial_analysis: Dict) -> list:
        """Generar recomendaciones basadas en el análisis"""
        recommendations = []
        
        try:
            # Recomendaciones basadas en estado del sistema
            if not system_status.get('financial_files', {}).get('latest_detected', False):
                recommendations.append("⚠️ No se detectó archivo financiero reciente. Verificar que existe un archivo 'INFORME DE * APRU- 2025 .xls' en Downloads")
            
            # Recomendaciones basadas en análisis financiero
            if financial_analysis.get('status') == 'success':
                metrics = financial_analysis.get('metrics', {})
                kpis = metrics.get('kpis', {})
                
                # Current Ratio
                current_ratio = kpis.get('current_ratio', 0)
                if current_ratio < 1.5:
                    recommendations.append("🔴 Current Ratio bajo (< 1.5). Revisar liquidez inmediatamente")
                elif current_ratio < 2.0:
                    recommendations.append("🟡 Current Ratio moderado (< 2.0). Monitorear liquidez")
                
                # Margen neto
                margen_neto = kpis.get('margen_neto', 0)
                if margen_neto < 5:
                    recommendations.append("🔴 Margen neto bajo (< 5%). Revisar costos y precios")
                elif margen_neto < 10:
                    recommendations.append("🟡 Margen neto moderado (< 10%). Optimizar operaciones")
                
                # Presupuesto ejecutado
                presupuesto = metrics.get('presupuesto_ejecutado', {})
                gastos_pct = presupuesto.get('gastos_pct', 0)
                if gastos_pct > 120:
                    recommendations.append("🔴 Gastos exceden presupuesto (> 120%). Control de gastos urgente")
                elif gastos_pct > 100:
                    recommendations.append("🟡 Gastos en límite presupuestario (> 100%). Monitorear gastos")
            
            # Recomendaciones generales
            recommendations.extend([
                "📊 Revisar reportes generados en directorio de reportes",
                "📧 Verificar configuración de email para envío automático",
                "🔄 Programar análisis financiero mensual automático",
                "📈 Considerar implementar alertas automáticas para KPIs críticos"
            ])
            
        except Exception as e:
            self.logger.error(f"Error generando recomendaciones: {e}")
            recommendations.append("❌ Error generando recomendaciones personalizadas")
        
        return recommendations

def main():
    """Función principal para demostrar el sistema integrado"""
    print("🚀 SuperBincent - Sistema Integrado de Impuestos y Análisis Financiero")
    print("=" * 80)
    
    # Crear sistema integrado
    system = SuperBincentIntegrated()
    
    # Mostrar estado del sistema
    print("\n📊 ESTADO DEL SISTEMA:")
    print("-" * 40)
    status = system.get_system_status()
    print(f"Sistema: {status.get('system', 'N/A')}")
    print(f"Versión: {status.get('version', 'N/A')}")
    print(f"Archivo financiero detectado: {'Sí' if status.get('financial_files', {}).get('latest_detected') else 'No'}")
    print(f"Reportes generados: {status.get('reports', {}).get('files_count', 0)}")
    
    # Ejecutar análisis financiero
    print("\n📈 EJECUTANDO ANÁLISIS FINANCIERO:")
    print("-" * 40)
    financial_result = system.run_financial_analysis_only()
    
    if financial_result.get('status') == 'success':
        print("✅ Análisis financiero completado exitosamente")
        metrics = financial_result.get('metrics', {})
        print(f"Mes analizado: {metrics.get('current_month', 'N/A')}")
        print(f"Ingresos: ${metrics.get('ingresos', 0):,.0f}")
        print(f"Gastos: ${metrics.get('gastos_totales', 0):,.0f}")
        print(f"Archivos generados: {financial_result.get('files_generated', 0)}")
    else:
        print(f"❌ Error en análisis financiero: {financial_result.get('error', 'Desconocido')}")
    
    # Generar reporte comprensivo
    print("\n📋 GENERANDO REPORTE COMPRENSIVO:")
    print("-" * 40)
    comprehensive_report = system.generate_comprehensive_report()
    
    if comprehensive_report.get('status') != 'error':
        recommendations = comprehensive_report.get('recommendations', [])
        print(f"Recomendaciones generadas: {len(recommendations)}")
        for i, rec in enumerate(recommendations[:5], 1):  # Mostrar primeras 5
            print(f"  {i}. {rec}")
    else:
        print(f"❌ Error generando reporte comprensivo: {comprehensive_report.get('error', 'Desconocido')}")
    
    print("\n🎉 SuperBincent Sistema Integrado - Operación Completada")
    print("=" * 80)

if __name__ == "__main__":
    main()