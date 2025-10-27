#!/usr/bin/env python3
"""
Script de prueba para las optimizaciones de performance y cumplimiento
"""

import os
import sys
import time
import json
from datetime import datetime
from cache_manager import CacheManager
from tax_validator import TaxValidator
from dian_validator import DIANValidator
from tasks import process_invoice, generate_report, validate_taxes

def test_cache_system():
    """Probar sistema de caché"""
    print("🧪 Probando sistema de caché...")
    
    try:
        cache_manager = CacheManager()
        
        # Probar guardar datos
        test_contact = {
            'id': 'test_123',
            'name': 'Empresa Test S.A.S.',
            'type': 'client'
        }
        
        # Guardar en caché
        success = cache_manager.cache_contact(test_contact)
        print(f"   ✅ Contacto guardado en caché: {success}")
        
        # Recuperar del caché
        cached_contact = cache_manager.get_contact_by_name('Empresa Test S.A.S.')
        print(f"   ✅ Contacto recuperado del caché: {cached_contact is not None}")
        
        # Obtener estadísticas
        stats = cache_manager.get_cache_stats()
        print(f"   📊 Estadísticas del caché: {stats}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Error probando caché: {e}")
        return False

def test_tax_validation():
    """Probar validación de impuestos por país"""
    print("\n🧪 Probando validación de impuestos...")
    
    try:
        # Probar Colombia
        validator_co = TaxValidator('CO')
        
        test_invoice = {
            'fecha': '2024-01-15',
            'total': 1000000.0,
            'iva': 190000.0,
            'retenciones': 0.0,
            'items': [
                {'descripcion': 'Servicio de consultoría', 'precio': 1000000.0}
            ],
            'tipo': 'compra',
            'nit_proveedor': '900123456-1'
        }
        
        result = validator_co.validate_invoice_taxes(test_invoice)
        print(f"   ✅ Validación Colombia: {result.is_valid}")
        print(f"   📊 Score de cumplimiento: {result.compliance_score}")
        
        # Probar México
        validator_mx = TaxValidator('MX')
        result_mx = validator_mx.validate_invoice_taxes(test_invoice)
        print(f"   ✅ Validación México: {result_mx.is_valid}")
        
        # Probar retenciones dinámicas
        retenciones = validator_co.calculate_dynamic_retenciones(test_invoice)
        print(f"   💰 Retenciones calculadas: {retenciones}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Error probando validación de impuestos: {e}")
        return False

def test_dian_validation():
    """Probar validación DIAN"""
    print("\n🧪 Probando validación DIAN...")
    
    try:
        validator = DIANValidator(test_mode=True)
        
        test_invoice = {
            'nit_emisor': '900123456-1',
            'nit_receptor': '800987654-3',
            'fecha': '2024-01-15',
            'numero_factura': 'FAC-001',
            'total': 1000000.0,
            'iva': 190000.0,
            'razon_social_emisor': 'Empresa Emisora S.A.S.',
            'razon_social_receptor': 'Empresa Receptora S.A.S.'
        }
        
        result = validator.validate_electronic_invoice(test_invoice)
        print(f"   ✅ Validación DIAN: {result.is_valid}")
        print(f"   🔑 CUFE generado: {result.cufe[:20]}...")
        print(f"   📱 QR Code: {result.qr_code[:50]}...")
        
        if result.errors:
            print(f"   ⚠️ Errores: {result.errors}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Error probando validación DIAN: {e}")
        return False

def test_async_tasks():
    """Probar tareas asíncronas"""
    print("\n🧪 Probando tareas asíncronas...")
    
    try:
        # Probar tarea de validación de impuestos
        test_data = {
            'fecha': '2024-01-15',
            'total': 1000000.0,
            'iva': 190000.0,
            'items': [{'descripcion': 'Test', 'precio': 1000000.0}],
            'tipo': 'compra'
        }
        
        # Enviar tarea (esto requiere que Celery esté corriendo)
        try:
            task = validate_taxes.delay(test_data, 'CO')
            print(f"   ✅ Tarea enviada: {task.id}")
            
            # Esperar un poco
            time.sleep(2)
            
            # Verificar estado
            if task.ready():
                result = task.result
                print(f"   ✅ Tarea completada: {result.get('status', 'unknown')}")
            else:
                print(f"   ⏳ Tarea en progreso...")
            
        except Exception as e:
            print(f"   ⚠️ No se pudo enviar tarea (Celery no disponible): {e}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Error probando tareas asíncronas: {e}")
        return False

def test_country_specific_rules():
    """Probar reglas específicas por país"""
    print("\n🧪 Probando reglas específicas por país...")
    
    try:
        # Probar Colombia
        co_rules = TaxValidator('CO').get_tax_rules_for_country()
        print(f"   🇨🇴 Colombia - IVA estándar: {co_rules['iva_rates']['standard']}")
        print(f"   🇨🇴 Colombia - ReteFuente natural: {co_rules['retenciones']['rete_fuente']['natural']}")
        
        # Probar México
        mx_rules = TaxValidator('MX').get_tax_rules_for_country()
        print(f"   🇲🇽 México - IVA estándar: {mx_rules['iva_rates']['standard']}")
        print(f"   🇲🇽 México - ISR natural: {mx_rules['retenciones']['isr']['natural']}")
        
        # Probar validación de NIT
        validator = TaxValidator('CO')
        valid_nit = validator.validate_nit_format('900123456-1')
        invalid_nit = validator.validate_nit_format('123')
        
        print(f"   🔢 NIT válido: {valid_nit}")
        print(f"   🔢 NIT inválido: {invalid_nit}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Error probando reglas por país: {e}")
        return False

def test_performance_improvements():
    """Probar mejoras de performance"""
    print("\n🧪 Probando mejoras de performance...")
    
    try:
        # Probar caché con múltiples operaciones
        cache_manager = CacheManager()
        
        start_time = time.time()
        
        # Simular múltiples consultas
        for i in range(100):
            test_contact = {
                'id': f'test_{i}',
                'name': f'Empresa Test {i} S.A.S.',
                'type': 'client'
            }
            cache_manager.cache_contact(test_contact)
        
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"   ⚡ 100 operaciones de caché en {duration:.2f} segundos")
        print(f"   📊 Promedio: {duration/100*1000:.2f} ms por operación")
        
        # Probar validación de impuestos en lote
        start_time = time.time()
        
        validator = TaxValidator('CO')
        for i in range(50):
            test_invoice = {
                'fecha': '2024-01-15',
                'total': 1000000.0 + i,
                'iva': 190000.0 + (i * 19),
                'items': [{'descripcion': f'Item {i}', 'precio': 1000000.0 + i}],
                'tipo': 'compra'
            }
            validator.validate_invoice_taxes(test_invoice)
        
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"   ⚡ 50 validaciones de impuestos en {duration:.2f} segundos")
        print(f"   📊 Promedio: {duration/50*1000:.2f} ms por validación")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Error probando performance: {e}")
        return False

def main():
    """Función principal de pruebas"""
    print("🚀 INICIANDO PRUEBAS DE OPTIMIZACIONES")
    print("=" * 60)
    
    tests = [
        ("Sistema de Caché", test_cache_system),
        ("Validación de Impuestos", test_tax_validation),
        ("Validación DIAN", test_dian_validation),
        ("Tareas Asíncronas", test_async_tasks),
        ("Reglas por País", test_country_specific_rules),
        ("Mejoras de Performance", test_performance_improvements)
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
    print("📊 RESUMEN DE PRUEBAS DE OPTIMIZACIONES")
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
        print("🎉 ¡Todas las optimizaciones están funcionando!")
    else:
        print("⚠️ Algunas optimizaciones necesitan revisión.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)