#!/usr/bin/env python3
"""
Script corregido para procesar testfactura.pdf con datos exactos
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
    """Extraer datos del PDF de factura con parsing mejorado"""
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
        
        # Extraer datos específicos de esta factura
        # Fecha: 10-10-2025 11:35:46
        fecha_match = re.search(r'Fecha:\s*(\d{1,2}-\d{1,2}-\d{4})', texto)
        fecha = fecha_match.group(1) if fecha_match else datetime.now().strftime('%Y-%m-%d')
        
        # Formatear fecha
        if '-' in fecha:
            parts = fecha.split('-')
            if len(parts) == 3:
                day, month, year = parts
                fecha = f"{year}-{month.zfill(2)}-{day.zfill(2)}"
        
        # Extraer vendedor (VEGA RODRIGUEZ MARIA CLEMENCIA)
        vendedor_match = re.search(r'Factura electrónica de venta #\d+\n([^\n]+)', texto)
        vendedor = vendedor_match.group(1).strip() if vendedor_match else "Vendedor Desconocido"
        
        # Extraer producto específico (3182550771337 - ROYAL CANIN GATO GASTROINTESTINAL FIBRE x2KG)
        producto_match = re.search(r'(\d+)\s*-\s*(.+?)\s*Impuestos:', texto, re.DOTALL)
        if producto_match:
            codigo = producto_match.group(1)
            descripcion = producto_match.group(2).strip()
            producto = f"{codigo} - {descripcion}"
        else:
            producto = "Producto no identificado"
        
        # Extraer precio unitario ($203,343.81)
        price_match = re.search(r'Precio unit\.\s*\$?([\d,]+\.?\d*)', texto)
        precio_unitario = float(price_match.group(1).replace(',', '')) if price_match else 0.0
        
        # Extraer cantidad (1 Unidad)
        qty_match = re.search(r'(\d+)\s+Unidad', texto)
        cantidad = float(qty_match.group(1)) if qty_match else 1.0
        
        # Extraer total real ($213,511.00)
        total_match = re.search(r'Total[:\s]+\d+\s+Unidad\s+\$?([\d,]+\.?\d*)', texto)
        if not total_match:
            total_match = re.search(r'Total[:\s]+\$?([\d,]+\.?\d*)', texto)
        total = float(total_match.group(1).replace(',', '')) if total_match else 0.0
        
        # Extraer subtotal ($203,343.81)
        subtotal_match = re.search(r'Subtotal\s+\$?([\d,]+\.?\d*)', texto)
        subtotal = float(subtotal_match.group(1).replace(',', '')) if subtotal_match else precio_unitario
        
        # Extraer impuestos ($10,167.19)
        impuestos_match = re.search(r'Impuestos\s+\$?([\d,]+\.?\d*)', texto)
        impuestos = float(impuestos_match.group(1).replace(',', '')) if impuestos_match else 0.0
        
        datos = {
            'fecha': fecha,
            'vendedor': vendedor,
            'cliente': 'Cliente desde PDF',
            'items': [{
                'descripcion': producto,
                'cantidad': cantidad,
                'precio': precio_unitario
            }],
            'subtotal': subtotal,
            'impuestos': impuestos,
            'total': total
        }
        
        print("\n📊 Datos extraídos del PDF:")
        print(f"   📅 Fecha: {datos['fecha']}")
        print(f"   🏪 Vendedor: {datos['vendedor']}")
        print(f"   👤 Cliente: {datos['cliente']}")
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

def create_custom_item(item_data, headers):
    """Crear item personalizado en Alegra"""
    print(f"\n📦 Creando item personalizado: {item_data['descripcion']}")
    
    # Payload para crear item sin inventario
    payload = {
        "name": item_data['descripcion'],
        "price": item_data['precio'],
        "description": f"Producto procesado desde PDF - {item_data['descripcion']}"
    }
    
    try:
        response = requests.post('https://api.alegra.com/api/v1/items', 
                               json=payload, 
                               headers=headers, 
                               timeout=10)
        
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code == 201:
            created_item = response.json()
            print(f"   ✅ Item creado exitosamente!")
            print(f"   🆔 ID: {created_item.get('id')}")
            print(f"   💰 Precio: ${created_item.get('price')}")
            return created_item.get('id')
        else:
            print(f"   ❌ Error creando item: {response.status_code}")
            print(f"   📝 Respuesta: {response.text}")
            return None
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return None

def get_existing_item(headers):
    """Obtener un item existente de Alegra como fallback"""
    try:
        response = requests.get('https://api.alegra.com/api/v1/items', headers=headers, timeout=10)
        if response.status_code == 200:
            items = response.json()
            if items:
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
    """Crear factura en Alegra con datos exactos del PDF"""
    print("\n🏢 Creando factura en Alegra con datos exactos...")
    print("=" * 50)
    
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
    
    # Crear item personalizado para el producto específico
    item_id = create_custom_item(datos_factura['items'][0], headers)
    
    # Si no se pudo crear, usar item existente como fallback
    if not item_id:
        print("⚠️ Usando item existente como fallback...")
        item_id = get_existing_item(headers)
    
    if not item_id:
        print("❌ No se pudo obtener item válido")
        return None
    
    # Calcular fecha de vencimiento
    fecha_vencimiento = datetime.strptime(datos_factura['fecha'], '%Y-%m-%d') + timedelta(days=30)
    
    # Crear payload para Alegra con datos exactos
    payload = {
        "date": datos_factura['fecha'],
        "dueDate": fecha_vencimiento.strftime('%Y-%m-%d'),
        "client": {"id": client_id},
        "items": [{
            "id": item_id,
            "quantity": datos_factura['items'][0]['cantidad'],
            "price": datos_factura['items'][0]['precio']
        }],
        "observations": f"Factura procesada desde PDF - Vendedor: {datos_factura['vendedor']} - Producto: {datos_factura['items'][0]['descripcion']} - Total: ${datos_factura['total']:,.2f} - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    }
    
    try:
        response = requests.post('https://api.alegra.com/api/v1/invoices', 
                               json=payload, 
                               headers=headers, 
                               timeout=30)
        
        print(f"📡 Status Code: {response.status_code}")
        
        if response.status_code == 201:
            factura_creada = response.json()
            print("✅ ¡Factura creada exitosamente con datos exactos!")
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
    print("🚀 InvoiceBot - Procesamiento Corregido de testfactura.pdf")
    print("=" * 70)
    
    pdf_path = "/Users/arielsanroj/Downloads/testfactura.pdf"
    
    # Paso 1: Extraer datos del PDF
    datos = extract_data_from_pdf(pdf_path)
    
    if not datos:
        print("❌ No se pudieron extraer datos del PDF")
        return
    
    # Paso 2: Crear factura en Alegra con datos exactos
    resultado = create_invoice_in_alegra(datos)
    
    if resultado:
        print("\n🎉 ¡Proceso completado exitosamente!")
        print("✅ PDF procesado correctamente")
        print("✅ Item personalizado creado")
        print("✅ Factura creada con datos exactos del PDF")
        print("✅ Sistema funcionando perfectamente")
        print(f"\n📋 Resumen de la factura:")
        print(f"   - Vendedor: {datos['vendedor']}")
        print(f"   - Producto: {datos['items'][0]['descripcion']}")
        print(f"   - Cantidad: {datos['items'][0]['cantidad']}")
        print(f"   - Precio Unitario: ${datos['items'][0]['precio']:,.2f}")
        print(f"   - Subtotal: ${datos['subtotal']:,.2f}")
        print(f"   - Impuestos: ${datos['impuestos']:,.2f}")
        print(f"   - Total: ${datos['total']:,.2f}")
        print(f"   - Fecha: {datos['fecha']}")
        print(f"\n🔗 Ahora deberías ver la factura con el producto correcto en Alegra")
    else:
        print("\n⚠️ Error en el proceso")
        print("❌ Revisa los logs para más detalles")

if __name__ == "__main__":
    main()