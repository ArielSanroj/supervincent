#!/usr/bin/env python3
"""
Script final mejorado para procesar testfactura.pdf
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
    """Extraer datos del PDF de factura con mejor parsing"""
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
        
        # Extraer fecha
        fecha_match = re.search(r'Fecha:\s*(\d{1,2}-\d{1,2}-\d{4})', texto)
        fecha = fecha_match.group(1) if fecha_match else datetime.now().strftime('%Y-%m-%d')
        
        # Formatear fecha
        if '-' in fecha:
            parts = fecha.split('-')
            if len(parts) == 3:
                day, month, year = parts
                fecha = f"{year}-{month.zfill(2)}-{day.zfill(2)}"
        
        # Extraer total correctamente
        total_match = re.search(r'Total[:\s]+\$?([\d,]+\.?\d*)', texto)
        if not total_match:
            # Buscar otros patrones de total
            total_match = re.search(r'Total[:\s]+(\d+)\s+Unidad\s+\$?([\d,]+\.?\d*)', texto)
            if total_match:
                total = float(total_match.group(2).replace(',', ''))
            else:
                total = 0.0
        else:
            total = float(total_match.group(1).replace(',', ''))
        
        # Extraer descripción del producto
        product_match = re.search(r'(\d+)\s*-\s*(.+?)\s*Impuestos:', texto, re.DOTALL)
        if product_match:
            codigo = product_match.group(1)
            descripcion = product_match.group(2).strip()
            producto = f"{codigo} - {descripcion}"
        else:
            producto = "Producto procesado desde PDF"
        
        # Extraer precio unitario
        price_match = re.search(r'Precio unit\.\s*\$?([\d,]+\.?\d*)', texto)
        precio_unitario = float(price_match.group(1).replace(',', '')) if price_match else total
        
        # Extraer cantidad
        qty_match = re.search(r'(\d+)\s+Unidad', texto)
        cantidad = float(qty_match.group(1)) if qty_match else 1.0
        
        datos = {
            'fecha': fecha,
            'cliente': 'Cliente desde PDF',
            'items': [{
                'descripcion': producto,
                'cantidad': cantidad,
                'precio': precio_unitario
            }],
            'total': total
        }
        
        print("\n📊 Datos extraídos:")
        print(f"   📅 Fecha: {datos['fecha']}")
        print(f"   👤 Cliente: {datos['cliente']}")
        print(f"   💰 Total: ${datos['total']:,.2f}")
        print(f"   📦 Producto: {datos['items'][0]['descripcion']}")
        print(f"   📊 Cantidad: {datos['items'][0]['cantidad']}")
        print(f"   💵 Precio Unitario: ${datos['items'][0]['precio']:,.2f}")
        
        return datos
        
    except Exception as e:
        print(f"❌ Error procesando PDF: {e}")
        return None

def get_existing_item(headers):
    """Obtener un item existente de Alegra"""
    try:
        response = requests.get('https://api.alegra.com/api/v1/items', headers=headers, timeout=10)
        if response.status_code == 200:
            items = response.json()
            if items:
                print(f"📦 Usando item existente: {items[0].get('name')} (ID: {items[0].get('id')})")
                return items[0].get('id')
        return None
    except Exception as e:
        print(f"Error obteniendo items: {e}")
        return None

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
    """Crear factura en Alegra usando item existente"""
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
    client_id = get_client_id_by_name("Consumidor Final", headers)
    
    if not client_id:
        print("❌ No se pudo encontrar cliente 'Consumidor Final'")
        return None
    
    print(f"✅ Usando cliente ID: {client_id}")
    
    # Obtener item existente
    item_id = get_existing_item(headers)
    
    if not item_id:
        print("❌ No se encontraron items existentes en Alegra")
        return None
    
    # Calcular fecha de vencimiento
    fecha_vencimiento = datetime.strptime(datos_factura['fecha'], '%Y-%m-%d') + timedelta(days=30)
    
    # Crear payload para Alegra
    payload = {
        "date": datos_factura['fecha'],
        "dueDate": fecha_vencimiento.strftime('%Y-%m-%d'),
        "client": {"id": client_id},
        "items": [{
            "id": item_id,
            "quantity": datos_factura['items'][0]['cantidad'],
            "price": datos_factura['items'][0]['precio']
        }],
        "observations": f"Factura procesada desde PDF: {datos_factura['items'][0]['descripcion'][:100]}... - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
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
            print(f"📝 Observaciones: {factura_creada.get('observations')}")
            
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
    print("🚀 InvoiceBot - Procesamiento Final de testfactura.pdf")
    print("=" * 70)
    
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
        print("✅ Factura creada en Alegra usando item existente")
        print("✅ Sistema funcionando perfectamente")
        print(f"\n📋 Resumen de la factura:")
        print(f"   - Producto: {datos['items'][0]['descripcion']}")
        print(f"   - Cantidad: {datos['items'][0]['cantidad']}")
        print(f"   - Precio Unitario: ${datos['items'][0]['precio']:,.2f}")
        print(f"   - Total: ${datos['total']:,.2f}")
        print(f"   - Fecha: {datos['fecha']}")
        print(f"\n🔗 Puedes ver la factura en tu panel de Alegra")
    else:
        print("\n⚠️ Error en el proceso")
        print("❌ Revisa los logs para más detalles")

if __name__ == "__main__":
    main()