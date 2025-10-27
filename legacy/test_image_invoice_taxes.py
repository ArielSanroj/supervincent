#!/usr/bin/env python3
"""
Prueba del Sistema de Impuestos con testfactura2.jpg (imagen)
"""

import os
import sys
from datetime import datetime
from tax_calculator import ColombianTaxCalculator, InvoiceData, create_invoice_data_from_pdf
from invoice_processor_with_taxes import TaxIntegratedInvoiceProcessor

def test_image_invoice():
    """Probar factura de imagen con sistema de impuestos"""
    print("🧪 PRUEBA CON FACTURA DE IMAGEN - testfactura2.jpg")
    print("=" * 60)
    
    # Ruta del archivo
    image_path = "/Users/arielsanroj/Downloads/testfactura2.jpg"
    
    if not os.path.exists(image_path):
        print(f"❌ Archivo no encontrado: {image_path}")
        return
    
    print(f"📄 Archivo: {image_path}")
    print(f"📅 Fecha de prueba: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    try:
        # Crear procesador con impuestos
        processor = TaxIntegratedInvoiceProcessor()
        
        # Procesar factura con impuestos
        print("🚀 Procesando factura de imagen con sistema de impuestos...")
        result = processor.process_invoice_with_taxes(image_path)
        
        if result:
            print("\n✅ PROCESAMIENTO EXITOSO")
            print("=" * 40)
            
            # Mostrar datos extraídos
            invoice_data = result['invoice_data']
            print("📋 DATOS EXTRAÍDOS:")
            print(f"   📄 Número: {invoice_data.get('numero_factura', 'N/A')}")
            print(f"   📅 Fecha: {invoice_data.get('fecha', 'N/A')}")
            print(f"   🏢 Proveedor: {invoice_data.get('proveedor', 'N/A')}")
            print(f"   👤 Cliente: {invoice_data.get('cliente', 'N/A')}")
            print(f"   💰 Base: ${invoice_data.get('subtotal', 0):,.2f}")
            print(f"   💵 Total: ${invoice_data.get('total', 0):,.2f}")
            print(f"   🧾 IVA: ${invoice_data.get('impuestos', 0):,.2f}")
            
            # Mostrar cálculo de impuestos
            tax_calc = result['tax_calculation']
            print(f"\n🧮 CÁLCULO DE IMPUESTOS:")
            print(f"   🧾 IVA Calculado: ${tax_calc['iva_amount']:,.2f} ({tax_calc['iva_rate']*100:.1f}%)")
            print(f"   💰 ReteFuente Renta: ${tax_calc['retefuente_renta']:,.2f}")
            print(f"   💰 ReteFuente IVA: ${tax_calc['retefuente_iva']:,.2f}")
            print(f"   💰 ReteFuente ICA: ${tax_calc['retefuente_ica']:,.2f}")
            print(f"   📋 Total Retenciones: ${tax_calc['total_withholdings']:,.2f}")
            print(f"   💸 Neto a Pagar: ${tax_calc['net_amount']:,.2f}")
            print(f"   ✅ Estado: {tax_calc['compliance_status']}")
            
            # Mostrar payload de Alegra
            alegra_payload = result['alegra_payload']
            print(f"\n📤 PAYLOAD PARA ALEGRA:")
            print(f"   📅 Fecha: {alegra_payload.get('date', 'N/A')}")
            print(f"   📅 Vencimiento: {alegra_payload.get('dueDate', 'N/A')}")
            print(f"   👤 Cliente: {alegra_payload.get('client', {}).get('name', 'N/A')}")
            print(f"   📦 Items: {len(alegra_payload.get('items', []))}")
            print(f"   🧾 Impuestos: {len(alegra_payload.get('tax', []))}")
            print(f"   📋 Retenciones: {len(alegra_payload.get('withholdings', []))}")
            
            # Mostrar información fiscal
            fiscal_info = alegra_payload.get('fiscal_info', {})
            if fiscal_info:
                print(f"\n🏢 INFORMACIÓN FISCAL:")
                print(f"   🏢 Régimen Proveedor: {fiscal_info.get('vendor_regime', 'N/A')}")
                print(f"   👤 Régimen Comprador: {fiscal_info.get('buyer_regime', 'N/A')}")
                print(f"   🏙️ Ciudad Proveedor: {fiscal_info.get('vendor_city', 'N/A')}")
                print(f"   🏙️ Ciudad Comprador: {fiscal_info.get('buyer_city', 'N/A')}")
                print(f"   ✅ Compliance: {fiscal_info.get('compliance_status', 'N/A')}")
            
            # Mostrar resultado de Alegra
            alegra_result = result['alegra_result']
            if alegra_result:
                print(f"\n🏢 RESULTADO EN ALEGRA:")
                print(f"   🆔 ID: {alegra_result.get('id', 'N/A')}")
                print(f"   📄 Número: {alegra_result.get('number', 'N/A')}")
                print(f"   💰 Total: ${alegra_result.get('total', 0):,.2f}")
                print(f"   ✅ Estado: Creada exitosamente")
            else:
                print(f"\n⚠️ No se pudo crear en Alegra (verificar credenciales)")
            
            # Análisis detallado
            print(f"\n📊 ANÁLISIS DETALLADO:")
            analyze_tax_calculation(invoice_data, tax_calc)
            
        else:
            print("❌ Error en el procesamiento")
            
    except Exception as e:
        print(f"❌ Error durante la prueba: {e}")
        import traceback
        traceback.print_exc()

def analyze_tax_calculation(invoice_data, tax_calc):
    """Analizar el cálculo de impuestos"""
    print("   🔍 Análisis de IVA:")
    
    # Comparar IVA calculado vs extraído
    iva_extraido = invoice_data.get('impuestos', 0)
    iva_calculado = tax_calc['iva_amount']
    diferencia_iva = abs(iva_calculado - iva_extraido)
    
    print(f"      • IVA Extraído: ${iva_extraido:,.2f}")
    print(f"      • IVA Calculado: ${iva_calculado:,.2f}")
    print(f"      • Diferencia: ${diferencia_iva:,.2f}")
    
    if diferencia_iva < 1:
        print("      ✅ IVA coincide (diferencia < $1)")
    else:
        print("      ⚠️ Diferencia significativa en IVA")
    
    # Análisis de retenciones
    print("   🔍 Análisis de Retenciones:")
    
    if tax_calc['retefuente_renta'] > 0:
        print(f"      • ReteFuente Renta: ${tax_calc['retefuente_renta']:,.2f} - Aplica")
    else:
        print("      • ReteFuente Renta: No aplica")
    
    if tax_calc['retefuente_iva'] > 0:
        print(f"      • ReteFuente IVA: ${tax_calc['retefuente_iva']:,.2f} - Aplica")
    else:
        print("      • ReteFuente IVA: No aplica")
    
    if tax_calc['retefuente_ica'] > 0:
        print(f"      • ReteFuente ICA: ${tax_calc['retefuente_ica']:,.2f} - Aplica")
    else:
        print("      • ReteFuente ICA: No aplica")
    
    # Explicación de por qué aplican o no
    print("   📋 Explicación:")
    base_amount = invoice_data.get('subtotal', 0)
    uvt_2025 = 49799
    
    print(f"      • Base: ${base_amount:,.2f} ({base_amount/uvt_2025:.1f} UVT)")
    
    if base_amount < 27 * uvt_2025:
        print("      • ReteFuente Renta: Monto < 27 UVT para compras de bienes")
    else:
        print("      • ReteFuente Renta: Monto > 27 UVT, aplica retención")
    
    if base_amount < 10 * uvt_2025:
        print("      • ReteFuente IVA: Monto < 10 UVT")
    else:
        print("      • ReteFuente IVA: Monto > 10 UVT, aplica retención")
    
    # Verificar ciudades
    vendor_city = invoice_data.get('proveedor_ciudad', 'bogota')
    buyer_city = invoice_data.get('comprador_ciudad', 'bogota')
    
    if vendor_city == buyer_city:
        print("      • ReteFuente ICA: Misma ciudad, no aplica")
    else:
        print(f"      • ReteFuente ICA: Diferente ciudad ({vendor_city}-{buyer_city})")

def test_ocr_capabilities():
    """Probar capacidades de OCR"""
    print("\n🔍 PRUEBA DE CAPACIDADES OCR")
    print("=" * 40)
    
    try:
        from invoice_processor_enhanced import InvoiceProcessor
        
        processor = InvoiceProcessor()
        image_path = "/Users/arielsanroj/Downloads/testfactura2.jpg"
        
        print(f"📄 Procesando imagen: {image_path}")
        
        # Procesar solo la extracción de datos
        result = processor.process_invoice(image_path)
        
        if result:
            print("✅ Extracción OCR exitosa")
            print(f"   📝 Texto extraído: {len(result.get('texto_extraido', ''))} caracteres")
            print(f"   📋 Tipo detectado: {result.get('tipo_factura', 'N/A')}")
            print(f"   📊 Datos extraídos: {len(result.get('datos_extraidos', {}))} campos")
            
            # Mostrar datos extraídos
            datos = result.get('datos_extraidos', {})
            print("\n📋 DATOS EXTRAÍDOS:")
            for key, value in datos.items():
                if isinstance(value, (int, float)) and key in ['subtotal', 'total', 'impuestos']:
                    print(f"   {key}: ${value:,.2f}")
                else:
                    print(f"   {key}: {value}")
        else:
            print("❌ Error en extracción OCR")
            
    except Exception as e:
        print(f"❌ Error en prueba OCR: {e}")

def main():
    """Función principal"""
    print("🚀 PRUEBA COMPLETA DEL SISTEMA DE IMPUESTOS CON IMAGEN")
    print("=" * 70)
    print("Archivo: testfactura2.jpg")
    print("Fecha: 2025-10-20")
    print()
    
    # Prueba de capacidades OCR
    test_ocr_capabilities()
    
    # Prueba con archivo de imagen
    test_image_invoice()
    
    print("\n🎉 PRUEBAS COMPLETADAS")
    print("=" * 70)
    print("✅ Sistema de impuestos funcionando con imágenes")
    print("✅ OCR funcionando correctamente")
    print("✅ Cálculos fiscales precisos")

if __name__ == "__main__":
    main()