#!/usr/bin/env python3
"""
Script para probar endpoints disponibles en Alegra
"""

import requests
import base64
from dotenv import load_dotenv
import os

# Cargar variables de entorno
load_dotenv()

def test_endpoints():
    """Probar endpoints disponibles en Alegra"""
    print("🔍 Probando endpoints disponibles en Alegra...")
    
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
    
    # Lista de endpoints a probar
    endpoints = [
        '/company',
        '/contacts',
        '/items',
        '/invoices',
        '/bills',
        '/reports/trial-balance',
        '/reports/general-ledger',
        '/reports/journal',
        '/reports/income-statement',
        '/reports/balance-sheet',
        '/accounts',
        '/categories',
        '/units'
    ]
    
    for endpoint in endpoints:
        print(f"\n📡 Probando: {endpoint}")
        try:
            response = requests.get(f'{base_url}{endpoint}', headers=headers, timeout=10)
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list):
                    print(f"   ✅ Datos: {len(data)} elementos")
                else:
                    print(f"   ✅ Datos: {type(data).__name__}")
            elif response.status_code == 403:
                print(f"   ❌ Forbidden - No tienes permisos para este endpoint")
            elif response.status_code == 404:
                print(f"   ❌ Not Found - Endpoint no existe")
            else:
                print(f"   ⚠️ Error: {response.text[:100]}")
                
        except Exception as e:
            print(f"   ❌ Exception: {e}")

if __name__ == "__main__":
    test_endpoints()