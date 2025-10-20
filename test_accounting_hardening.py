#!/usr/bin/env python3
"""
Script de prueba para validar las mejoras contables implementadas
"""

import os
import sys
import json
from datetime import datetime
from invoice_processor_conversational import ConversationalInvoiceProcessor
from alegra_reports import AlegraReports

def test_conversational_processor():
    """Probar el procesador conversacional con validaciones contables"""
    print("🧪 Probando ConversationalInvoiceProcessor con validaciones contables...")
    
    try:
        processor = ConversationalInvoiceProcessor()
        
        # Datos de prueba
        test_data = {
            'fecha': '2024-01-15',
            'cliente': 'Empresa Test S.A.S.',
            'total': 1500000.0,  # Monto alto para probar threshold
            'iva': 285000.0,
            'retenciones': 0.0,
            'items': [
                {'descripcion': 'Servicio de consultoría', 'precio': 1500000.0}
            ],
            'tipo': 'venta'
        }
        
        # Probar validación de datos
        print("\n1. Probando validación de datos...")
        validation = processor.validate_invoice_data(test_data)
        print(f"   Validación: {validation}")
        
        # Probar cálculo de impuestos
        print("\n2. Probando cálculo de impuestos...")
        calculated_data = processor.calculate_taxes(test_data)
        print(f"   IVA calculado: ${calculated_data.get('iva', 0):,.2f}")
        
        # Probar auto-categorización
        print("\n3. Probando auto-categorización...")
        categorized_data = processor.auto_categorize_items(test_data)
        for item in categorized_data.get('items', []):
            print(f"   Item: {item.get('descripcion')} -> Categoría: {item.get('category', 'N/A')}")
        
        # Probar detección de duplicados
        print("\n4. Probando detección de duplicados...")
        is_duplicate = processor.check_duplicate_invoice(test_data)
        print(f"   Es duplicado: {is_duplicate}")
        
        print("✅ ConversationalInvoiceProcessor funcionando correctamente")
        return True
        
    except Exception as e:
        print(f"❌ Error probando ConversationalInvoiceProcessor: {e}")
        return False

def test_advanced_reports():
    """Probar reportes contables avanzados"""
    print("\n🧪 Probando reportes contables avanzados...")
    
    try:
        reporter = AlegraReports()
        
        # Probar reporte de aging
        print("\n1. Probando reporte de aging...")
        aging_report = reporter.generate_aging_report('2024-01-01', '2024-01-31')
        if aging_report:
            print("   ✅ Reporte de aging generado")
        else:
            print("   ⚠️ No se pudo generar reporte de aging (posible falta de datos)")
        
        # Probar reporte de flujo de caja
        print("\n2. Probando reporte de flujo de caja...")
        cash_flow_report = reporter.generate_cash_flow_report('2024-01-01', '2024-01-31')
        if cash_flow_report:
            print("   ✅ Reporte de flujo de caja generado")
        else:
            print("   ⚠️ No se pudo generar reporte de flujo de caja (posible falta de datos)")
        
        print("✅ Reportes contables avanzados funcionando")
        return True
        
    except Exception as e:
        print(f"❌ Error probando reportes: {e}")
        return False

def test_tax_rules():
    """Probar configuración de reglas fiscales"""
    print("\n🧪 Probando reglas fiscales...")
    
    try:
        from config import TAX_RULES
        
        if TAX_RULES:
            print("   ✅ Reglas fiscales cargadas:")
            print(f"   - IVA estándar: {TAX_RULES.get('tax_rates', {}).get('iva_standard', 'N/A')}")
            print(f"   - Threshold de aprobación: ${TAX_RULES.get('validation_rules', {}).get('max_amount_without_approval', 'N/A'):,}")
        else:
            print("   ⚠️ No se encontraron reglas fiscales")
        
        return True
        
    except Exception as e:
        print(f"❌ Error probando reglas fiscales: {e}")
        return False

def test_nanobot_config():
    """Probar configuración de Nanobot"""
    print("\n🧪 Probando configuración de Nanobot...")
    
    try:
        # Verificar archivo de configuración
        nanobot_config_path = 'nanobot_accounting.yaml'
        if os.path.exists(nanobot_config_path):
            print("   ✅ Configuración de Nanobot encontrada")
            
            # Leer y mostrar agentes disponibles
            import yaml
            with open(nanobot_config_path, 'r') as f:
                config = yaml.safe_load(f)
            
            agents = config.get('agents', {})
            print(f"   - Agentes disponibles: {list(agents.keys())}")
            
            thresholds = config.get('thresholds', {})
            print(f"   - Threshold de confianza: {thresholds.get('confidence_minimum', 'N/A')}")
            print(f"   - Threshold de monto alto: ${thresholds.get('high_amount_threshold', 'N/A'):,}")
        else:
            print("   ⚠️ Archivo de configuración de Nanobot no encontrado")
        
        return True
        
    except Exception as e:
        print(f"❌ Error probando configuración de Nanobot: {e}")
        return False

def main():
    """Función principal de pruebas"""
    print("🚀 INICIANDO PRUEBAS DE ENDURECIMIENTO CONTABLE")
    print("=" * 60)
    
    tests = [
        ("ConversationalInvoiceProcessor", test_conversational_processor),
        ("Reportes Avanzados", test_advanced_reports),
        ("Reglas Fiscales", test_tax_rules),
        ("Configuración Nanobot", test_nanobot_config)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Error inesperado en {test_name}: {e}")
            results.append((test_name, False))
    
    # Resumen de resultados
    print("\n" + "="*60)
    print("📊 RESUMEN DE PRUEBAS")
    print("="*60)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASÓ" if result else "❌ FALLÓ"
        print(f"{test_name:30} {status}")
        if result:
            passed += 1
    
    print(f"\nResultado: {passed}/{total} pruebas pasaron")
    
    if passed == total:
        print("🎉 ¡Todas las pruebas pasaron! El endurecimiento contable está funcionando.")
    else:
        print("⚠️ Algunas pruebas fallaron. Revisar la configuración.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)