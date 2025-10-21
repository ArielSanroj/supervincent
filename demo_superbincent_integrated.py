#!/usr/bin/env python3
"""
Demostración del Sistema Integrado SuperBincent
Muestra el flujo completo: Facturas → Impuestos → Análisis Financiero
"""

import os
import sys
from datetime import datetime
from superbincent_integrated import SuperBincentIntegrated

def demo_integrated_system():
    """Demostración del sistema integrado SuperBincent"""
    print("🚀 DEMOSTRACIÓN SUPERBINCENT - SISTEMA INTEGRADO")
    print("=" * 70)
    print("Sistema: Impuestos + Análisis Financiero Automatizado")
    print("Fecha:", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    print()
    
    # Inicializar sistema
    print("🔧 INICIALIZANDO SISTEMA...")
    system = SuperBincentIntegrated()
    
    # Mostrar estado inicial
    print("\n📊 ESTADO INICIAL DEL SISTEMA:")
    print("-" * 50)
    status = system.get_system_status()
    print(f"✅ Sistema: {status.get('system', 'N/A')}")
    print(f"✅ Versión: {status.get('version', 'N/A')}")
    print(f"📁 Directorio Downloads: {status.get('directories', {}).get('downloads', 'N/A')}")
    print(f"📁 Directorio Reportes: {status.get('directories', {}).get('reports', 'N/A')}")
    print(f"📄 Archivo financiero: {'✅ Detectado' if status.get('financial_files', {}).get('latest_detected') else '❌ No detectado'}")
    print(f"📊 Reportes existentes: {status.get('reports', {}).get('files_count', 0)}")
    
    # Demo 1: Análisis financiero independiente
    print("\n" + "="*70)
    print("📈 DEMO 1: ANÁLISIS FINANCIERO INDEPENDIENTE")
    print("="*70)
    
    print("🔍 Buscando archivo financiero...")
    financial_result = system.run_financial_analysis_only()
    
    if financial_result.get('status') == 'success':
        print("✅ Análisis financiero completado exitosamente")
        
        metrics = financial_result.get('metrics', {})
        print(f"\n📊 MÉTRICAS CALCULADAS:")
        print(f"   📅 Mes: {metrics.get('current_month', 'N/A')}")
        print(f"   💰 Ingresos: ${metrics.get('ingresos', 0):,.0f}")
        print(f"   💸 Gastos: ${metrics.get('gastos_totales', 0):,.0f}")
        
        kpis = metrics.get('kpis', {})
        print(f"\n📈 KPIs PRINCIPALES:")
        print(f"   🏦 Current Ratio: {kpis.get('current_ratio', 0):.2f}")
        print(f"   📊 Margen Neto: {kpis.get('margen_neto', 0):.1f}%")
        print(f"   💎 EBITDA: ${kpis.get('ebitda', 0):,.0f}")
        print(f"   📈 ROE: {kpis.get('roe', 0):.1f}%")
        
        presupuesto = metrics.get('presupuesto_ejecutado', {})
        print(f"\n💰 PRESUPUESTO EJECUTADO:")
        print(f"   📈 Ingresos: {presupuesto.get('ingresos_pct', 0):.1f}%")
        print(f"   📉 Gastos: {presupuesto.get('gastos_pct', 0):.1f}%")
        
        print(f"\n📁 ARCHIVOS GENERADOS: {financial_result.get('files_generated', 0)}")
        print(f"📧 Email enviado: {'Sí' if financial_result.get('email_sent') else 'No'}")
        
    else:
        print(f"❌ Error en análisis financiero: {financial_result.get('error', 'Desconocido')}")
        print("💡 Sugerencia: Asegúrate de tener un archivo 'INFORME DE * APRU- 2025 .xls' en Downloads")
    
    # Demo 2: Procesamiento de facturas (si existen)
    print("\n" + "="*70)
    print("📄 DEMO 2: PROCESAMIENTO DE FACTURAS CON IMPUESTOS")
    print("="*70)
    
    # Buscar facturas de prueba
    test_files = [
        "/Users/arielsanroj/Downloads/testfactura.pdf",
        "/Users/arielsanroj/Downloads/testfactura2.jpg"
    ]
    
    existing_files = [f for f in test_files if os.path.exists(f)]
    
    if existing_files:
        print(f"📄 Procesando {len(existing_files)} factura(s) de prueba...")
        
        for i, file_path in enumerate(existing_files, 1):
            print(f"\n--- FACTURA {i}: {os.path.basename(file_path)} ---")
            
            result = system.process_invoice_with_financial_analysis(file_path)
            
            if result.get('status') == 'success':
                print("✅ Procesamiento exitoso")
                
                summary = result.get('summary', {})
                invoice_summary = summary.get('invoice_summary', {})
                tax_summary = summary.get('tax_summary', {})
                
                print(f"   📄 Número: {invoice_summary.get('numero', 'N/A')}")
                print(f"   📅 Fecha: {invoice_summary.get('fecha', 'N/A')}")
                print(f"   🏢 Proveedor: {invoice_summary.get('proveedor', 'N/A')}")
                print(f"   💰 Total: ${invoice_summary.get('total', 0):,.2f}")
                print(f"   🧾 IVA: ${invoice_summary.get('iva', 0):,.2f}")
                print(f"   📋 Retenciones: ${tax_summary.get('total_retenciones', 0):,.2f}")
                print(f"   ✅ Compliance: {tax_summary.get('compliance_status', 'N/A')}")
                
            else:
                print(f"❌ Error: {result.get('message', 'Desconocido')}")
    else:
        print("⚠️ No se encontraron facturas de prueba en Downloads")
        print("💡 Archivos esperados: testfactura.pdf, testfactura2.jpg")
    
    # Demo 3: Reporte comprensivo
    print("\n" + "="*70)
    print("📋 DEMO 3: REPORTE COMPRENSIVO DEL SISTEMA")
    print("="*70)
    
    print("🔍 Generando reporte comprensivo...")
    comprehensive_report = system.generate_comprehensive_report()
    
    if comprehensive_report.get('status') != 'error':
        print("✅ Reporte comprensivo generado exitosamente")
        
        recommendations = comprehensive_report.get('recommendations', [])
        print(f"\n💡 RECOMENDACIONES ({len(recommendations)}):")
        for i, rec in enumerate(recommendations, 1):
            print(f"   {i}. {rec}")
        
        # Mostrar estado actualizado
        updated_status = comprehensive_report.get('system_status', {})
        print(f"\n📊 ESTADO ACTUALIZADO:")
        print(f"   📄 Archivo financiero: {'✅' if updated_status.get('financial_files', {}).get('latest_detected') else '❌'}")
        print(f"   📊 Reportes: {updated_status.get('reports', {}).get('files_count', 0)} archivos")
        
    else:
        print(f"❌ Error generando reporte comprensivo: {comprehensive_report.get('error', 'Desconocido')}")
    
    # Resumen final
    print("\n" + "="*70)
    print("🎉 RESUMEN DE LA DEMOSTRACIÓN")
    print("="*70)
    
    final_status = system.get_system_status()
    print(f"✅ Sistema operativo: {final_status.get('system', 'N/A')}")
    print(f"📊 Reportes generados: {final_status.get('reports', {}).get('files_count', 0)}")
    print(f"📁 Directorio reportes: {final_status.get('directories', {}).get('reports', 'N/A')}")
    
    print("\n🚀 FUNCIONALIDADES DEMOSTRADAS:")
    print("   ✅ Análisis financiero automático")
    print("   ✅ Cálculo de impuestos colombianos 2025")
    print("   ✅ Procesamiento de facturas (PDF, JPG)")
    print("   ✅ Generación de reportes (Excel, Word, PNG)")
    print("   ✅ Envío automático por email")
    print("   ✅ KPIs y métricas financieras")
    print("   ✅ Compliance fiscal automático")
    
    print("\n💡 PRÓXIMOS PASOS:")
    print("   1. Configurar credenciales de email en financial_analysis.py")
    print("   2. Asegurar archivo financiero mensual en Downloads")
    print("   3. Programar ejecución automática mensual")
    print("   4. Configurar alertas para KPIs críticos")
    
    print("\n🏆 ¡SuperBincent Sistema Integrado - Demostración Completada! 🏆")

def demo_individual_components():
    """Demostración de componentes individuales"""
    print("\n" + "="*70)
    print("🔧 DEMO COMPONENTES INDIVIDUALES")
    print("="*70)
    
    system = SuperBincentIntegrated()
    
    # Demo Tax Calculator
    print("\n🧮 DEMO: CALCULADOR DE IMPUESTOS")
    print("-" * 40)
    
    from tax_calculator import ColombianTaxCalculator, InvoiceData
    
    calculator = ColombianTaxCalculator()
    
    # Datos de ejemplo
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
    
    tax_result = calculator.calculate_taxes(invoice_data)
    print(calculator.get_tax_summary(tax_result))
    
    # Demo Financial Analyzer
    print("\n📊 DEMO: ANALIZADOR FINANCIERO")
    print("-" * 40)
    
    analyzer = system.financial_analyzer
    print(f"📁 Directorio reportes: {analyzer.reports_dir}")
    print(f"📄 Archivo financiero detectado: {'Sí' if analyzer.detect_latest_financial_file() else 'No'}")

if __name__ == "__main__":
    # Ejecutar demostración principal
    demo_integrated_system()
    
    # Ejecutar demostración de componentes
    demo_individual_components()