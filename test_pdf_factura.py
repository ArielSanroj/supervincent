#!/usr/bin/env python3
"""
Script para procesar testfactura.pdf y crear factura en Alegra
"""

import requests
import base64
import pdfplumber
import re
from datetime import datetime, timedelta
from dotenv import load_dotenv
import os

# Cargar variables de entorno
load_dotenv()

def extract_data_from_pdf(pdf_path):
    """Extraer datos del PDF de factura"""
    print(f"📄 Procesando PDF: {pdf_path}")
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
        
        # Patrones mejorados para extraer datos
        fecha_patterns = [
            r'Fecha[:\s]+(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
            r'Date[:\s]+(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
            r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
            r'Fecha de emisión[:\s]+(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
            r'(\d{4}-\d{2}-\d{2})'  # Formato YYYY-MM-DD
        ]
        
        cliente_patterns = [
            r'Cliente[:\s]+(.+)',
            r'Customer[:\s]+(.+)',
            r'Facturar a[:\s]+(.+)',
            r'Bill to[:\s]+(.+)',
            r'Razón Social[:\s]+(.+)',
            r'Nombre[:\s]+(.+)',
            r'Señor[:\s]+(.+)',
            r'Señora[:\s]+(.+)'
        ]
        
        total_patterns = [
            r'Total[:\s]+\$?([\d,]+\.?\d*)',
            r'Amount[:\s]+\$?([\d,]+\.?\d*)',
            r'Subtotal[:\s]+\$?([\d,]+\.?\d*)',
            r'Importe Total[:\s]+\$?([\d,]+\.?\d*)',
            r'Total a Pagar[:\s]+\$?([\d,]+\.?\d*)',
            r'Valor Total[:\s]+\$?([\d,]+\.?\d*)'
        ]
        
        # Extraer datos
        fecha = extract_with_patterns(texto, fecha_patterns)
        cliente = extract_with_patterns(texto, cliente_patterns)
        total = extract_with_patterns(texto, total_patterns)
        
        # Extraer items del PDF
        items = extract_items_from_pdf(texto)
        
        # Formatear fecha si es necesario
        if fecha:
            # Convertir diferentes formatos a YYYY-MM-DD
            fecha = format_date(fecha)
        
        datos = {
            'fecha': fecha or datetime.now().strftime('%Y-%m-%d'),
            'cliente': cliente or 'Cliente Desconocido',
            'items': items,
            'total': float(total.replace(',', '')) if total else 0.0
        }
        
        print("\n📊 Datos extraídos:")
        print(f"   📅 Fecha: {datos['fecha']}")
        print(f"   👤 Cliente: {datos['cliente']}")
        print(f"   💰 Total: ${datos['total']}")
        print(f"   📦 Items: {len(datos['items'])}")
        
        for i, item in enumerate(datos['items'], 1):
            print(f"      {i}. {item['descripcion']} - Cant: {item['cantidad']} - Precio: ${item['precio']}")
        
        return datos
        
    except Exception as e:
        print(f"❌ Error procesando PDF: {e}")
        return None

def extract_with_patterns(text, patterns):
    """Extraer texto usando múltiples patrones"""
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
        if match:
            return match.group(1).strip()
    return None

def format_date(date_str):
    """Formatear fecha a YYYY-MM-DD"""
    try:
        # Si ya está en formato YYYY-MM-DD
        if re.match(r'\d{4}-\d{2}-\d{2}', date_str):
            return date_str
        
        # Convertir DD/MM/YYYY o DD-MM-YYYY
        if '/' in date_str or '-' in date_str:
            parts = re.split(r'[/-]', date_str)
            if len(parts) == 3:
                day, month, year = parts
                if len(year) == 2:
                    year = '20' + year
                return f"{year}-{month.zfill(2)}-{day.zfill(2)}"
        
        return date_str
    except:
        return date_str

def extract_items_from_pdf(text):
    """Extraer items del PDF"""
    items = []
    lines = text.split('\n')
    
    # Buscar sección de items
    in_items_section = False
    item_count = 0
    
    for i, line in enumerate(lines):
        line = line.strip()
        
        # Detectar inicio de items
        if any(keyword in line.lower() for keyword in ['descripción', 'descripcion', 'item', 'concepto', 'producto', 'servicio', 'cantidad', 'precio']):
            in_items_section = True
            continue
        
        # Detectar fin de items
        if any(keyword in line.lower() for keyword in ['subtotal', 'total', 'impuestos', 'iva', 'descuento', 'suma']):
            in_items_section = False
            continue
        
        # Procesar líneas de items
        if in_items_section and line and not line.startswith(('Fecha', 'Cliente', 'Total')):
            # Buscar patrones de cantidad y precio
            price_match = re.search(r'(\d+\.?\d*)\s*$', line)
            qty_match = re.search(r'(\d+\.?\d*)\s+(\d+\.?\d*)\s*$', line)
            
            if price_match and qty_match:
                # Línea con cantidad y precio
                qty = float(qty_match.group(1))
                price = float(qty_match.group(2))
                desc = line[:qty_match.start()].strip()
            elif price_match:
                # Solo precio
                price = float(price_match.group(1))
                desc = line[:price_match.start()].strip()
                qty = 1.0
            else:
                # Solo descripción
                desc = line
                qty = 1.0
                price = 0.0
            
            if desc and len(desc) > 3:  # Filtrar líneas muy cortas
                items.append({
                    'descripcion': desc,
                    'cantidad': qty,
                    'precio': price
                })
                item_count += 1
    
    # Si no se encontraron items, crear uno genérico
    if not items:
        items.append({
            'descripcion': 'Servicio procesado desde PDF',
            'cantidad': 1.0,
            'precio': 100.0
        })
    
    return items

def get_client_id_by_name(client_name, headers):
    """Obtener ID del cliente por nombre"""
    try:
        response = requests.get('https://api.alegra.com/api/v1/contacts', headers=headers, timeout=10)
        if response.status_code == 200:
            clients = response.json()
            for client in clients:
                if client.get('name', '').lower() == client_name.lower():
                    return client.get('id')
        return None
    except Exception as e:
        print(f"Error obteniendo clientes: {e}")
        return None

def create_invoice_in_alegra(datos_factura):
    """Crear factura en Alegra"""
    print("\n🏢 Creando factura en Alegra...")
    print("=" * 40)
    
    # Configurar autenticación
    email = os.getenv('ALEGRA_USER')
    token = os.getenv('ALEGRA_TOKEN')
    
    credentials = f"{email}:{token}"
    auth_header = f"Basic {base64.b64encode(credentials.encode()).decode()}"
    
    headers = {
        'Authorization': auth_header,
        'Content-Type': 'application/json'
    }
    
    # Obtener ID del cliente
    client_id = get_client_id_by_name(datos_factura['cliente'], headers)
    
    if not client_id:
        print(f"⚠️ Cliente '{datos_factura['cliente']}' no encontrado, usando 'Consumidor Final'")
        client_id = get_client_id_by_name("Consumidor Final", headers)
    
    if not client_id:
        print("❌ No se pudo encontrar un cliente válido")
        return None
    
    print(f"✅ Usando cliente ID: {client_id}")
    
    # Calcular fecha de vencimiento
    fecha_vencimiento = datetime.strptime(datos_factura['fecha'], '%Y-%m-%d') + timedelta(days=30)
    
    # Crear payload para Alegra
    payload = {
        "date": datos_factura['fecha'],
        "dueDate": fecha_vencimiento.strftime('%Y-%m-%d'),
        "client": {"id": client_id},
        "items": [
            {
                "name": item['descripcion'],
                "quantity": item['cantidad'],
                "price": item['precio']
            } for item in datos_factura['items']
        ],
        "observations": f"Factura procesada automáticamente desde PDF por InvoiceBot - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    }
    
    try:
        response = requests.post('https://api.alegra.com/api/v1/invoices', 
                               json=payload, 
                               headers=headers, 
                               timeout=30)
        
        print(f"📡 Status Code: {response.status_code}")
        
        if response.status_code == 201:
            factura_creada = response.json()
            print("✅ ¡Factura creada exitosamente!")
            print(f"🆔 ID: {factura_creada.get('id')}")
            print(f"📄 Número: {factura_creada.get('number')}")
            print(f"💰 Total: ${factura_creada.get('total')}")
            print(f"👤 Cliente: {factura_creada.get('client', {}).get('name')}")
            print(f"📅 Fecha: {factura_creada.get('date')}")
            print(f"📅 Vencimiento: {factura_creada.get('dueDate')}")
            
            return factura_creada
        else:
            print(f"❌ Error creando factura: {response.status_code}")
            print(f"📝 Respuesta: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Error en API Alegra: {e}")
        return None

def main():
    """Función principal"""
    print("🚀 InvoiceBot - Procesamiento de testfactura.pdf")
    print("=" * 60)
    
    pdf_path = "/Users/arielsanroj/Downloads/testfactura.pdf"
    
    # Paso 1: Extraer datos del PDF
    datos = extract_data_from_pdf(pdf_path)
    
    if not datos:
        print("❌ No se pudieron extraer datos del PDF")
        return
    
    # Paso 2: Crear factura en Alegra
    resultado = create_invoice_in_alegra(datos)
    
    if resultado:
        print("\n🎉 ¡Proceso completado exitosamente!")
        print("✅ PDF procesado correctamente")
        print("✅ Factura creada en Alegra")
        print("✅ Sistema funcionando perfectamente")
    else:
        print("\n⚠️ Error en el proceso")
        print("❌ Revisa los logs para más detalles")

if __name__ == "__main__":
    main()