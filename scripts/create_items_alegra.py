#!/usr/bin/env python3
"""
Script para crear items necesarios en Alegra
"""

import requests
import base64
from dotenv import load_dotenv
import os

# Cargar variables de entorno
load_dotenv()

def create_items_in_alegra():
    """Crear items básicos en Alegra"""
    print("🏭 Creando items en Alegra...")
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
    
    # Items básicos para crear
    items_to_create = [
        {
            "name": "Servicio General",
            "price": 100.00,
            "description": "Servicio general para facturas procesadas"
        },
        {
            "name": "Producto Varios",
            "price": 50.00,
            "description": "Producto varios para facturas procesadas"
        },
        {
            "name": "Consultoría",
            "price": 200.00,
            "description": "Servicio de consultoría"
        },
        {
            "name": "Venta de Productos",
            "price": 150.00,
            "description": "Venta de productos varios"
        },
        {
            "name": "Servicio Técnico",
            "price": 300.00,
            "description": "Servicio técnico especializado"
        }
    ]
    
    created_items = []
    
    for item_data in items_to_create:
        print(f"\n📦 Creando item: {item_data['name']}")
        
        # Payload para crear item sin inventario
        payload = {
            "name": item_data['name'],
            "price": item_data['price'],
            "description": item_data['description']
            # No incluir inventory para evitar problemas con unidades
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
                created_items.append(created_item)
            else:
                print(f"   ❌ Error creando item: {response.status_code}")
                print(f"   📝 Respuesta: {response.text}")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    return created_items

def list_existing_items():
    """Listar items existentes en Alegra"""
    print("\n📋 Items existentes en Alegra:")
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
    
    try:
        response = requests.get('https://api.alegra.com/api/v1/items', headers=headers, timeout=10)
        
        if response.status_code == 200:
            items = response.json()
            print(f"Total de items: {len(items)}")
            
            for i, item in enumerate(items, 1):
                print(f"{i}. {item.get('name')} - ID: {item.get('id')} - Precio: ${item.get('price')}")
        else:
            print(f"❌ Error obteniendo items: {response.status_code}")
            print(f"📝 Respuesta: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

def test_create_invoice_with_items():
    """Probar creación de factura con items existentes"""
    print("\n🧪 Probando creación de factura con items...")
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
    
    # Obtener items existentes
    try:
        response = requests.get('https://api.alegra.com/api/v1/items', headers=headers, timeout=10)
        
        if response.status_code == 200:
            items = response.json()
            
            if items:
                # Usar el primer item disponible
                item = items[0]
                item_id = item.get('id')
                
                print(f"📦 Usando item: {item.get('name')} (ID: {item_id})")
                
                # Obtener cliente
                client_response = requests.get('https://api.alegra.com/api/v1/contacts', headers=headers, timeout=10)
                if client_response.status_code == 200:
                    clients = client_response.json()
                    if clients:
                        client_id = clients[0].get('id')
                        client_name = clients[0].get('name')
                        
                        print(f"👤 Usando cliente: {client_name} (ID: {client_id})")
                        
                        # Crear factura de prueba
                        from datetime import datetime, timedelta
                        
                        payload = {
                            "date": "2024-01-15",
                            "dueDate": "2024-02-14",
                            "client": {"id": client_id},
                            "items": [{
                                "id": item_id,
                                "quantity": 1,
                                "price": 100.00
                            }],
                            "observations": "Factura de prueba creada por InvoiceBot"
                        }
                        
                        print("📄 Creando factura de prueba...")
                        invoice_response = requests.post('https://api.alegra.com/api/v1/invoices', 
                                                       json=payload, 
                                                       headers=headers, 
                                                       timeout=10)
                        
                        print(f"   Status Code: {invoice_response.status_code}")
                        
                        if invoice_response.status_code == 201:
                            invoice = invoice_response.json()
                            print("   ✅ ¡Factura de prueba creada exitosamente!")
                            print(f"   🆔 ID: {invoice.get('id')}")
                            print(f"   📄 Número: {invoice.get('number')}")
                            print(f"   💰 Total: ${invoice.get('total')}")
                            
                            # Eliminar factura de prueba
                            invoice_id = invoice.get('id')
                            if invoice_id:
                                print(f"\n🗑️ Eliminando factura de prueba (ID: {invoice_id})...")
                                delete_response = requests.delete(f'https://api.alegra.com/api/v1/invoices/{invoice_id}', 
                                                                headers=headers, 
                                                                timeout=10)
                                if delete_response.status_code == 200:
                                    print("   ✅ Factura de prueba eliminada")
                                else:
                                    print(f"   ⚠️ No se pudo eliminar: {delete_response.status_code}")
                            
                            return True
                        else:
                            print(f"   ❌ Error creando factura: {invoice_response.status_code}")
                            print(f"   📝 Respuesta: {invoice_response.text}")
                    else:
                        print("❌ No hay clientes disponibles")
                else:
                    print(f"❌ Error obteniendo clientes: {client_response.status_code}")
            else:
                print("❌ No hay items disponibles")
        else:
            print(f"❌ Error obteniendo items: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    
    return False

def main():
    """Función principal"""
    print("🚀 InvoiceBot - Configuración de Items en Alegra")
    print("=" * 60)
    
    # Paso 1: Listar items existentes
    list_existing_items()
    
    # Paso 2: Crear items necesarios
    created_items = create_items_in_alegra()
    
    if created_items:
        print(f"\n✅ Se crearon {len(created_items)} items exitosamente")
        
        # Paso 3: Listar items actualizados
        list_existing_items()
        
        # Paso 4: Probar creación de factura
        if test_create_invoice_with_items():
            print("\n🎉 ¡Configuración completada exitosamente!")
            print("✅ Items creados en Alegra")
            print("✅ Sistema listo para procesar facturas")
        else:
            print("\n⚠️ Error en la prueba de factura")
    else:
        print("\n❌ No se pudieron crear items")
        print("⚠️ Revisa los logs para más detalles")

if __name__ == "__main__":
    main()