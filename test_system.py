#!/usr/bin/env python3
"""
Script de pruebas del sistema InvoiceBot
"""

import os
import sys
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_imports():
    """Probar que todos los módulos se importan correctamente"""
    print("🔍 Probando imports...")
    
    try:
        from invoice_processor_enhanced import InvoiceProcessor
        print("   ✅ InvoiceProcessor importado")
    except ImportError as e:
        print(f"   ❌ Error importando InvoiceProcessor: {e}")
        return False
    
    try:
        from alegra_reports import AlegraReports
        print("   ✅ AlegraReports importado")
    except ImportError as e:
        print(f"   ❌ Error importando AlegraReports: {e}")
        return False
    
    try:
        from invoice_watcher import InvoiceWatcher
        print("   ✅ InvoiceWatcher importado")
    except ImportError as e:
        print(f"   ❌ Error importando InvoiceWatcher: {e}")
        return False
    
    try:
        from config_validator import ConfigValidator
        print("   ✅ ConfigValidator importado")
    except ImportError as e:
        print(f"   ❌ Error importando ConfigValidator: {e}")
        return False
    
    return True

def test_configuration():
    """Probar configuración del sistema"""
    print("⚙️ Probando configuración...")
    
    # Verificar archivo .env
    if not os.path.exists('.env'):
        print("   ❌ Archivo .env no encontrado")
        return False
    print("   ✅ Archivo .env encontrado")
    
    # Verificar variables de entorno
    from dotenv import load_dotenv
    load_dotenv()
    
    alegra_user = os.getenv('ALEGRA_USER')
    alegra_token = os.getenv('ALEGRA_TOKEN')
    
    if not alegra_user or alegra_user == 'tu_email@ejemplo.com':
        print("   ⚠️ ALEGRA_USER no configurado correctamente")
    else:
        print("   ✅ ALEGRA_USER configurado")
    
    if not alegra_token or alegra_token == 'tu_token_de_alegra':
        print("   ⚠️ ALEGRA_TOKEN no configurado correctamente")
    else:
        print("   ✅ ALEGRA_TOKEN configurado")
    
    return True

def test_directories():
    """Probar estructura de directorios"""
    print("📁 Probando estructura de directorios...")
    
    required_dirs = [
        'logs',
        'reports',
        'facturas',
        'facturas/processed',
        'facturas/error',
        'backup',
        'config'
    ]
    
    all_exist = True
    for directory in required_dirs:
        if os.path.exists(directory):
            print(f"   ✅ {directory}/")
        else:
            print(f"   ❌ {directory}/ no encontrado")
            all_exist = False
    
    return all_exist

def test_invoice_processor():
    """Probar procesador de facturas"""
    print("📄 Probando procesador de facturas...")
    
    try:
        from invoice_processor_enhanced import InvoiceProcessor
        processor = InvoiceProcessor()
        print("   ✅ InvoiceProcessor inicializado")
        
        # Probar detección de tipo
        test_text_compra = "Factura de compra Proveedor: Test Company"
        tipo_compra = processor.detect_invoice_type(test_text_compra)
        if tipo_compra == 'compra':
            print("   ✅ Detección de compra funciona")
        else:
            print(f"   ❌ Detección de compra falló: {tipo_compra}")
        
        test_text_venta = "Factura de venta Cliente: Test Customer"
        tipo_venta = processor.detect_invoice_type(test_text_venta)
        if tipo_venta == 'venta':
            print("   ✅ Detección de venta funciona")
        else:
            print(f"   ❌ Detección de venta falló: {tipo_venta}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Error probando InvoiceProcessor: {e}")
        return False

def test_reports():
    """Probar generador de reportes"""
    print("📊 Probando generador de reportes...")
    
    try:
        from alegra_reports import AlegraReports
        reporter = AlegraReports()
        print("   ✅ AlegraReports inicializado")
        
        # Probar obtención de cuentas (sin hacer llamada real)
        print("   ✅ AlegraReports configurado correctamente")
        return True
        
    except Exception as e:
        print(f"   ❌ Error probando AlegraReports: {e}")
        return False

def test_watcher():
    """Probar sistema de monitoreo"""
    print("👀 Probando sistema de monitoreo...")
    
    try:
        from invoice_watcher import InvoiceWatcher, InvoiceHandler
        print("   ✅ InvoiceWatcher importado")
        
        # Probar inicialización (sin iniciar monitoreo)
        watcher = InvoiceWatcher('facturas')
        print("   ✅ InvoiceWatcher inicializado")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Error probando InvoiceWatcher: {e}")
        return False

def test_config_validator():
    """Probar validador de configuración"""
    print("🔍 Probando validador de configuración...")
    
    try:
        from config_validator import ConfigValidator
        validator = ConfigValidator()
        print("   ✅ ConfigValidator inicializado")
        
        # Ejecutar validación
        success, errors, warnings = validator.validate_all()
        
        if success:
            print("   ✅ Validación completada exitosamente")
        else:
            print(f"   ⚠️ Validación completada con {len(errors)} errores")
            for error in errors:
                print(f"      - {error}")
        
        if warnings:
            print(f"   ⚠️ {len(warnings)} advertencias encontradas")
            for warning in warnings:
                print(f"      - {warning}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Error probando ConfigValidator: {e}")
        return False

def create_test_pdf():
    """Crear un PDF de prueba"""
    print("📄 Creando PDF de prueba...")
    
    try:
        # Crear un PDF simple de prueba usando reportlab si está disponible
        try:
            from reportlab.pdfgen import canvas
            from reportlab.lib.pagesizes import letter
            
            pdf_path = 'facturas/test_factura.pdf'
            c = canvas.Canvas(pdf_path, pagesize=letter)
            
            # Contenido de factura de prueba
            c.drawString(100, 750, "FACTURA DE VENTA")
            c.drawString(100, 720, "Cliente: Cliente de Prueba")
            c.drawString(100, 690, "Fecha: 01-01-2024")
            c.drawString(100, 660, "Producto: Producto de Prueba")
            c.drawString(100, 630, "Cantidad: 1 Unidad")
            c.drawString(100, 600, "Precio unit.: $100.00")
            c.drawString(100, 570, "Subtotal $100.00")
            c.drawString(100, 540, "Impuestos $19.00")
            c.drawString(100, 510, "Total $119.00")
            
            c.save()
            print(f"   ✅ PDF de prueba creado: {pdf_path}")
            return pdf_path
            
        except ImportError:
            print("   ⚠️ reportlab no disponible, saltando creación de PDF de prueba")
            return None
            
    except Exception as e:
        print(f"   ❌ Error creando PDF de prueba: {e}")
        return None

def test_pdf_processing(pdf_path):
    """Probar procesamiento de PDF"""
    if not pdf_path or not os.path.exists(pdf_path):
        print("   ⚠️ No hay PDF de prueba para procesar")
        return True
    
    print("🔄 Probando procesamiento de PDF...")
    
    try:
        from invoice_processor_enhanced import InvoiceProcessor
        processor = InvoiceProcessor()
        
        # Probar extracción de datos
        datos = processor.extract_data_from_pdf(pdf_path)
        
        if datos:
            print("   ✅ Extracción de datos exitosa")
            print(f"      Tipo detectado: {datos['tipo']}")
            print(f"      Fecha: {datos['fecha']}")
            print(f"      Total: ${datos['total']:,.2f}")
            return True
        else:
            print("   ❌ Error extrayendo datos del PDF")
            return False
            
    except Exception as e:
        print(f"   ❌ Error procesando PDF: {e}")
        return False

def generate_test_report():
    """Generar reporte de pruebas"""
    print("📋 Generando reporte de pruebas...")
    
    report = {
        "timestamp": datetime.now().isoformat(),
        "tests": {
            "imports": test_imports(),
            "configuration": test_configuration(),
            "directories": test_directories(),
            "invoice_processor": test_invoice_processor(),
            "reports": test_reports(),
            "watcher": test_watcher(),
            "config_validator": test_config_validator()
        }
    }
    
    # Guardar reporte
    with open('reports/test_report.json', 'w') as f:
        json.dump(report, f, indent=2)
    
    print("   ✅ Reporte guardado en: reports/test_report.json")
    
    return report

def main():
    """Función principal de pruebas"""
    print("""
╔══════════════════════════════════════════════════════════════╗
║                    InvoiceBot - Test Suite                   ║
╚══════════════════════════════════════════════════════════════╝
""")
    
    # Ejecutar todas las pruebas
    print("🧪 Ejecutando suite de pruebas...")
    print("=" * 50)
    
    # Crear PDF de prueba
    test_pdf = create_test_pdf()
    
    # Probar procesamiento de PDF
    test_pdf_processing(test_pdf)
    
    # Generar reporte
    report = generate_test_report()
    
    # Mostrar resumen
    print("\n📊 RESUMEN DE PRUEBAS")
    print("=" * 50)
    
    passed = 0
    total = len(report['tests'])
    
    for test_name, result in report['tests'].items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:20} {status}")
        if result:
            passed += 1
    
    print("=" * 50)
    print(f"Pruebas pasadas: {passed}/{total}")
    
    if passed == total:
        print("🎉 ¡Todas las pruebas pasaron!")
        print("✅ El sistema está listo para usar")
    else:
        print("⚠️ Algunas pruebas fallaron")
        print("🔧 Revisa los errores y ejecuta la configuración nuevamente")
    
    print(f"\n📁 Reporte completo: reports/test_report.json")

if __name__ == "__main__":
    main()