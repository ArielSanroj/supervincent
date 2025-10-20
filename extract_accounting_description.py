#!/usr/bin/env python3
"""
Script para extraer descripción contable de archivos PDF y Excel
"""

import pdfplumber
import pandas as pd
import re
import sys
from datetime import datetime
from pathlib import Path

def extract_pdf_accounting_description(pdf_path):
    """Extraer descripción contable de un archivo PDF"""
    print(f"📄 Procesando PDF: {pdf_path}")
    print("=" * 60)
    
    try:
        with pdfplumber.open(pdf_path) as pdf:
            texto = ''
            for page in pdf.pages:
                texto += page.extract_text() or ''
        
        print("📝 Texto extraído del PDF:")
        print("-" * 40)
        print(texto[:800] + "..." if len(texto) > 800 else texto)
        print("-" * 40)
        
        # Extraer información contable específica
        accounting_info = {
            'fecha': extract_date(texto),
            'numero_factura': extract_invoice_number(texto),
            'vendedor_proveedor': extract_vendor(texto),
            'cliente_comprador': extract_client(texto),
            'productos_servicios': extract_products(texto),
            'valores': extract_values(texto),
            'impuestos': extract_taxes(texto),
            'total': extract_total(texto),
            'tipo_factura': detect_invoice_type(texto)
        }
        
        return accounting_info
        
    except Exception as e:
        print(f"❌ Error procesando PDF: {e}")
        return None

def extract_excel_accounting_description(excel_path):
    """Extraer descripción contable de un archivo Excel"""
    print(f"📊 Procesando Excel: {excel_path}")
    print("=" * 60)
    
    try:
        # Leer todas las hojas del Excel
        excel_file = pd.ExcelFile(excel_path)
        print(f"📋 Hojas disponibles: {excel_file.sheet_names}")
        
        accounting_info = {
            'hojas': excel_file.sheet_names,
            'datos_por_hoja': {}
        }
        
        for sheet_name in excel_file.sheet_names:
            print(f"\n📊 Procesando hoja: {sheet_name}")
            df = pd.read_excel(excel_path, sheet_name=sheet_name)
            
            print(f"   Dimensiones: {df.shape[0]} filas x {df.shape[1]} columnas")
            print(f"   Columnas: {list(df.columns)}")
            
            # Mostrar primeras filas
            print("   Primeras 5 filas:")
            print(df.head().to_string())
            
            accounting_info['datos_por_hoja'][sheet_name] = {
                'dimensiones': df.shape,
                'columnas': list(df.columns),
                'datos': df.to_dict('records')[:10]  # Primeras 10 filas
            }
        
        return accounting_info
        
    except Exception as e:
        print(f"❌ Error procesando Excel: {e}")
        return None

def extract_date(texto):
    """Extraer fecha del texto"""
    patterns = [
        r'Fecha:\s*(\d{1,2}[-/]\d{1,2}[-/]\d{4})',
        r'(\d{1,2}[-/]\d{1,2}[-/]\d{4})',
        r'(\d{4}[-/]\d{1,2}[-/]\d{1,2})'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, texto)
        if match:
            return match.group(1)
    return "Fecha no encontrada"

def extract_invoice_number(texto):
    """Extraer número de factura"""
    patterns = [
        r'Factura\s*#?\s*(\d+)',
        r'No\.\s*(\d+)',
        r'Número:\s*(\d+)',
        r'#\s*(\d+)'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, texto, re.IGNORECASE)
        if match:
            return match.group(1)
    return "Número no encontrado"

def extract_vendor(texto):
    """Extraer vendedor/proveedor"""
    patterns = [
        r'Factura electrónica de venta #\d+\n([^\n]+)',
        r'Vendedor:\s*([^\n]+)',
        r'Proveedor:\s*([^\n]+)',
        r'De:\s*([^\n]+)'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, texto, re.IGNORECASE)
        if match:
            return match.group(1).strip()
    return "Vendedor no encontrado"

def extract_client(texto):
    """Extraer cliente/comprador"""
    patterns = [
        r'Para:\s*([^\n]+)',
        r'Cliente:\s*([^\n]+)',
        r'Comprador:\s*([^\n]+)',
        r'Adquiriente:\s*([^\n]+)'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, texto, re.IGNORECASE)
        if match:
            return match.group(1).strip()
    return "Cliente no encontrado"

def extract_products(texto):
    """Extraer productos/servicios"""
    products = []
    
    # Buscar patrones de productos
    patterns = [
        r'(\d+)\s*-\s*(.+?)(?=\s*Impuestos|\s*Total|\s*Subtotal)',
        r'Descripción:\s*([^\n]+)',
        r'Producto:\s*([^\n]+)',
        r'Servicio:\s*([^\n]+)'
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, texto, re.DOTALL | re.IGNORECASE)
        for match in matches:
            if isinstance(match, tuple):
                products.append(f"{match[0]} - {match[1].strip()}")
            else:
                products.append(match.strip())
    
    return products if products else ["Producto no identificado"]

def extract_values(texto):
    """Extraer valores monetarios"""
    values = {}
    
    # Buscar precios unitarios
    price_match = re.search(r'Precio unit\.?\s*\$?([\d,]+\.?\d*)', texto, re.IGNORECASE)
    if price_match:
        values['precio_unitario'] = float(price_match.group(1).replace(',', ''))
    
    # Buscar cantidad
    qty_match = re.search(r'(\d+)\s+Unidad', texto, re.IGNORECASE)
    if qty_match:
        values['cantidad'] = float(qty_match.group(1))
    
    # Buscar subtotal
    subtotal_match = re.search(r'Subtotal\s*\$?([\d,]+\.?\d*)', texto, re.IGNORECASE)
    if subtotal_match:
        values['subtotal'] = float(subtotal_match.group(1).replace(',', ''))
    
    return values

def extract_taxes(texto):
    """Extraer información de impuestos"""
    taxes = {}
    
    # Buscar IVA
    iva_match = re.search(r'IVA\s*\$?([\d,]+\.?\d*)', texto, re.IGNORECASE)
    if iva_match:
        taxes['iva'] = float(iva_match.group(1).replace(',', ''))
    
    # Buscar impuestos generales
    tax_match = re.search(r'Impuestos?\s*\$?([\d,]+\.?\d*)', texto, re.IGNORECASE)
    if tax_match:
        taxes['impuestos'] = float(tax_match.group(1).replace(',', ''))
    
    return taxes

def extract_total(texto):
    """Extraer total"""
    patterns = [
        r'Total\s*\$?([\d,]+\.?\d*)',
        r'Total a pagar\s*\$?([\d,]+\.?\d*)',
        r'Valor total\s*\$?([\d,]+\.?\d*)'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, texto, re.IGNORECASE)
        if match:
            return float(match.group(1).replace(',', ''))
    return 0.0

def detect_invoice_type(texto):
    """Detectar tipo de factura"""
    if any(word in texto.lower() for word in ['compra', 'proveedor', 'adquiriente']):
        return 'COMPRA'
    elif any(word in texto.lower() for word in ['venta', 'cliente', 'vendedor']):
        return 'VENTA'
    else:
        return 'NO DETERMINADO'

def format_accounting_description(info, file_type):
    """Formatear descripción contable"""
    print(f"\n📋 DESCRIPCIÓN CONTABLE - {file_type.upper()}")
    print("=" * 60)
    
    if file_type == 'PDF':
        print(f"📅 Fecha: {info['fecha']}")
        print(f"📄 Número de Factura: {info['numero_factura']}")
        print(f"🏢 {'Proveedor' if info['tipo_factura'] == 'COMPRA' else 'Vendedor'}: {info['vendedor_proveedor']}")
        print(f"👤 {'Comprador' if info['tipo_factura'] == 'COMPRA' else 'Cliente'}: {info['cliente_comprador']}")
        print(f"📦 Productos/Servicios:")
        for i, product in enumerate(info['productos_servicios'], 1):
            print(f"   {i}. {product}")
        
        if info['valores']:
            print(f"💰 Valores:")
            for key, value in info['valores'].items():
                print(f"   {key.replace('_', ' ').title()}: ${value:,.2f}")
        
        if info['impuestos']:
            print(f"🧾 Impuestos:")
            for key, value in info['impuestos'].items():
                print(f"   {key.upper()}: ${value:,.2f}")
        
        print(f"💵 Total: ${info['total']:,.2f}")
        print(f"📋 Tipo: {info['tipo_factura']}")
    
    elif file_type == 'EXCEL':
        print(f"📊 Archivo Excel procesado")
        print(f"📋 Hojas: {', '.join(info['hojas'])}")
        
        for sheet_name, sheet_data in info['datos_por_hoja'].items():
            print(f"\n📊 Hoja: {sheet_name}")
            print(f"   Dimensiones: {sheet_data['dimensiones'][0]} filas x {sheet_data['dimensiones'][1]} columnas")
            print(f"   Columnas: {', '.join(sheet_data['columnas'])}")
            
            if sheet_data['datos']:
                print(f"   Primeras filas de datos:")
                for i, row in enumerate(sheet_data['datos'][:3], 1):
                    print(f"     Fila {i}: {row}")

def main():
    """Función principal"""
    print("🔍 EXTRACTOR DE DESCRIPCIÓN CONTABLE")
    print("=" * 60)
    
    # Procesar PDF
    pdf_path = "/Users/arielsanroj/Downloads/testfactura.pdf"
    if Path(pdf_path).exists():
        pdf_info = extract_pdf_accounting_description(pdf_path)
        if pdf_info:
            format_accounting_description(pdf_info, 'PDF')
    else:
        print(f"❌ Archivo PDF no encontrado: {pdf_path}")
    
    print("\n" + "=" * 60)
    
    # Procesar Excel
    excel_path = "/Users/arielsanroj/Downloads/testastra.xlsx"
    if Path(excel_path).exists():
        excel_info = extract_excel_accounting_description(excel_path)
        if excel_info:
            format_accounting_description(excel_info, 'EXCEL')
    else:
        print(f"❌ Archivo Excel no encontrado: {excel_path}")

if __name__ == "__main__":
    main()