#!/usr/bin/env python3
"""
Script para procesar factura de COMPRA automáticamente
"""

import requests
import base64
import pdfplumber
import re
import json
from datetime import datetime, timedelta
from dotenv import load_dotenv
import os

# Cargar variables de entorno
load_dotenv()

def extract_data_from_pdf(pdf_path):
    """Extraer datos del PDF de factura de compra"""
    print(f"📄 Procesando PDF de COMPRA: {pdf_path}")
    print("=" * 50)
    
    try:
        with pdfplumber.open(pdf_path) as pdf:
            texto = ''
            for page in pdf.pages:
                texto += page.extract_text() or ''
        
        print("📝 Texto extraído del PDF:")
        print("-" * 30)
        print(texto[:500] + "..." if len(texto) > 500 else texto)
        print("-" * 30)
        
        # Extraer datos específicos de esta factura
        fecha_match = re.search(r'Fecha:\s*(\d{1,2}-\d{1,2}-\d{4})', texto)
        fecha = fecha_match.group(1) if fecha_match else datetime.now().strftime('%Y-%m-%d')
        
        # Formatear fecha
        if '-' in fecha:
            parts = fecha.split('-')
            if len(parts) == 3:
                day, month, year = parts
                fecha = f"{year}-{month.zfill(2)}-{day.zfill(2)}"
        
        # Extraer proveedor
        vendedor_match = re.search(r'Factura electrónica de venta #\d+\n([^\n]+)', texto)
        proveedor = vendedor_match.group(1).strip() if vendedor_match else "Proveedor Desconocido"
        
        # Extraer producto específico
        producto_match = re.search(r'(\d+)\s*-\s*(.+?)\s*Impuestos:', texto, re.DOTALL)
        if producto_match:
            codigo = producto_match.group(1)
            descripcion = producto_match.group(2).strip()
            producto = f"{codigo} - {descripcion}"
        else:
            producto = "Producto no identificado"
        
        # Extraer precios
        price_match = re.search(r'Precio unit\.\s*\$?([\d,]+\.?\d*)', texto)
        precio_unitario = float(price_match.group(1).replace(',', '')) if price_match else 0.0
        
        qty_match = re.search(r'(\d+)\s+Unidad', texto)
        cantidad = float(qty_match.group(1)) if qty_match else 1.0
        
        # Extraer totales
        total_match = re.search(r'Total[:\s]+\d+\s+Unidad\s+\$?([\d,]+\.?\d*)', texto)
        if not total_match:
            total_match = re.search(r'Total[:\s]+\$?([\d,]+\.?\d*)', texto)
        total = float(total_match.group(1).replace(',', '')) if total_match else 0.0
        
        subtotal_match = re.search(r'Subtotal\s+\$?([\d,]+\.?\d*)', texto)
        subtotal = float(subtotal_match.group(1).replace(',', '')) if subtotal_match else precio_unitario
        
        impuestos_match = re.search(r'Impuestos\s+\$?([\d,]+\.?\d*)', texto)
        impuestos = float(impuestos_match.group(1).replace(',', '')) if impuestos_match else 0.0
        
        datos = {
            'tipo': 'compra',
            'fecha': fecha,
            'proveedor': proveedor,
            'items': [{
                'descripcion': producto,
                'cantidad': cantidad,
                'precio': precio_unitario
            }],
            'subtotal': subtotal,
            'impuestos': impuestos,
            'total': total
        }
        
        print(f"\n📊 Datos extraídos del PDF:")
        print(f"   📅 Fecha: {datos['fecha']}")
        print(f"   🏪 Proveedor: {datos['proveedor']}")
        print(f"   📦 Producto: {datos['items'][0]['descripcion']}")
        print(f"   📊 Cantidad: {datos['items'][0]['cantidad']}")
        print(f"   💵 Precio Unitario: ${datos['items'][0]['precio']:,.2f}")
        print(f"   💰 Subtotal: ${datos['subtotal']:,.2f}")
        print(f"   🧾 Impuestos: ${datos['impuestos']:,.2f}")
        print(f"   💰 Total: ${datos['total']:,.2f}")
        
        return datos
        
    except Exception as e:
        print(f"❌ Error procesando PDF: {e}")
        return None

def register_purchase_invoice(datos_factura):
    """Registrar factura de compra en el sistema"""
    print(f"\n📥 Registrando factura de COMPRA en el sistema...")
    print("=" * 50)
    
    # Crear archivo de registro
    registro_file = f"facturas_compra_{datetime.now().strftime('%Y%m%d')}.txt"
    
    registro_entry = f"""
FACTURA DE COMPRA REGISTRADA
============================
Fecha: {datos_factura['fecha']}
Proveedor: {datos_factura['proveedor']}
Producto: {datos_factura['items'][0]['descripcion']}
Cantidad: {datos_factura['items'][0]['cantidad']}
Precio Unitario: ${datos_factura['items'][0]['precio']:,.2f}
Subtotal: ${datos_factura['subtotal']:,.2f}
Impuestos: ${datos_factura['impuestos']:,.2f}
Total: ${datos_factura['total']:,.2f}
Registrado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
============================
"""
    
    try:
        with open(registro_file, 'a', encoding='utf-8') as f:
            f.write(registro_entry)
        
        print("✅ Factura de compra registrada exitosamente!")
        print(f"📁 Archivo de registro: {registro_file}")
        print(f"📊 Total registrado: ${datos_factura['total']:,.2f}")
        print(f"🏪 Proveedor: {datos_factura['proveedor']}")
        
        # También crear un registro JSON para futuras integraciones
        json_file = f"facturas_compra_{datetime.now().strftime('%Y%m%d')}.json"
        
        registro_json = {
            "tipo": "compra",
            "fecha": datos_factura['fecha'],
            "proveedor": datos_factura['proveedor'],
            "items": datos_factura['items'],
            "subtotal": datos_factura['subtotal'],
            "impuestos": datos_factura['impuestos'],
            "total": datos_factura['total'],
            "registrado": datetime.now().isoformat()
        }
        
        # Cargar registros existentes o crear lista vacía
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                registros = json.load(f)
        except FileNotFoundError:
            registros = []
        
        registros.append(registro_json)
        
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(registros, f, indent=2, ensure_ascii=False)
        
        print(f"📄 Archivo JSON: {json_file}")
        
        # Mostrar resumen de todas las facturas de compra del día
        print(f"\n📊 Resumen de facturas de compra del día:")
        print(f"   📅 Fecha: {datetime.now().strftime('%Y-%m-%d')}")
        print(f"   📄 Total de facturas: {len(registros)}")
        
        total_dia = sum(factura['total'] for factura in registros)
        print(f"   💰 Total del día: ${total_dia:,.2f}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error registrando factura de compra: {e}")
        return False

def show_purchase_summary():
    """Mostrar resumen de facturas de compra"""
    print(f"\n📊 Resumen de Facturas de Compra")
    print("=" * 40)
    
    json_file = f"facturas_compra_{datetime.now().strftime('%Y%m%d')}.json"
    
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            registros = json.load(f)
        
        if registros:
            print(f"📅 Fecha: {datetime.now().strftime('%Y-%m-%d')}")
            print(f"📄 Total de facturas: {len(registros)}")
            
            total_dia = sum(factura['total'] for factura in registros)
            print(f"💰 Total del día: ${total_dia:,.2f}")
            
            print(f"\n📋 Lista de facturas:")
            for i, factura in enumerate(registros, 1):
                print(f"   {i}. {factura['proveedor']} - ${factura['total']:,.2f}")
        else:
            print("❌ No hay facturas de compra registradas hoy")
            
    except FileNotFoundError:
        print("❌ No hay archivo de facturas de compra para hoy")

def main():
    """Función principal"""
    print("🚀 InvoiceBot - Procesador de Facturas de COMPRA")
    print("=" * 60)
    
    pdf_path = "/Users/arielsanroj/Downloads/testfactura.pdf"
    
    # Paso 1: Extraer datos del PDF
    datos = extract_data_from_pdf(pdf_path)
    
    if not datos:
        print("❌ No se pudieron extraer datos del PDF")
        return
    
    # Paso 2: Registrar factura de compra
    resultado = register_purchase_invoice(datos)
    
    if resultado:
        print("\n🎉 ¡Factura de COMPRA registrada exitosamente!")
        print("✅ Se guardó en el sistema local")
        print("✅ Lista para procesamiento contable")
        print("✅ No se creó en Alegra (es factura de compra)")
        
        # Mostrar resumen
        show_purchase_summary()
    else:
        print("\n⚠️ Error en el proceso")
        print("❌ Revisa los logs para más detalles")

if __name__ == "__main__":
    main()