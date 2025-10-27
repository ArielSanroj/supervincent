#!/usr/bin/env python3
"""
Demostración de cómo usar el token de Alegra correctamente
"""

import base64
import requests
from dotenv import load_dotenv
import os

# Cargar variables de entorno
load_dotenv()

def demo_token_usage():
    """Demostrar el uso correcto del token de Alegra"""
    print("🔐 Demostración del uso del token de Alegra")
    print("=" * 60)
    
    # Obtener credenciales del .env
    email = os.getenv('ALEGRA_USER')
    token = os.getenv('ALEGRA_TOKEN')
    
    print(f"📧 Email: {email}")
    print(f"🔑 Token: {token}")
    print()
    
    # Paso 1: Combinar email y token
    print("📝 Paso 1: Combinar email y token con dos puntos")
    credentials = f"{email}:{token}"
    print(f"   Resultado: {credentials}")
    print()
    
    # Paso 2: Codificar en Base64
    print("🔢 Paso 2: Codificar en Base64")
    encoded_credentials = base64.b64encode(credentials.encode()).decode()
    print(f"   Resultado: {encoded_credentials}")
    print()
    
    # Paso 3: Crear header de autorización
    print("📋 Paso 3: Crear header de autorización")
    auth_header = f"Basic {encoded_credentials}"
    print(f"   Authorization: {auth_header}")
    print()
    
    # Paso 4: Probar la conexión
    print("🧪 Paso 4: Probar conexión con Alegra")
    headers = {
        'Authorization': auth_header,
        'Content-Type': 'application/json'
    }
    
    try:
        response = requests.get('https://api.alegra.com/api/v1/company', 
                              headers=headers, 
                              timeout=10)
        
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code == 200:
            company_info = response.json()
            print("   ✅ ¡Conexión exitosa!")
            print(f"   🏢 Empresa: {company_info.get('name', 'N/A')}")
            print(f"   📧 Email: {company_info.get('email', 'N/A')}")
        else:
            print(f"   ❌ Error: {response.status_code}")
            print(f"   📝 Respuesta: {response.text}")
            
    except Exception as e:
        print(f"   ❌ Error de conexión: {e}")
    
    print()
    return headers

def test_create_invoice(headers):
    """Probar creación de factura con el token correcto"""
    print("🧪 Probando creación de factura...")
    print("=" * 40)
    
    # Obtener clientes primero
    try:
        response = requests.get('https://api.alegra.com/api/v1/contacts', 
                              headers=headers, 
                              timeout=10)
        
        if response.status_code == 200:
            clients = response.json()
            print(f"✅ Clientes encontrados: {len(clients)}")
            
            if clients:
                # Usar el primer cliente
                client = clients[0]
                client_id = client.get('id')
                client_name = client.get('name')
                
                print(f"👤 Usando cliente: {client_name} (ID: {client_id})")
                
                # Crear factura de prueba
                test_invoice = {
                    "date": "2024-01-15",
                    "dueDate": "2024-02-14",
                    "client": {"id": client_id},  # Usar ID del cliente
                    "items": [
                        {
                            "name": "Servicio de prueba - Demo Token",
                            "quantity": 1,
                            "price": 100.00
                        }
                    ],
                    "observations": "Factura de prueba creada con token correcto"
                }
                
                print("📄 Creando factura de prueba...")
                response = requests.post('https://api.alegra.com/api/v1/invoices', 
                                       json=test_invoice, 
                                       headers=headers, 
                                       timeout=10)
                
                print(f"   Status Code: {response.status_code}")
                
                if response.status_code == 201:
                    invoice = response.json()
                    print("   ✅ ¡Factura creada exitosamente!")
                    print(f"   🆔 ID: {invoice.get('id')}")
                    print(f"   📄 Número: {invoice.get('number')}")
                    print(f"   💰 Total: ${invoice.get('total')}")
                    print(f"   👤 Cliente: {invoice.get('client', {}).get('name')}")
                    
                    # Opcional: Eliminar la factura de prueba
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
                    print(f"   ❌ Error creando factura: {response.status_code}")
                    print(f"   📝 Respuesta: {response.text}")
            else:
                print("❌ No hay clientes disponibles")
        else:
            print(f"❌ Error obteniendo clientes: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    
    return False

def show_code_example():
    """Mostrar ejemplo de código para usar en tu proyecto"""
    print("\n💻 Ejemplo de código para tu proyecto:")
    print("=" * 50)
    
    code_example = '''
# En tu archivo .env
ALEGRA_USER=asanroj10@gmail.com
ALEGRA_TOKEN=***REMOVED***

# En tu código Python
import base64
import requests
from dotenv import load_dotenv
import os

load_dotenv()

# Obtener credenciales
email = os.getenv('ALEGRA_USER')
token = os.getenv('ALEGRA_TOKEN')

# Crear autenticación
credentials = f"{email}:{token}"
auth_header = f"Basic {base64.b64encode(credentials.encode()).decode()}"

# Headers para las peticiones
headers = {
    'Authorization': auth_header,
    'Content-Type': 'application/json'
}

# Hacer petición a Alegra
response = requests.get('https://api.alegra.com/api/v1/company', headers=headers)
print(response.json())
'''
    
    print(code_example)

def main():
    """Función principal"""
    print("🚀 Demo: Uso correcto del token de Alegra")
    print("=" * 60)
    
    # Demostrar uso del token
    headers = demo_token_usage()
    
    # Probar creación de factura
    if headers:
        success = test_create_invoice(headers)
        
        if success:
            print("\n🎉 ¡Todo funciona perfectamente!")
            print("✅ El token está configurado correctamente")
            print("✅ Puedes crear facturas en Alegra")
            print("✅ Tu sistema InvoiceBot está listo para usar")
        else:
            print("\n⚠️ Hay algún problema con la creación de facturas")
    
    # Mostrar ejemplo de código
    show_code_example()

if __name__ == "__main__":
    main()