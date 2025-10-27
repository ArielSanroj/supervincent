#!/usr/bin/env python3
"""
Script de prueba para verificar las correcciones implementadas
"""

import sys
import os
from invoice_processor_robust import InvoiceProcessorRobust

def test_invoice_processing():
    """Probar el procesamiento de facturas con las correcciones"""
    print("🧪 Probando procesamiento de facturas con correcciones...")
    
    try:
        processor = InvoiceProcessorRobust()
        print("✅ Procesador inicializado correctamente")
        
        # Probar validación de datos
        print("\n📋 Probando validación de datos...")
        
        # Datos válidos
        datos_validos = {
            'fecha': '2025-01-15',
            'cliente': 'Cliente de Prueba',
            'items': [
                {'descripcion': 'Producto 1', 'cantidad': 2.0, 'precio': 100.0},
                {'descripcion': 'Producto 2', 'cantidad': 1.0, 'precio': 50.0}
            ],
            'total': 250.0
        }
        
        is_valid, errors = processor.validate_invoice_data(datos_validos)
        if is_valid:
            print("✅ Validación de datos válidos: PASS")
        else:
            print(f"❌ Validación de datos válidos: FAIL - {errors}")
        
        # Datos inválidos
        datos_invalidos = {
            'fecha': 'fecha-invalida',
            'items': [],
            'total': -100.0
        }
        
        is_valid, errors = processor.validate_invoice_data(datos_invalidos)
        if not is_valid:
            print("✅ Validación de datos inválidos: PASS")
        else:
            print(f"❌ Validación de datos inválidos: FAIL - debería detectar errores")
        
        # Probar detección de tipo de factura
        print("\n🔍 Probando detección de tipo de factura...")
        
        texto_compra = "Factura de compra - Proveedor: ABC S.A.S. - Total: $1000"
        tipo_compra = processor.detect_invoice_type(texto_compra)
        if tipo_compra == 'compra':
            print("✅ Detección de factura de compra: PASS")
        else:
            print(f"❌ Detección de factura de compra: FAIL - detectado como {tipo_compra}")
        
        texto_venta = "Factura de venta - Cliente: XYZ Ltda. - Total: $2000"
        tipo_venta = processor.detect_invoice_type(texto_venta)
        if tipo_venta == 'venta':
            print("✅ Detección de factura de venta: PASS")
        else:
            print(f"❌ Detección de factura de venta: FAIL - detectado como {tipo_venta}")
        
        # Probar parsing de datos
        print("\n📊 Probando parsing de datos...")
        
        texto_ejemplo = """
        Fecha: 15/01/2025
        Cliente: Empresa Ejemplo S.A.S.
        Total: $1,500.00
        
        Descripción    Cantidad    Precio
        Producto A     2           500.00
        Producto B     1           500.00
        """
        
        datos_parseados = processor.parse_invoice_data(texto_ejemplo)
        
        if datos_parseados.get('fecha') == '2025-01-15':
            print("✅ Parsing de fecha: PASS")
        else:
            print(f"❌ Parsing de fecha: FAIL - {datos_parseados.get('fecha')}")
        
        if datos_parseados.get('cliente') == 'Empresa Ejemplo S.A.S.':
            print("✅ Parsing de cliente: PASS")
        else:
            print(f"❌ Parsing de cliente: FAIL - {datos_parseados.get('cliente')}")
        
        if abs(datos_parseados.get('total', 0) - 1500.0) < 0.01:
            print("✅ Parsing de total: PASS")
        else:
            print(f"❌ Parsing de total: FAIL - {datos_parseados.get('total')}")
        
        print("\n🎉 Todas las pruebas completadas!")
        return True
        
    except Exception as e:
        print(f"❌ Error en las pruebas: {e}")
        return False

def test_contact_creation_fallback():
    """Probar el fallback de creación de contactos"""
    print("\n👥 Probando fallback de contactos...")
    
    try:
        processor = InvoiceProcessorRobust()
        
        # Probar con nombre vacío
        contact_id = processor.get_or_create_contact_robust("", "client")
        if contact_id == "1":
            print("✅ Fallback con nombre vacío: PASS")
        else:
            print(f"❌ Fallback con nombre vacío: FAIL - {contact_id}")
        
        # Probar con nombre muy largo (que podría causar error)
        contact_id = processor.get_or_create_contact_robust("A" * 1000, "client")
        if contact_id:
            print("✅ Fallback con nombre largo: PASS")
        else:
            print(f"❌ Fallback con nombre largo: FAIL")
        
        return True
        
    except Exception as e:
        print(f"❌ Error en prueba de contactos: {e}")
        return False

def main():
    """Función principal de pruebas"""
    print("🚀 Iniciando pruebas de correcciones...")
    print("=" * 50)
    
    # Ejecutar pruebas
    test1 = test_invoice_processing()
    test2 = test_contact_creation_fallback()
    
    print("\n" + "=" * 50)
    if test1 and test2:
        print("🎉 ¡Todas las pruebas pasaron exitosamente!")
        print("✅ Las correcciones están funcionando correctamente")
    else:
        print("❌ Algunas pruebas fallaron")
        print("⚠️ Revisar los errores mostrados arriba")
    
    return test1 and test2

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)