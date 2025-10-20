#!/usr/bin/env python3
"""
Script de prueba para la API de Alegra
"""

import requests
import base64
import json
from dotenv import load_dotenv
import os

# Cargar variables de entorno
load_dotenv()

def test_alegra_connection():
    """Probar conexión con la API de Alegra"""
    print("🔍 Probando conexión con Alegra API...")
    print("=" * 50)
    
    # Obtener credenciales
    alegra_user = os.getenv('ALEGRA_USER')
    alegra_token = os.getenv('ALEGRA_TOKEN')
    base_url = os.getenv('ALEGRA_BASE_URL', 'https://api.alegra.com/api/v1')
    
    if not alegra_user or not alegra_token:
        print("❌ Error: ALEGRA_USER y ALEGRA_TOKEN deben estar configurados en .env")
        return False
    
    print(f"👤 Usuario: {alegra_user}")
    print(f"🔑 Token: {alegra_token[:10]}...")
    print(f"🌐 URL Base: {base_url}")
    print()
    
    # Configurar autenticación
    auth = base64.b64encode(f"{alegra_user}:{alegra_token}".encode()).decode()
    headers = {
        'Authorization': f'Basic {auth}',
        'Content-Type': 'application/json'
    }
    
    # Prueba 1: Obtener información de la cuenta
    print("📊 Prueba 1: Obteniendo información de la cuenta...")
    try:
        response = requests.get(f'{base_url}/company', headers=headers, timeout=10)
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code == 200:
            company_info = response.json()
            print("   ✅ Conexión exitosa!")
            print(f"   🏢 Empresa: {company_info.get('name', 'N/A')}")
            print(f"   📧 Email: {company_info.get('email', 'N/A')}")
            print(f"   🌍 País: {company_info.get('country', 'N/A')}")
        else:
            print(f"   ❌ Error: {response.status_code}")
            print(f"   📝 Respuesta: {response.text}")
            return False
            
    except Exception as e:
        print(f"   ❌ Error de conexión: {e}")
        return False
    
    print()
    
    # Prueba 2: Obtener clientes
    print("👥 Prueba 2: Obteniendo lista de clientes...")
    try:
        response = requests.get(f'{base_url}/contacts', headers=headers, timeout=10)
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code == 200:
            clients = response.json()
            print(f"   ✅ Clientes obtenidos: {len(clients)}")
            if clients:
                print(f"   📋 Primer cliente: {clients[0].get('name', 'N/A')}")
        else:
            print(f"   ❌ Error: {response.status_code}")
            print(f"   📝 Respuesta: {response.text}")
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print()
    
    # Prueba 3: Obtener facturas existentes
    print("📄 Prueba 3: Obteniendo facturas existentes...")
    try:
        response = requests.get(f'{base_url}/invoices', headers=headers, timeout=10)
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code == 200:
            invoices = response.json()
            print(f"   ✅ Facturas obtenidas: {len(invoices)}")
            if invoices:
                latest_invoice = invoices[0]
                print(f"   📋 Última factura: #{latest_invoice.get('number', 'N/A')}")
                print(f"   💰 Total: ${latest_invoice.get('total', 0)}")
        else:
            print(f"   ❌ Error: {response.status_code}")
            print(f"   📝 Respuesta: {response.text}")
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print()
    
    # Prueba 4: Crear una factura de prueba
    print("🧪 Prueba 4: Creando factura de prueba...")
    try:
        test_invoice = {
            "date": "2024-01-15",
            "dueDate": "2024-02-14",
            "client": {"name": "Cliente Prueba API"},
            "items": [
                {
                    "name": "Servicio de prueba",
                    "quantity": 1,
                    "price": 100.00
                }
            ],
            "observations": "Factura de prueba creada por InvoiceBot"
        }
        
        response = requests.post(f'{base_url}/invoices', 
                               json=test_invoice, 
                               headers=headers, 
                               timeout=10)
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code == 201:
            created_invoice = response.json()
            print("   ✅ Factura de prueba creada exitosamente!")
            print(f"   🆔 ID: {created_invoice.get('id')}")
            print(f"   📄 Número: {created_invoice.get('number')}")
            print(f"   💰 Total: ${created_invoice.get('total')}")
            
            # Opcional: Eliminar la factura de prueba
            invoice_id = created_invoice.get('id')
            if invoice_id:
                delete_response = requests.delete(f'{base_url}/invoices/{invoice_id}', 
                                                headers=headers, 
                                                timeout=10)
                if delete_response.status_code == 200:
                    print("   🗑️ Factura de prueba eliminada")
                else:
                    print(f"   ⚠️ No se pudo eliminar la factura de prueba: {delete_response.status_code}")
        else:
            print(f"   ❌ Error creando factura: {response.status_code}")
            print(f"   📝 Respuesta: {response.text}")
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print()
    print("🎉 Pruebas completadas!")
    return True

def test_invoice_processor():
    """Probar el procesador de facturas"""
    print("\n🤖 Probando InvoiceProcessor...")
    print("=" * 50)
    
    try:
        from invoice_processor import InvoiceProcessor
        
        # Crear instancia del procesador
        processor = InvoiceProcessor()
        print("✅ InvoiceProcessor inicializado correctamente")
        
        # Probar con datos de ejemplo
        test_data = {
            'fecha': '2024-01-15',
            'cliente': 'Cliente Prueba InvoiceBot',
            'items': [
                {
                    'descripcion': 'Servicio de prueba InvoiceBot',
                    'cantidad': 1.0,
                    'precio': 50.00
                }
            ],
            'total': 50.00
        }
        
        print("📝 Creando factura de prueba con InvoiceProcessor...")
        resultado = processor.crear_factura_alegra(test_data)
        
        if resultado:
            print("✅ Factura creada exitosamente con InvoiceProcessor!")
            print(f"🆔 ID: {resultado.get('id')}")
            print(f"📄 Número: {resultado.get('number')}")
            print(f"💰 Total: ${resultado.get('total')}")
            
            # Eliminar factura de prueba
            invoice_id = resultado.get('id')
            if invoice_id:
                import requests
                import base64
                from dotenv import load_dotenv
                import os
                
                load_dotenv()
                auth = base64.b64encode(f"{os.getenv('ALEGRA_USER')}:{os.getenv('ALEGRA_TOKEN')}".encode()).decode()
                headers = {'Authorization': f'Basic {auth}'}
                
                delete_response = requests.delete(f'https://api.alegra.com/api/v1/invoices/{invoice_id}', 
                                                headers=headers, 
                                                timeout=10)
                if delete_response.status_code == 200:
                    print("🗑️ Factura de prueba eliminada")
        else:
            print("❌ Error creando factura con InvoiceProcessor")
            
    except Exception as e:
        print(f"❌ Error probando InvoiceProcessor: {e}")

def main():
    """Función principal"""
    print("🚀 InvoiceBot - Prueba de API de Alegra")
    print("=" * 60)
    
    # Probar conexión directa
    if test_alegra_connection():
        # Probar procesador de facturas
        test_invoice_processor()
    
    print("\n✨ Pruebas completadas!")

if __name__ == "__main__":
    main()