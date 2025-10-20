#!/usr/bin/env python3
"""
Script para verificar la estructura de items en Alegra
"""

import requests
import base64
from dotenv import load_dotenv
import os
import json

# Cargar variables de entorno
load_dotenv()

def test_item_structure():
    """Verificar estructura de items en Alegra"""
    print("🔍 Verificando estructura de items en Alegra...")
    
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
    
    # Obtener items existentes
    print("📦 Obteniendo items...")
    response = requests.get(f'{base_url}/items', headers=headers, timeout=10)
    
    if response.status_code == 200:
        items = response.json()
        print(f"✅ Items encontrados: {len(items)}")
        
        if items:
            # Mostrar estructura del primer item
            item = items[0]
            print(f"\n📋 Estructura del item '{item.get('name')}':")
            print(json.dumps(item, indent=2, ensure_ascii=False))
            
            # Verificar si tiene cuenta contable
            if 'accountingAccount' in item:
                print(f"\n✅ Item tiene cuenta contable: {item['accountingAccount']}")
            else:
                print(f"\n❌ Item NO tiene cuenta contable")
                
        else:
            print("❌ No hay items disponibles")
    else:
        print(f"❌ Error obteniendo items: {response.status_code}")
        print(f"📝 Respuesta: {response.text}")

if __name__ == "__main__":
    test_item_structure()