#!/usr/bin/env python3
"""
Script para verificar las facturas creadas en Alegra
"""

import requests
import base64
from dotenv import load_dotenv
import os

# Cargar variables de entorno
load_dotenv()

def check_invoices_in_alegra():
    """Verificar facturas existentes en Alegra"""
    print("🔍 Verificando facturas en Alegra...")
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
    
    try:
        response = requests.get('https://api.alegra.com/api/v1/invoices', headers=headers, timeout=10)
        
        print(f"📡 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            invoices = response.json()
            print(f"📄 Total de facturas encontradas: {len(invoices)}")
            
            if invoices:
                print("\n📋 Lista de facturas:")
                print("-" * 60)
                for i, invoice in enumerate(invoices, 1):
                    print(f"{i}. ID: {invoice.get('id')}")
                    print(f"   📄 Número: {invoice.get('number', 'Sin número')}")
                    print(f"   📅 Fecha: {invoice.get('date')}")
                    print(f"   💰 Total: ${invoice.get('total', 0)}")
                    print(f"   👤 Cliente: {invoice.get('client', {}).get('name', 'N/A')}")
                    print(f"   📝 Observaciones: {invoice.get('observations', 'N/A')[:100]}...")
                    print(f"   📊 Estado: {invoice.get('status', 'N/A')}")
                    print("-" * 60)
            else:
                print("❌ No se encontraron facturas en Alegra")
                print("💡 Esto puede significar que:")
                print("   - Las facturas se crearon pero no se guardaron")
                print("   - Hay un problema con la API")
                print("   - Las facturas están en estado borrador")
        else:
            print(f"❌ Error obteniendo facturas: {response.status_code}")
            print(f"📝 Respuesta: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

def check_company_info():
    """Verificar información de la empresa"""
    print("\n🏢 Información de la empresa:")
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
        response = requests.get('https://api.alegra.com/api/v1/company', headers=headers, timeout=10)
        
        if response.status_code == 200:
            company = response.json()
            print(f"🏢 Empresa: {company.get('name')}")
            print(f"📧 Email: {company.get('email', 'N/A')}")
            print(f"🌍 País: {company.get('country', 'N/A')}")
            print(f"💰 Moneda: {company.get('currency', {}).get('code', 'N/A')}")
        else:
            print(f"❌ Error obteniendo info de empresa: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

def create_test_invoice():
    """Crear una factura de prueba simple"""
    print("\n🧪 Creando factura de prueba...")
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
    
    # Obtener cliente
    try:
        client_response = requests.get('https://api.alegra.com/api/v1/contacts', headers=headers, timeout=10)
        if client_response.status_code == 200:
            clients = client_response.json()
            if clients:
                client_id = clients[0].get('id')
                client_name = clients[0].get('name')
                
                # Obtener item
                item_response = requests.get('https://api.alegra.com/api/v1/items', headers=headers, timeout=10)
                if item_response.status_code == 200:
                    items = item_response.json()
                    if items:
                        item_id = items[0].get('id')
                        item_name = items[0].get('name')
                        
                        print(f"👤 Cliente: {client_name} (ID: {client_id})")
                        print(f"📦 Item: {item_name} (ID: {item_id})")
                        
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
                            "observations": "Factura de prueba - Verificación de sistema"
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
                            print(f"   📅 Fecha: {invoice.get('date')}")
                            
                            # Verificar que aparece en la lista
                            print("\n🔍 Verificando que la factura aparece en la lista...")
                            check_response = requests.get('https://api.alegra.com/api/v1/invoices', headers=headers, timeout=10)
                            if check_response.status_code == 200:
                                all_invoices = check_response.json()
                                print(f"   📊 Total de facturas ahora: {len(all_invoices)}")
                                
                                # Buscar la factura recién creada
                                for inv in all_invoices:
                                    if inv.get('id') == invoice.get('id'):
                                        print(f"   ✅ Factura encontrada en la lista!")
                                        print(f"   📝 Observaciones: {inv.get('observations')}")
                                        break
                                else:
                                    print("   ❌ Factura no encontrada en la lista")
                            
                            return invoice
                        else:
                            print(f"   ❌ Error creando factura: {invoice_response.status_code}")
                            print(f"   📝 Respuesta: {invoice_response.text}")
                    else:
                        print("❌ No hay items disponibles")
                else:
                    print(f"❌ Error obteniendo items: {item_response.status_code}")
            else:
                print("❌ No hay clientes disponibles")
        else:
            print(f"❌ Error obteniendo clientes: {client_response.status_code}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    
    return None

def main():
    """Función principal"""
    print("🔍 InvoiceBot - Verificación de Facturas en Alegra")
    print("=" * 60)
    
    # Verificar información de la empresa
    check_company_info()
    
    # Verificar facturas existentes
    check_invoices_in_alegra()
    
    # Crear factura de prueba
    test_invoice = create_test_invoice()
    
    if test_invoice:
        print("\n🎉 ¡Verificación completada!")
        print("✅ La API de Alegra funciona correctamente")
        print("✅ Se pueden crear facturas")
        print("✅ Las facturas aparecen en la lista")
        print("\n💡 Si no ves las facturas en tu panel web:")
        print("   - Refresca la página")
        print("   - Verifica que estés en la sección correcta")
        print("   - Revisa los filtros de fecha")
    else:
        print("\n⚠️ Hay un problema con la creación de facturas")
        print("❌ Revisa los logs para más detalles")

if __name__ == "__main__":
    main()