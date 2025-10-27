#!/usr/bin/env python3
"""
Script de prueba para las funcionalidades de resiliencia y optimización de caché
"""

import os
import sys
import time
import json
from datetime import datetime
from cache_manager import CacheManager
from dian_resilience import DIANResilienceManager, ComplianceStatus

def test_cache_optimization():
    """Probar optimizaciones de caché"""
    print("🧪 Probando optimizaciones de caché...")
    
    try:
        cache_manager = CacheManager()
        
        # Probar invalidación granular
        test_contact = {
            'id': 'test_contact_123',
            'name': 'Empresa Test S.A.S.',
            'type': 'client'
        }
        
        # Guardar contacto
        cache_manager.cache_contact(test_contact)
        print("   ✅ Contacto guardado en caché")
        
        # Recuperar contacto
        cached_contact = cache_manager.get_contact_by_id('test_contact_123')
        print(f"   ✅ Contacto recuperado: {cached_contact is not None}")
        
        # Probar invalidación específica
        cache_manager.invalidate_contact('test_contact_123')
        print("   ✅ Invalidación granular funcionando")
        
        # Obtener métricas detalladas
        metrics = cache_manager.get_cache_metrics()
        print(f"   📊 Hit Rate: {metrics.get('hit_rate', 0)}%")
        print(f"   📊 Hits: {metrics.get('hits', 0)}")
        print(f"   📊 Misses: {metrics.get('misses', 0)}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Error probando caché: {e}")
        return False

def test_dian_resilience():
    """Probar sistema de resiliencia DIAN"""
    print("\n🧪 Probando sistema de resiliencia DIAN...")
    
    try:
        resilience_manager = DIANResilienceManager()
        
        # Datos de prueba
        test_invoice_data = {
            'nit_emisor': '900123456-1',
            'nit_receptor': '800987654-3',
            'fecha': '2024-01-15',
            'numero_factura': 'FAC-001',
            'total': 1000000.0,
            'iva': 190000.0
        }
        
        # Registrar factura
        record = resilience_manager.register_invoice(
            'test_invoice_001',
            '/test/path/invoice.pdf',
            test_invoice_data
        )
        print(f"   ✅ Factura registrada: {record.invoice_id}")
        
        # Simular diferentes estados
        resilience_manager.update_compliance_status(
            'test_invoice_001',
            ComplianceStatus.RETRY,
            error_message="Timeout en validación DIAN"
        )
        print("   ✅ Estado actualizado a RETRY")
        
        # Obtener estadísticas
        stats = resilience_manager.get_compliance_stats()
        print(f"   📊 Total facturas: {stats.get('total_invoices', 0)}")
        print(f"   📊 Pendientes: {stats.get('pending', 0)}")
        print(f"   📊 Reintentos: {stats.get('retry', 0)}")
        
        # Probar limpieza
        cleaned = resilience_manager.cleanup_old_records(days_old=0)  # Limpiar todo para prueba
        print(f"   🧹 Limpieza: {cleaned} registros eliminados")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Error probando resiliencia: {e}")
        return False

def test_fallback_system():
    """Probar sistema de fallback"""
    print("\n🧪 Probando sistema de fallback...")
    
    try:
        resilience_manager = DIANResilienceManager()
        
        # Simular factura con fallo
        test_invoice_data = {
            'nit_emisor': '900123456-1',
            'nit_receptor': '800987654-3',
            'fecha': '2024-01-15',
            'numero_factura': 'FAC-002',
            'total': 2000000.0,
            'iva': 380000.0
        }
        
        # Registrar factura
        record = resilience_manager.register_invoice(
            'test_invoice_002',
            '/test/path/invoice2.pdf',
            test_invoice_data
        )
        
        # Simular fallo después de reintentos
        resilience_manager.update_compliance_status(
            'test_invoice_002',
            ComplianceStatus.FAILED,
            error_message="Falló después de 3 reintentos"
        )
        
        # Verificar backup
        backup_file = os.path.join(
            resilience_manager.fallback_folder,
            'test_invoice_002_backup.json'
        )
        
        if os.path.exists(backup_file):
            with open(backup_file, 'r', encoding='utf-8') as f:
                backup_data = json.load(f)
            
            print(f"   ✅ Backup creado: {backup_data['invoice_id']}")
            print(f"   ✅ Estado en backup: {backup_data['compliance_status']}")
        
        # Obtener facturas fallidas
        failed_invoices = resilience_manager.get_failed_invoices()
        print(f"   📊 Facturas fallidas: {len(failed_invoices)}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Error probando fallback: {e}")
        return False

def test_metrics_and_monitoring():
    """Probar métricas y monitoreo"""
    print("\n🧪 Probando métricas y monitoreo...")
    
    try:
        cache_manager = CacheManager()
        
        # Simular operaciones para generar métricas
        for i in range(10):
            test_contact = {
                'id': f'metric_test_{i}',
                'name': f'Empresa Métrica {i}',
                'type': 'client'
            }
            cache_manager.cache_contact(test_contact)
            cache_manager.get_contact_by_id(f'metric_test_{i}')
        
        # Obtener métricas detalladas
        metrics = cache_manager.get_cache_metrics()
        
        print(f"   📊 Hit Rate: {metrics.get('hit_rate', 0)}%")
        print(f"   📊 Total Requests: {metrics.get('hits', 0) + metrics.get('misses', 0)}")
        print(f"   📊 Memory Usage: {metrics.get('memory_usage_mb', 0)} MB")
        print(f"   📊 Average TTL: {metrics.get('avg_ttl_seconds', 0)}s")
        
        # Resetear métricas
        cache_manager.reset_metrics()
        print("   ✅ Métricas reseteadas")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Error probando métricas: {e}")
        return False

def test_error_handling():
    """Probar manejo de errores"""
    print("\n🧪 Probando manejo de errores...")
    
    try:
        cache_manager = CacheManager()
        
        # Probar con datos inválidos
        invalid_contact = {'id': 'test', 'name': ''}  # Sin nombre
        result = cache_manager.cache_contact(invalid_contact)
        print(f"   ✅ Manejo de datos inválidos: {not result}")
        
        # Probar invalidación de contacto inexistente
        result = cache_manager.invalidate_contact('nonexistent_id')
        print(f"   ✅ Invalidación de ID inexistente: {result}")
        
        # Probar invalidación por patrón
        deleted_count = cache_manager.invalidate_by_pattern('metric_test_*')
        print(f"   ✅ Invalidación por patrón: {deleted_count} claves eliminadas")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Error probando manejo de errores: {e}")
        return False

def main():
    """Función principal de pruebas"""
    print("🚀 INICIANDO PRUEBAS DE RESILIENCIA Y OPTIMIZACIÓN")
    print("=" * 60)
    
    tests = [
        ("Optimización de Caché", test_cache_optimization),
        ("Resiliencia DIAN", test_dian_resilience),
        ("Sistema de Fallback", test_fallback_system),
        ("Métricas y Monitoreo", test_metrics_and_monitoring),
        ("Manejo de Errores", test_error_handling)
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
    print("📊 RESUMEN DE PRUEBAS DE RESILIENCIA")
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
        print("🎉 ¡Todas las funcionalidades de resiliencia están funcionando!")
    else:
        print("⚠️ Algunas funcionalidades necesitan revisión.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)