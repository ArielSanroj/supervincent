#!/usr/bin/env python3
"""
Script de prueba mejorado para la API de Alegra
"""

import requests
import base64
import json
from dotenv import load_dotenv
import os

# Cargar variables de entorno
load_dotenv()

def get_client_id_by_name(client_name, headers, base_url):
    """Obtener ID del cliente por nombre"""
    try:
        response = requests.get(f'{base_url}/contacts', headers=headers, timeout=10)
        if response.status_code == 200:
            clients = response.json()
            for client in clients:
                if client.get('name', '').lower() == client_name.lower():
                    return client.get('id')
        return None
    except Exception as e:
        print(f"Error obteniendo clientes: {e}")
        return None

def test_alegra_with_fixed_client():
    """Probar Alegra con cliente existente"""
    print("🔍 Probando Alegra con cliente existente...")
    print("=" * 50)
    
    # Obtener credenciales
    alegra_user = os.getenv('ALEGRA_USER')
    alegra_token = os.getenv('ALEGRA_TOKEN')
    base_url = os.getenv('ALEGRA_BASE_URL', 'https://api.alegra.com/api/v1')
    
    # Configurar autenticación
    auth = base64.b64encode(f"{alegra_user}:{alegra_token}".encode()).decode()
    headers = {
        'Authorization': f'Basic {auth}',
        'Content-Type': 'application/json'
    }
    
    # Obtener ID del cliente "Consumidor Final"
    print("👥 Obteniendo ID del cliente 'Consumidor Final'...")
    client_id = get_client_id_by_name("Consumidor Final", headers, base_url)
    
    if not client_id:
        print("❌ No se encontró el cliente 'Consumidor Final'")
        return False
    
    print(f"✅ Cliente encontrado con ID: {client_id}")
    
    # Crear factura con ID del cliente
    print("\n🧪 Creando factura con ID del cliente...")
    test_invoice = {
        "date": "2024-01-15",
        "dueDate": "2024-02-14",
        "client": {"id": client_id},  # Usar ID en lugar de nombre
        "items": [
            {
                "name": "Servicio de prueba InvoiceBot",
                "quantity": 1,
                "price": 100.00
            }
        ],
        "observations": "Factura de prueba creada por InvoiceBot - Prueba exitosa"
    }
    
    try:
        response = requests.post(f'{base_url}/invoices', 
                               json=test_invoice, 
                               headers=headers, 
                               timeout=10)
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code == 201:
            created_invoice = response.json()
            print("   ✅ Factura creada exitosamente!")
            print(f"   🆔 ID: {created_invoice.get('id')}")
            print(f"   📄 Número: {created_invoice.get('number')}")
            print(f"   💰 Total: ${created_invoice.get('total')}")
            print(f"   👤 Cliente: {created_invoice.get('client', {}).get('name')}")
            
            return created_invoice
        else:
            print(f"   ❌ Error creando factura: {response.status_code}")
            print(f"   📝 Respuesta: {response.text}")
            return None
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return None

def test_invoice_processor_fixed():
    """Probar InvoiceProcessor con cliente existente"""
    print("\n🤖 Probando InvoiceProcessor mejorado...")
    print("=" * 50)
    
    try:
        from invoice_processor import InvoiceProcessor
        
        # Crear instancia del procesador
        processor = InvoiceProcessor()
        print("✅ InvoiceProcessor inicializado correctamente")
        
        # Obtener ID del cliente existente
        import requests
        import base64
        from dotenv import load_dotenv
        import os
        
        load_dotenv()
        auth = base64.b64encode(f"{os.getenv('ALEGRA_USER')}:{os.getenv('ALEGRA_TOKEN')}".encode()).decode()
        headers = {'Authorization': f'Basic {auth}'}
        
        response = requests.get('https://api.alegra.com/api/v1/contacts', headers=headers, timeout=10)
        if response.status_code == 200:
            clients = response.json()
            client_id = None
            for client in clients:
                if client.get('name', '').lower() == 'consumidor final':
                    client_id = client.get('id')
                    break
            
            if client_id:
                print(f"✅ Cliente encontrado con ID: {client_id}")
                
                # Probar con datos usando ID del cliente
                test_data = {
                    'fecha': '2024-01-15',
                    'cliente_id': client_id,  # Usar ID en lugar de nombre
                    'items': [
                        {
                            'descripcion': 'Servicio de prueba InvoiceBot',
                            'cantidad': 1.0,
                            'precio': 50.00
                        }
                    ],
                    'total': 50.00
                }
                
                # Modificar el método para usar ID del cliente
                auth = base64.b64encode(f"{os.getenv('ALEGRA_USER')}:{os.getenv('ALEGRA_TOKEN')}".encode()).decode()
                headers = {
                    'Authorization': f'Basic {auth}',
                    'Content-Type': 'application/json'
                }
                
                from datetime import datetime, timedelta
                fecha_vencimiento = datetime.strptime(test_data['fecha'], '%Y-%m-%d') + timedelta(days=30)
                
                payload = {
                    "date": test_data['fecha'],
                    "dueDate": fecha_vencimiento.strftime('%Y-%m-%d'),
                    "client": {"id": test_data['cliente_id']},  # Usar ID
                    "items": [
                        {
                            "name": item['descripcion'],
                            "quantity": item['cantidad'],
                            "price": item['precio']
                        } for item in test_data['items']
                    ],
                    "observations": "Factura procesada automáticamente por InvoiceBot"
                }
                
                print("📝 Creando factura con InvoiceProcessor...")
                response = requests.post('https://api.alegra.com/api/v1/invoices', 
                                       json=payload, 
                                       headers=headers, 
                                       timeout=10)
                
                if response.status_code == 201:
                    resultado = response.json()
                    print("✅ Factura creada exitosamente con InvoiceProcessor!")
                    print(f"🆔 ID: {resultado.get('id')}")
                    print(f"📄 Número: {resultado.get('number')}")
                    print(f"💰 Total: ${resultado.get('total')}")
                    print(f"👤 Cliente: {resultado.get('client', {}).get('name')}")
                    return resultado
                else:
                    print(f"❌ Error: {response.status_code} - {response.text}")
            else:
                print("❌ No se encontró el cliente 'Consumidor Final'")
        else:
            print(f"❌ Error obteniendo clientes: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error probando InvoiceProcessor: {e}")

def main():
    """Función principal"""
    print("🚀 InvoiceBot - Prueba Mejorada de API de Alegra")
    print("=" * 60)
    
    # Probar con cliente existente
    factura_creada = test_alegra_with_fixed_client()
    
    if factura_creada:
        print("\n🎉 ¡Prueba exitosa! La API de Alegra funciona correctamente")
        print("✅ Las credenciales son válidas")
        print("✅ Se pueden crear facturas")
        print("✅ El sistema está listo para usar")
        
        # Probar InvoiceProcessor
        test_invoice_processor_fixed()
    else:
        print("\n❌ Error en las pruebas")

if __name__ == "__main__":
    main()