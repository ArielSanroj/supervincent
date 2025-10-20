#!/usr/bin/env python3
"""
Script para publicar facturas en borrador en Alegra
"""

import requests
import base64
from dotenv import load_dotenv
import os

# Cargar variables de entorno
load_dotenv()

def publish_invoices():
    """Publicar facturas en borrador"""
    print("📢 Publicando facturas en borrador...")
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
        # Obtener todas las facturas
        response = requests.get('https://api.alegra.com/api/v1/invoices', headers=headers, timeout=10)
        
        if response.status_code == 200:
            invoices = response.json()
            print(f"📄 Total de facturas encontradas: {len(invoices)}")
            
            published_count = 0
            
            for invoice in invoices:
                invoice_id = invoice.get('id')
                status = invoice.get('status')
                total = invoice.get('total')
                
                print(f"\n📋 Factura ID: {invoice_id}")
                print(f"   💰 Total: ${total}")
                print(f"   📊 Estado actual: {status}")
                
                if status == 'draft':
                    print("   📢 Publicando factura...")
                    
                    # Publicar la factura
                    publish_response = requests.put(f'https://api.alegra.com/api/v1/invoices/{invoice_id}/publish', 
                                                  headers=headers, 
                                                  timeout=10)
                    
                    print(f"   📡 Status Code: {publish_response.status_code}")
                    
                    if publish_response.status_code == 200:
                        published_invoice = publish_response.json()
                        print("   ✅ ¡Factura publicada exitosamente!")
                        print(f"   📄 Número: {published_invoice.get('number', 'N/A')}")
                        print(f"   📊 Nuevo estado: {published_invoice.get('status')}")
                        published_count += 1
                    else:
                        print(f"   ❌ Error publicando factura: {publish_response.status_code}")
                        print(f"   📝 Respuesta: {publish_response.text}")
                else:
                    print(f"   ℹ️ Factura ya está publicada o en otro estado")
            
            print(f"\n🎉 Proceso completado!")
            print(f"✅ Facturas publicadas: {published_count}")
            
            if published_count > 0:
                print("\n💡 Ahora deberías ver las facturas en tu panel de Alegra:")
                print("   - Ve a la sección 'Facturas' o 'Invoices'")
                print("   - Refresca la página")
                print("   - Las facturas ya no estarán en borrador")
            
        else:
            print(f"❌ Error obteniendo facturas: {response.status_code}")
            print(f"📝 Respuesta: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

def check_published_invoices():
    """Verificar facturas publicadas"""
    print("\n🔍 Verificando facturas publicadas...")
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
        response = requests.get('https://api.alegra.com/api/v1/invoices', headers=headers, timeout=10)
        
        if response.status_code == 200:
            invoices = response.json()
            
            print(f"📄 Total de facturas: {len(invoices)}")
            
            # Contar por estado
            draft_count = 0
            published_count = 0
            
            for invoice in invoices:
                status = invoice.get('status')
                if status == 'draft':
                    draft_count += 1
                elif status == 'published':
                    published_count += 1
            
            print(f"📊 Facturas en borrador: {draft_count}")
            print(f"📊 Facturas publicadas: {published_count}")
            
            if published_count > 0:
                print("\n✅ ¡Tienes facturas publicadas que deberían aparecer en tu panel!")
            else:
                print("\n⚠️ No hay facturas publicadas")
                
        else:
            print(f"❌ Error: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

def main():
    """Función principal"""
    print("📢 InvoiceBot - Publicador de Facturas en Alegra")
    print("=" * 60)
    
    # Publicar facturas
    publish_invoices()
    
    # Verificar resultado
    check_published_invoices()

if __name__ == "__main__":
    main()