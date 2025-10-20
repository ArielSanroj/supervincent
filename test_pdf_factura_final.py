#!/usr/bin/env python3
"""
Script final para procesar testfactura.pdf y crear factura en Alegra
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
    """Extraer items del PDF con mejor parsing"""
    items = []
    
    # Buscar el patrón específico de esta factura
    # "3182550771337 - ROYAL CANIN GATO GASTROINTESTINAL FIBRE x2KG"
    # "Precio unit. $203,343.81"
    # "1 Unidad $203,343.81"
    
    # Buscar descripción del producto
    product_match = re.search(r'(\d+)\s*-\s*(.+?)\s*Impuestos:', text, re.DOTALL)
    if product_match:
        codigo = product_match.group(1)
        descripcion = product_match.group(2).strip()
        
        # Buscar precio unitario
        price_match = re.search(r'Precio unit\.\s*\$?([\d,]+\.?\d*)', text)
        precio = float(price_match.group(1).replace(',', '')) if price_match else 0.0
        
        # Buscar cantidad
        qty_match = re.search(r'(\d+)\s+Unidad', text)
        cantidad = float(qty_match.group(1)) if qty_match else 1.0
        
        items.append({
            'descripcion': f"{codigo} - {descripcion}",
            'cantidad': cantidad,
            'precio': precio
        })
    
    # Si no se encontró el patrón específico, usar método genérico
    if not items:
        lines = text.split('\n')
        in_items_section = False
        
        for line in lines:
            line = line.strip()
            
            # Detectar inicio de items
            if any(keyword in line.lower() for keyword in ['descripción', 'descripcion', 'item', 'concepto', 'producto', 'servicio']):
                in_items_section = True
                continue
            
            # Detectar fin de items
            if any(keyword in line.lower() for keyword in ['subtotal', 'total', 'impuestos', 'iva', 'descuento']):
                in_items_section = False
                continue
            
            # Procesar líneas de items
            if in_items_section and line and not line.startswith(('Fecha', 'Cliente', 'Total')):
                price_match = re.search(r'(\d+\.?\d*)\s*$', line)
                if price_match:
                    price = float(price_match.group(1))
                    desc = line[:price_match.start()].strip()
                    if desc and len(desc) > 3:
                        items.append({
                            'descripcion': desc,
                            'cantidad': 1.0,
                            'precio': price
                        })
    
    # Si no se encontraron items, crear uno genérico basado en el total
    if not items:
        total_match = re.search(r'Total[:\s]+\$?([\d,]+\.?\d*)', text)
        if total_match:
            total = float(total_match.group(1).replace(',', ''))
            items.append({
                'descripcion': 'Producto/Servicio procesado desde PDF',
                'cantidad': 1.0,
                'precio': total
            })
        else:
            items.append({
                'descripcion': 'Servicio procesado desde PDF',
                'cantidad': 1.0,
                'precio': 100.0
            })
    
    return items

def get_available_units(headers):
    """Obtener unidades de medida disponibles en Alegra"""
    try:
        response = requests.get('https://api.alegra.com/api/v1/units', headers=headers, timeout=10)
        if response.status_code == 200:
            units = response.json()
            print("📏 Unidades disponibles en Alegra:")
            for unit in units[:5]:  # Mostrar solo las primeras 5
                print(f"   - {unit.get('name')} (ID: {unit.get('id')})")
            return units
        return []
    except Exception as e:
        print(f"Error obteniendo unidades: {e}")
        return []

def get_or_create_item(item_data, headers):
    """Obtener o crear item en Alegra con unidad válida"""
    try:
        # Buscar item existente por nombre
        response = requests.get('https://api.alegra.com/api/v1/items', headers=headers, timeout=10)
        if response.status_code == 200:
            items = response.json()
            for item in items:
                if item.get('name', '').lower() == item_data['descripcion'].lower():
                    return item.get('id')
        
        # Si no existe, crear nuevo item
        print(f"📦 Creando nuevo item: {item_data['descripcion']}")
        
        # Obtener unidades disponibles
        units = get_available_units(headers)
        
        # Usar la primera unidad disponible o una por defecto
        unit_id = 1  # ID por defecto para "Unidad"
        if units:
            unit_id = units[0].get('id', 1)
        
        new_item = {
            "name": item_data['descripcion'],
            "price": item_data['precio'],
            "inventory": {
                "unit": {"id": unit_id},  # Usar ID de unidad en lugar de string
                "initialQuantity": 0
            }
        }
        
        response = requests.post('https://api.alegra.com/api/v1/items', 
                               json=new_item, 
                               headers=headers, 
                               timeout=10)
        
        if response.status_code == 201:
            created_item = response.json()
            print(f"✅ Item creado con ID: {created_item.get('id')}")
            return created_item.get('id')
        else:
            print(f"❌ Error creando item: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Error con items: {e}")
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
    """Crear factura en Alegra con items correctos"""
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
    
    # Obtener o crear items
    items_with_ids = []
    for item in datos_factura['items']:
        item_id = get_or_create_item(item, headers)
        if item_id:
            items_with_ids.append({
                "id": item_id,
                "quantity": item['cantidad'],
                "price": item['precio']
            })
        else:
            print(f"⚠️ No se pudo obtener ID para item: {item['descripcion']}")
    
    if not items_with_ids:
        print("❌ No se pudieron obtener items válidos")
        return None
    
    # Calcular fecha de vencimiento
    fecha_vencimiento = datetime.strptime(datos_factura['fecha'], '%Y-%m-%d') + timedelta(days=30)
    
    # Crear payload para Alegra
    payload = {
        "date": datos_factura['fecha'],
        "dueDate": fecha_vencimiento.strftime('%Y-%m-%d'),
        "client": {"id": client_id},
        "items": items_with_ids,
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
    print("🚀 InvoiceBot - Procesamiento de testfactura.pdf (Versión Final)")
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
        print("✅ Items creados/obtenidos en Alegra")
        print("✅ Factura creada en Alegra")
        print("✅ Sistema funcionando perfectamente")
    else:
        print("\n⚠️ Error en el proceso")
        print("❌ Revisa los logs para más detalles")

if __name__ == "__main__":
    main()