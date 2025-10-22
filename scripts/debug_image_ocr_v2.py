#!/usr/bin/env python3
"""
Debug del OCR para testfactura2.jpg - Acceso directo al texto
"""

import os
import pytesseract
from PIL import Image
import cv2
import numpy as np

def preprocess_image_for_ocr(image):
    """Preprocesar imagen para mejorar OCR"""
    # Convertir a escala de grises
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
    else:
        gray = image
    
    # Aplicar filtro gaussiano para reducir ruido
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    
    # Aplicar umbralización adaptativa
    thresh = cv2.adaptiveThreshold(
        blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
    )
    
    # Morfología para limpiar
    kernel = np.ones((1, 1), np.uint8)
    cleaned = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
    
    return cleaned

def debug_image_ocr():
    """Debug del OCR de la imagen"""
    print("🔍 DEBUG OCR - testfactura2.jpg")
    print("=" * 50)
    
    image_path = "/Users/arielsanroj/Downloads/testfactura2.jpg"
    
    if not os.path.exists(image_path):
        print(f"❌ Archivo no encontrado: {image_path}")
        return
    
    try:
        # Cargar imagen
        print("🚀 Cargando imagen...")
        image = Image.open(image_path)
        print(f"✅ Imagen cargada: {image.size} píxeles")
        
        # Convertir a OpenCV para preprocesamiento
        image_cv = np.array(image)
        
        # Preprocesar imagen
        print("🔧 Preprocesando imagen...")
        processed_image = preprocess_image_for_ocr(image_cv)
        
        # Extraer texto usando OCR
        print("📝 Extrayendo texto con OCR...")
        texto = pytesseract.image_to_string(processed_image, lang='spa+eng')
        
        if not texto.strip():
            print("❌ No se pudo extraer texto de la imagen")
            return
        
        print(f"✅ Texto extraído ({len(texto)} caracteres):")
        print("-" * 50)
        print(texto)
        print("-" * 50)
        
        # Análisis del texto
        print("\n🔍 ANÁLISIS DEL TEXTO:")
        lines = texto.split('\n')
        for i, line in enumerate(lines):
            if line.strip():
                print(f"Línea {i+1}: {line.strip()}")
        
        # Buscar patrones específicos
        print("\n🔍 BÚSQUEDA DE PATRONES:")
        
        # Buscar números que podrían ser montos
        import re
        numbers = re.findall(r'\$?[\d,]+\.?\d*', texto)
        if numbers:
            print(f"💰 Números encontrados: {numbers}")
        
        # Buscar fechas
        dates = re.findall(r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}', texto)
        if dates:
            print(f"📅 Fechas encontradas: {dates}")
        
        # Buscar NITs
        nits = re.findall(r'\d{6,12}[-]?\d?', texto)
        if nits:
            print(f"🆔 NITs encontrados: {nits}")
        
        # Buscar palabras clave de factura
        keywords = ['factura', 'invoice', 'total', 'subtotal', 'iva', 'nit', 'fecha', 'fecha']
        found_keywords = []
        for keyword in keywords:
            if keyword.lower() in texto.lower():
                found_keywords.append(keyword)
        
        if found_keywords:
            print(f"🔑 Palabras clave encontradas: {found_keywords}")
        
        # Análisis de calidad del OCR
        print(f"\n📊 ANÁLISIS DE CALIDAD:")
        print(f"   • Caracteres totales: {len(texto)}")
        print(f"   • Líneas no vacías: {len([l for l in lines if l.strip()])}")
        print(f"   • Números encontrados: {len(numbers)}")
        print(f"   • Palabras clave: {len(found_keywords)}")
        
        if len(texto) < 100:
            print("   ⚠️ Texto muy corto, posible problema de OCR")
        elif len(numbers) == 0:
            print("   ⚠️ No se encontraron números, posible problema de OCR")
        else:
            print("   ✅ Calidad de OCR parece aceptable")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_image_ocr()