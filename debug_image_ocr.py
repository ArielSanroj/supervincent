#!/usr/bin/env python3
"""
Debug del OCR para testfactura2.jpg
"""

import os
from invoice_processor_enhanced import InvoiceProcessor

def debug_image_ocr():
    """Debug del OCR de la imagen"""
    print("🔍 DEBUG OCR - testfactura2.jpg")
    print("=" * 50)
    
    image_path = "/Users/arielsanroj/Downloads/testfactura2.jpg"
    
    if not os.path.exists(image_path):
        print(f"❌ Archivo no encontrado: {image_path}")
        return
    
    try:
        processor = InvoiceProcessor()
        
        # Procesar imagen
        print("🚀 Procesando imagen...")
        result = processor.extract_data_from_image(image_path)
        
        if result:
            print("✅ Procesamiento exitoso")
            print(f"📝 Texto extraído ({len(result)} caracteres):")
            print("-" * 50)
            print(result)
            print("-" * 50)
            
            # Intentar extraer datos manualmente
            print("\n🔍 ANÁLISIS MANUAL DEL TEXTO:")
            lines = result.split('\n')
            for i, line in enumerate(lines):
                if line.strip():
                    print(f"Línea {i+1}: {line.strip()}")
            
            # Buscar patrones específicos
            print("\n🔍 BÚSQUEDA DE PATRONES:")
            
            # Buscar números que podrían ser montos
            import re
            numbers = re.findall(r'\$?[\d,]+\.?\d*', result)
            if numbers:
                print(f"💰 Números encontrados: {numbers}")
            
            # Buscar fechas
            dates = re.findall(r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}', result)
            if dates:
                print(f"📅 Fechas encontradas: {dates}")
            
            # Buscar NITs
            nits = re.findall(r'\d{6,12}[-]?\d?', result)
            if nits:
                print(f"🆔 NITs encontrados: {nits}")
            
        else:
            print("❌ No se pudo extraer texto de la imagen")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_image_ocr()