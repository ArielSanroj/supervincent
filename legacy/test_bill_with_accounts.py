#!/usr/bin/env python3
"""
Script de prueba para crear bills con cuentas contables en Alegra
"""

import requests
import base64
from dotenv import load_dotenv
import os

# Cargar variables de entorno
load_dotenv()

def test_bill_with_accounts():
    """Probar creación de bill con cuentas contables"""
    print("🧪 Probando creación de bill con cuentas contables...")
    
    # Configurar autenticación
    email = os.getenv('ALEGRA_USER')
    token = os.getenv('ALEGRA_TOKEN')
    base_url = 'https://api.alegra.com/api/v1'
    
    credentials = f"{email}:{token}"
    auth_header = f"Basic {base64.b64encode(credentials.encode()).decode()}"
    
    headers = {
        'Authorization': auth_header,
        'Content-Type': 'application/json'
    }
    
    # Obtener contactos existentes
    print("📋 Obteniendo contactos...")
    response = requests.get(f'{base_url}/contacts', headers=headers, timeout=10)
    
    if response.status_code == 200:
        contacts = response.json()
        if contacts:
            provider_id = contacts[0].get('id')
            print(f"👤 Usando proveedor: {contacts[0].get('name')} (ID: {provider_id})")
        else:
            print("❌ No hay contactos disponibles")
            return
    else:
        print(f"❌ Error obteniendo contactos: {response.status_code}")
        return
    
    # Crear bill con cuentas contables directas
    print("📄 Creando bill con cuentas contables...")
    payload = {
        "date": "2025-01-15",
        "dueDate": "2025-02-14",
        "provider": {"id": provider_id},
        "items": [
            {
                "name": "Producto de prueba",
                "quantity": 1,
                "price": 100.00,
                "accountingAccount": {"id": 1}  # Cuenta contable para el item
            }
        ],
        "observations": "Bill de prueba con cuentas contables"
    }
    
    print(f"📤 Payload: {payload}")
    
    response = requests.post(f'{base_url}/bills', 
                           json=payload, 
                           headers=headers, 
                           timeout=30)
    
    print(f"📡 Status Code: {response.status_code}")
    print(f"📝 Respuesta: {response.text}")
    
    if response.status_code == 201:
        bill = response.json()
        print("✅ ¡Bill creada exitosamente!")
        print(f"🆔 ID: {bill.get('id')}")
        print(f"💰 Total: ${bill.get('total')}")
    else:
        print("❌ Error creando bill")

if __name__ == "__main__":
    test_bill_with_accounts()