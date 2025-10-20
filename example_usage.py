#!/usr/bin/env python3
"""
Ejemplos de uso del InvoiceBot
"""

from invoice_processor import InvoiceProcessor
import os
from pathlib import Path

def ejemplo_procesamiento_manual():
    """Ejemplo de procesamiento manual de facturas"""
    print("=== Ejemplo de Procesamiento Manual ===")
    
    # Crear instancia del procesador
    processor = InvoiceProcessor()
    
    # Ejemplo con archivo XML
    archivo_xml = "ejemplo_factura.xml"
    if os.path.exists(archivo_xml):
        print(f"Procesando {archivo_xml}...")
        resultado = processor.procesar_factura(archivo_xml, 'xml')
        if resultado:
            print(f"✅ Factura XML procesada: {resultado.get('id')}")
        else:
            print("❌ Error procesando factura XML")
    else:
        print(f"Archivo {archivo_xml} no encontrado")
    
    # Ejemplo con archivo PDF
    archivo_pdf = "ejemplo_factura.pdf"
    if os.path.exists(archivo_pdf):
        print(f"Procesando {archivo_pdf}...")
        resultado = processor.procesar_factura(archivo_pdf, 'pdf')
        if resultado:
            print(f"✅ Factura PDF procesada: {resultado.get('id')}")
        else:
            print("❌ Error procesando factura PDF")
    else:
        print(f"Archivo {archivo_pdf} no encontrado")

def ejemplo_crear_factura_desde_datos():
    """Ejemplo de crear factura directamente desde datos"""
    print("\n=== Ejemplo de Creación Directa ===")
    
    processor = InvoiceProcessor()
    
    # Datos de ejemplo
    datos_factura = {
        'fecha': '2024-01-15',
        'cliente': 'Cliente Ejemplo S.A.',
        'items': [
            {
                'descripcion': 'Servicio de consultoría',
                'cantidad': 1.0,
                'precio': 1000.00
            },
            {
                'descripcion': 'Desarrollo de software',
                'cantidad': 2.0,
                'precio': 500.00
            }
        ],
        'total': 2000.00
    }
    
    print("Creando factura desde datos...")
    resultado = processor.crear_factura_alegra(datos_factura)
    
    if resultado:
        print(f"✅ Factura creada: {resultado.get('id')}")
        print(f"Cliente: {resultado.get('client', {}).get('name')}")
        print(f"Total: ${resultado.get('total')}")
    else:
        print("❌ Error creando factura")

def ejemplo_monitoreo_carpeta():
    """Ejemplo de configuración de monitoreo de carpeta"""
    print("\n=== Ejemplo de Monitoreo de Carpeta ===")
    
    # Crear carpeta de ejemplo si no existe
    carpeta_facturas = "facturas_entrada"
    Path(carpeta_facturas).mkdir(exist_ok=True)
    
    print(f"Carpeta de monitoreo: {carpeta_facturas}")
    print("Coloca archivos XML o PDF en esta carpeta para procesamiento automático")
    print("Presiona Ctrl+C para detener el monitoreo")
    
    try:
        from invoice_processor import monitorear_carpeta
        monitorear_carpeta(carpeta_facturas)
    except KeyboardInterrupt:
        print("\nMonitoreo detenido")

def ejemplo_configuracion_personalizada():
    """Ejemplo de configuración personalizada"""
    print("\n=== Ejemplo de Configuración Personalizada ===")
    
    # Importar configuración
    from config import PDF_PATTERNS, XML_NAMESPACES
    
    print("Patrones PDF configurados:")
    for tipo, patrones in PDF_PATTERNS.items():
        print(f"  {tipo}: {len(patrones)} patrones")
    
    print("\nNamespaces XML configurados:")
    for namespace, url in XML_NAMESPACES.items():
        print(f"  {namespace}: {url}")

def main():
    """Función principal de ejemplos"""
    print("🤖 InvoiceBot - Ejemplos de Uso")
    print("=" * 40)
    
    # Verificar configuración
    if not os.path.exists('.env'):
        print("❌ Archivo .env no encontrado")
        print("Copia .env a .env y configura tus credenciales")
        return
    
    # Ejecutar ejemplos
    ejemplo_procesamiento_manual()
    ejemplo_crear_factura_desde_datos()
    ejemplo_configuracion_personalizada()
    
    # Preguntar si quiere ejecutar monitoreo
    respuesta = input("\n¿Quieres ejecutar el monitoreo de carpeta? (y/n): ")
    if respuesta.lower() == 'y':
        ejemplo_monitoreo_carpeta()

if __name__ == "__main__":
    main()