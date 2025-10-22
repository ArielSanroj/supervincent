#!/usr/bin/env python3
"""
Sistema final de procesamiento de facturas - Compra y Venta
"""

import requests
import base64
import pdfplumber
import re
import json
import sys
from datetime import datetime, timedelta
from dotenv import load_dotenv
import os

# Cargar variables de entorno
load_dotenv()

def extract_data_from_pdf(pdf_path, invoice_type):
    """Extraer datos del PDF según el tipo de factura"""
    print(f"📄 Procesando PDF: {pdf_path}")
    print(f"📋 Tipo: {'Factura de COMPRA' if invoice_type == 'compra' else 'Factura de VENTA'}")
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
        
        # Extraer vendedor/proveedor
        vendedor_match = re.search(r'Factura electrónica de venta #\d+\n([^\n]+)', texto)
        vendedor = vendedor_match.group(1).strip() if vendedor_match else "Proveedor Desconocido"
        
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
            'tipo': invoice_type,
            'fecha': fecha,
            'proveedor': vendedor,
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
        
        print(f"\n📊 Datos extraídos del PDF:")
        print(f"   📅 Fecha: {datos['fecha']}")
        print(f"   🏪 {'Proveedor' if invoice_type == 'compra' else 'Cliente'}: {datos['proveedor']}")
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
        
        # También crear un registro JSON
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
        
        return True
        
    except Exception as e:
        print(f"❌ Error registrando factura de compra: {e}")
        return False

def create_sale_invoice(datos_factura):
    """Crear factura de venta en Alegra"""
    print(f"\n📤 Creando factura de VENTA en Alegra...")
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
        "observations": f"Factura de VENTA procesada desde PDF - Cliente: {datos_factura['proveedor']} - Producto: {datos_factura['items'][0]['descripcion']} - Total: ${datos_factura['total']:,.2f} - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    }
    
    try:
        response = requests.post('https://api.alegra.com/api/v1/invoices', 
                               json=payload, 
                               headers=headers, 
                               timeout=30)
        
        print(f"📡 Status Code: {response.status_code}")
        
        if response.status_code == 201:
            factura_creada = response.json()
            print("✅ ¡Factura de VENTA creada exitosamente!")
            print(f"🆔 ID: {factura_creada.get('id')}")
            print(f"📄 Número: {factura_creada.get('number')}")
            print(f"💰 Total: ${factura_creada.get('total')}")
            print(f"👤 Cliente: {factura_creada.get('client', {}).get('name')}")
            print(f"📅 Fecha: {factura_creada.get('date')}")
            print(f"📅 Vencimiento: {factura_creada.get('dueDate')}")
            
            return factura_creada
        else:
            print(f"❌ Error creando factura de venta: {response.status_code}")
            print(f"📝 Respuesta: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Error en API Alegra: {e}")
        return None

def create_custom_item(item_data, headers):
    """Crear item personalizado en Alegra"""
    print(f"\n📦 Creando item personalizado: {item_data['descripcion']}")
    
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
        
        if response.status_code == 201:
            created_item = response.json()
            print(f"   ✅ Item creado exitosamente! ID: {created_item.get('id')}")
            return created_item.get('id')
        else:
            print(f"   ❌ Error creando item: {response.status_code}")
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

def main():
    """Función principal"""
    print("🚀 InvoiceBot - Sistema Final de Facturas")
    print("=" * 60)
    
    # Verificar argumentos de línea de comandos
    if len(sys.argv) < 2:
        print("❌ Uso: python invoice_processor_final.py <tipo> [archivo]")
        print("   Tipos: compra, venta")
        print("   Archivo: ruta al PDF (opcional, usa testfactura.pdf por defecto)")
        print("\nEjemplos:")
        print("   python invoice_processor_final.py compra")
        print("   python invoice_processor_final.py venta")
        print("   python invoice_processor_final.py compra /ruta/a/factura.pdf")
        return
    
    invoice_type = sys.argv[1].lower()
    
    if invoice_type not in ['compra', 'venta']:
        print("❌ Tipo inválido. Usa 'compra' o 'venta'")
        return
    
    # Usar archivo por defecto o el especificado
    if len(sys.argv) > 2:
        pdf_path = sys.argv[2]
    else:
        pdf_path = "/Users/arielsanroj/Downloads/testfactura.pdf"
    
    # Verificar que el archivo existe
    if not os.path.exists(pdf_path):
        print(f"❌ Archivo no encontrado: {pdf_path}")
        return
    
    # Paso 1: Extraer datos del PDF
    datos = extract_data_from_pdf(pdf_path, invoice_type)
    
    if not datos:
        print("❌ No se pudieron extraer datos del PDF")
        return
    
    # Paso 2: Procesar según el tipo
    if invoice_type == "compra":
        resultado = register_purchase_invoice(datos)
        if resultado:
            print("\n🎉 ¡Factura de COMPRA registrada exitosamente!")
            print("✅ Se guardó en el sistema local")
            print("✅ Lista para procesamiento contable")
            print("✅ No se creó en Alegra (es factura de compra)")
        else:
            print("\n⚠️ Error registrando factura de compra")
    else:  # venta
        resultado = create_sale_invoice(datos)
        if resultado:
            print("\n🎉 ¡Factura de VENTA creada exitosamente!")
            print("✅ Se creó en Alegra")
            print("✅ Lista para enviar al cliente")
        else:
            print("\n⚠️ Error creando factura de venta")

if __name__ == "__main__":
    main()