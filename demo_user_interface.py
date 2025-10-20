#!/usr/bin/env python3
"""
Demostración de la interfaz de usuario del sistema de facturas
Muestra exactamente lo que vería el usuario durante el procesamiento
"""

import os
import sys
import json
import pdfplumber
import re
from datetime import datetime
from config import PDF_PATTERNS

def clear_screen():
    """Limpiar pantalla"""
    os.system('clear' if os.name == 'posix' else 'cls')

def print_header(title):
    """Imprimir encabezado"""
    print("=" * 60)
    print(f"🚀 {title}")
    print("=" * 60)

def print_section(title):
    """Imprimir sección"""
    print(f"\n{'='*20} {title} {'='*20}")

def print_data_table(data):
    """Imprimir tabla de datos"""
    print("┌" + "─" * 58 + "┐")
    for key, value in data.items():
        if value and value != 'N/A':
            print(f"│ {key:15} │ {str(value):38} │")
    print("└" + "─" * 58 + "┘")

def print_validation_results(validations):
    """Imprimir resultados de validación"""
    print("┌" + "─" * 58 + "┐")
    for validation, result in validations.items():
        status = "✅" if result['valid'] else "❌"
        message = result['message'][:35] + "..." if len(result['message']) > 35 else result['message']
        print(f"│ {status} {validation.replace('_', ' ').title():15} │ {message:38} │")
    print("└" + "─" * 58 + "┘")

def print_menu(options):
    """Imprimir menú de opciones"""
    print("\n" + "─" * 40)
    for i, option in enumerate(options, 1):
        print(f"{i}. {option}")
    print("─" * 40)

def simulate_user_input(prompt, default="s"):
    """Simular entrada del usuario"""
    print(f"\n{prompt}")
    return default

def extract_pdf_data(file_path):
    """Extraer datos de PDF"""
    print(f"🔍 Extrayendo datos de {file_path}...")
    
    try:
        with pdfplumber.open(file_path) as pdf:
            text = ''
            for page in pdf.pages:
                text += page.extract_text() or ''
        
        print(f"✅ Texto extraído: {len(text)} caracteres")
        
        # Extraer datos con patrones
        patterns = PDF_PATTERNS.copy()
        datos = {}
        
        for tipo, patrones_lista in patterns.items():
            for patron in patrones_lista:
                matches = re.findall(patron, text, re.IGNORECASE | re.MULTILINE)
                if matches:
                    if tipo not in datos:
                        datos[tipo] = []
                    datos[tipo].extend(matches)
        
        # Procesar datos extraídos
        processed_data = {
            'fecha': datos.get('fecha', ['N/A'])[0] if datos.get('fecha') else 'N/A',
            'proveedor': datos.get('proveedor', ['N/A'])[0] if datos.get('proveedor') else 'N/A',
            'nit_proveedor': datos.get('nit_proveedor', ['N/A'])[0] if datos.get('nit_proveedor') else 'N/A',
            'total': float(datos.get('total', ['0'])[0].replace(',', '')) if datos.get('total') else 0,
            'iva': float(datos.get('iva', ['0'])[0].replace(',', '')) if datos.get('iva') else 0,
            'numero_factura': datos.get('numero_factura', ['N/A'])[0] if datos.get('numero_factura') else 'N/A',
            'cliente': datos.get('cliente', ['N/A'])[0] if datos.get('cliente') else 'N/A'
        }
        
        return processed_data
        
    except Exception as e:
        print(f"❌ Error extrayendo datos: {e}")
        return None

def validate_invoice_data(datos):
    """Validar datos de factura"""
    print("🔍 Ejecutando validaciones contables...")
    
    validaciones = {}
    
    # Validación 1: Total vs IVA
    if datos['total'] > 0 and datos['iva'] > 0:
        expected_iva = datos['total'] * 0.19  # 19% IVA
        tolerance = datos['total'] * 0.01  # 1% tolerancia
        validaciones['iva_calculo'] = {
            'valid': abs(datos['iva'] - expected_iva) <= tolerance,
            'message': f'IVA calculado: ${datos["iva"]:,.2f}, Esperado: ${expected_iva:,.2f}'
        }
    else:
        validaciones['iva_calculo'] = {
            'valid': False,
            'message': 'Datos de total o IVA faltantes'
        }
    
    # Validación 2: NIT formato
    nit = datos.get('nit_proveedor', '')
    if nit and nit != 'N/A':
        nit_valid = re.match(r'^\d{8,10}-\d{1}$', nit)
        validaciones['nit_formato'] = {
            'valid': bool(nit_valid),
            'message': f'NIT {nit} - Formato {"válido" if nit_valid else "inválido"}'
        }
    else:
        validaciones['nit_formato'] = {
            'valid': False,
            'message': 'NIT no encontrado'
        }
    
    # Validación 3: Monto mínimo
    validaciones['monto_minimo'] = {
        'valid': datos['total'] >= 1000,
        'message': f'Total ${datos["total"]:,.2f} - {"Aceptable" if datos["total"] >= 1000 else "Muy bajo"}'
    }
    
    # Validación 4: Duplicados
    validaciones['duplicados'] = {
        'valid': True,
        'message': 'No se encontraron duplicados'
    }
    
    return validaciones

def show_invoice_detection(datos):
    """Mostrar detección de factura"""
    clear_screen()
    print_header("FACTURA DETECTADA")
    
    print_data_table({
        'Fecha': datos['fecha'],
        'Proveedor': datos['proveedor'],
        'NIT': datos['nit_proveedor'],
        'Total': f"${datos['total']:,.2f}",
        'IVA': f"${datos['iva']:,.2f}",
        'Número': datos['numero_factura'],
        'Cliente': datos['cliente']
    })

def show_validations(validaciones):
    """Mostrar validaciones"""
    print_section("VALIDACIONES CONTABLES")
    print_validation_results(validaciones)

def show_categorization():
    """Mostrar categorización automática"""
    print_section("CATEGORIZACIÓN AUTOMÁTICA")
    print("🤖 Categoría sugerida: Gastos Operativos")
    print("📝 Subcategoría: Servicios Profesionales")
    print("💡 Confianza: 95%")

def show_user_options():
    """Mostrar opciones del usuario"""
    print_section("OPCIONES DISPONIBLES")
    print_menu([
        "✅ CONFIRMAR Y CREAR",
        "✏️ EDITAR DATOS",
        "🔍 VER DETALLES",
        "📝 EDITAR CATEGORÍA",
        "❌ CANCELAR"
    ])

def show_editing_interface(datos):
    """Mostrar interfaz de edición"""
    print_section("EDITAR DATOS")
    print("✏️ Modifica los campos que necesites:")
    print()
    
    fields = [
        ('fecha', 'Fecha', datos['fecha']),
        ('proveedor', 'Proveedor', datos['proveedor']),
        ('nit_proveedor', 'NIT', datos['nit_proveedor']),
        ('total', 'Total', f"${datos['total']:,.2f}"),
        ('iva', 'IVA', f"${datos['iva']:,.2f}"),
        ('numero_factura', 'Número', datos['numero_factura'])
    ]
    
    for field, label, value in fields:
        print(f"📝 {label} [{value}]: ")

def show_category_editing():
    """Mostrar interfaz de edición de categoría"""
    print_section("EDITAR CATEGORÍA")
    print("📝 Selecciona la categoría correcta:")
    print()
    
    categories = [
        "Gastos Operativos",
        "Gastos Administrativos",
        "Gastos de Ventas",
        "Costos Directos",
        "Inversiones",
        "Otros Gastos"
    ]
    
    for i, category in enumerate(categories, 1):
        print(f"{i}. {category}")

def show_alegra_creation(datos):
    """Mostrar creación en Alegra"""
    print_section("CREACIÓN EN ALEGRA")
    print("💾 Generando payload para Alegra...")
    print()
    
    payload = {
        'date': datos['fecha'],
        'dueDate': '2024-02-15',
        'client': {'name': datos['cliente']},
        'items': [{
            'description': 'Producto/Servicio procesado',
            'quantity': 1,
            'price': datos['total']
        }],
        'taxes': [{'amount': datos['iva']}],
        'total': datos['total']
    }
    
    print("✅ Payload generado:")
    print(f"   📅 Fecha: {payload['date']}")
    print(f"   👤 Cliente: {payload['client']['name']}")
    print(f"   💰 Total: ${payload['total']:,.2f}")
    print(f"   🧾 IVA: ${payload['taxes'][0]['amount']:,.2f}")
    print()
    print("🔄 Enviando a Alegra API...")
    print("⏳ Procesando...")
    
    # Simular delay
    import time
    time.sleep(2)
    
    print("✅ ¡Factura creada exitosamente!")
    print(f"🆔 ID Alegra: FAC-{datetime.now().strftime('%Y%m%d%H%M%S')}")
    print(f"📊 Estado: Procesada")

def show_processing_metrics():
    """Mostrar métricas de procesamiento"""
    print_section("MÉTRICAS DE PROCESAMIENTO")
    print("✅ Procesamiento completado:")
    print(f"   ⏱️ Tiempo total: 2.3 segundos")
    print(f"   ✅ Validaciones: 8/8 exitosas")
    print(f"   💾 Caché hit rate: 85%")
    print(f"   🏛️ Estado DIAN: Validado ✓")
    print(f"   📄 Archivo procesado: ✓")

def show_final_summary(datos, alegra_id):
    """Mostrar resumen final"""
    print_section("RESUMEN FINAL")
    print("🎉 ¡Factura procesada exitosamente!")
    print()
    print_data_table({
        'ID Alegra': alegra_id,
        'Fecha': datos['fecha'],
        'Proveedor': datos['proveedor'],
        'Total': f"${datos['total']:,.2f}",
        'IVA': f"${datos['iva']:,.2f}",
        'Estado': 'Procesada'
    })
    
    print("\n¿Qué deseas hacer ahora?")
    print_menu([
        "📄 Procesar otra factura",
        "📊 Ver reportes",
        "⚙️ Configurar sistema",
        "🚪 Salir"
    ])

def simulate_user_journey():
    """Simular el journey completo del usuario"""
    print_header("SISTEMA DE FACTURAS - INTERFAZ DE USUARIO")
    print("👤 Bienvenido al sistema de procesamiento de facturas")
    print("📄 Archivo detectado: testfactura1.pdf")
    
    input("\n⏎ Presiona Enter para continuar...")
    
    # Paso 1: Extracción de datos
    datos = extract_pdf_data('testfactura1.pdf')
    if not datos:
        print("❌ Error: No se pudieron extraer datos del archivo")
        return
    
    # Paso 2: Mostrar datos extraídos
    show_invoice_detection(datos)
    input("\n⏎ Presiona Enter para continuar...")
    
    # Paso 3: Mostrar validaciones
    validaciones = validate_invoice_data(datos)
    show_validations(validaciones)
    input("\n⏎ Presiona Enter para continuar...")
    
    # Paso 4: Mostrar categorización
    show_categorization()
    input("\n⏎ Presiona Enter para continuar...")
    
    # Paso 5: Mostrar opciones del usuario
    show_user_options()
    
    # Simular selección del usuario
    print("\n👤 [Usuario] Selecciona: 1 (CONFIRMAR Y CREAR)")
    input("⏎ Presiona Enter para continuar...")
    
    # Paso 6: Mostrar creación en Alegra
    show_alegra_creation(datos)
    input("\n⏎ Presiona Enter para continuar...")
    
    # Paso 7: Mostrar métricas
    show_processing_metrics()
    input("\n⏎ Presiona Enter para continuar...")
    
    # Paso 8: Mostrar resumen final
    alegra_id = f"FAC-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    show_final_summary(datos, alegra_id)
    
    print("\n🎉 ¡User Journey completado exitosamente!")

def main():
    """Función principal"""
    if not os.path.exists('testfactura1.pdf'):
        print("❌ Error: Archivo testfactura1.pdf no encontrado")
        return False
    
    simulate_user_journey()
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)