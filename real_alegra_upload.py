#!/usr/bin/env python3
"""
Script para subir realmente las facturas a Alegra
Conecta con la API real de Alegra y crea las facturas
"""

import os
import sys
import json
import requests
import pdfplumber
import re
from datetime import datetime
from config import PDF_PATTERNS

class AlegraRealClient:
    """Cliente real para conectar con Alegra API"""
    
    def __init__(self):
        self.base_url = "https://app.alegra.com/api/v1"
        self.email = os.getenv('ALEGRA_EMAIL')
        self.token = os.getenv('ALEGRA_TOKEN')
        
        if not self.email or not self.token:
            print("❌ Error: Configura las variables de entorno ALEGRA_EMAIL y ALEGRA_TOKEN")
            print("   export ALEGRA_EMAIL='tu-email@ejemplo.com'")
            print("   export ALEGRA_TOKEN='tu-token-de-alegra'")
            sys.exit(1)
        
        self.auth = (self.email, self.token)
        self.headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
    
    def test_connection(self):
        """Probar conexión con Alegra"""
        try:
            response = requests.get(
                f"{self.base_url}/users/me",
                auth=self.auth,
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code == 200:
                user_data = response.json()
                print(f"✅ Conexión exitosa con Alegra")
                print(f"   👤 Usuario: {user_data.get('name', 'N/A')}")
                print(f"   🏢 Empresa: {user_data.get('company', 'N/A')}")
                return True
            else:
                print(f"❌ Error de conexión: {response.status_code}")
                print(f"   Respuesta: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Error conectando con Alegra: {e}")
            return False
    
    def get_or_create_contact(self, contact_data):
        """Obtener o crear contacto en Alegra"""
        try:
            # Buscar contacto existente
            search_params = {
                'query': contact_data.get('name', ''),
                'type': 'client'
            }
            
            response = requests.get(
                f"{self.base_url}/contacts",
                auth=self.auth,
                headers=self.headers,
                params=search_params,
                timeout=10
            )
            
            if response.status_code == 200:
                contacts = response.json()
                if contacts and len(contacts) > 0:
                    contact = contacts[0]
                    print(f"✅ Contacto encontrado: {contact['name']} (ID: {contact['id']})")
                    return contact
            
            # Crear nuevo contacto si no existe
            new_contact = {
                'name': contact_data.get('name', 'Cliente Sin Nombre'),
                'type': 'client',
                'identification': contact_data.get('nit', ''),
                'email': contact_data.get('email', ''),
                'phonePrimary': contact_data.get('phone', ''),
                'address': contact_data.get('address', '')
            }
            
            response = requests.post(
                f"{self.base_url}/contacts",
                auth=self.auth,
                headers=self.headers,
                json=new_contact,
                timeout=10
            )
            
            if response.status_code == 201:
                contact = response.json()
                print(f"✅ Contacto creado: {contact['name']} (ID: {contact['id']})")
                return contact
            else:
                print(f"❌ Error creando contacto: {response.status_code}")
                print(f"   Respuesta: {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ Error con contacto: {e}")
            return None
    
    def create_bill(self, bill_data):
        """Crear factura de compra en Alegra"""
        try:
            response = requests.post(
                f"{self.base_url}/bills",
                auth=self.auth,
                headers=self.headers,
                json=bill_data,
                timeout=10
            )
            
            if response.status_code == 201:
                bill = response.json()
                print(f"✅ Factura creada exitosamente!")
                print(f"   🆔 ID: {bill['id']}")
                print(f"   📄 Número: {bill.get('number', 'N/A')}")
                print(f"   💰 Total: ${bill.get('total', 0):,.2f}")
                print(f"   📅 Fecha: {bill.get('date', 'N/A')}")
                return bill
            else:
                print(f"❌ Error creando factura: {response.status_code}")
                print(f"   Respuesta: {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ Error creando factura: {e}")
            return None
    
    def get_bill(self, bill_id):
        """Obtener factura por ID"""
        try:
            response = requests.get(
                f"{self.base_url}/bills/{bill_id}",
                auth=self.auth,
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"❌ Error obteniendo factura: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ Error obteniendo factura: {e}")
            return None

def extract_pdf_data(file_path):
    """Extraer datos de PDF"""
    print(f"🔍 Extrayendo datos de {file_path}...")
    
    try:
        with pdfplumber.open(file_path) as pdf:
            text = ''
            for page in pdf.pages:
                text += page.extract_text() or ''
        
        print(f"✅ Texto extraído: {len(text)} caracteres")
        
        # Extraer datos con patrones
        patterns = PDF_PATTERNS.copy()
        datos = {}
        
        for tipo, patrones_lista in patterns.items():
            for patron in patrones_lista:
                matches = re.findall(patron, text, re.IGNORECASE | re.MULTILINE)
                if matches:
                    if tipo not in datos:
                        datos[tipo] = []
                    datos[tipo].extend(matches)
        
        # Procesar datos extraídos
        processed_data = {
            'fecha': datos.get('fecha', ['N/A'])[0] if datos.get('fecha') else 'N/A',
            'proveedor': datos.get('proveedor', ['N/A'])[0] if datos.get('proveedor') else 'N/A',
            'nit_proveedor': datos.get('nit_proveedor', ['N/A'])[0] if datos.get('nit_proveedor') else 'N/A',
            'total': float(datos.get('total', ['0'])[0].replace(',', '')) if datos.get('total') else 0,
            'iva': float(datos.get('iva', ['0'])[0].replace(',', '')) if datos.get('iva') else 0,
            'numero_factura': datos.get('numero_factura', ['N/A'])[0] if datos.get('numero_factura') else 'N/A',
            'cliente': datos.get('cliente', ['N/A'])[0] if datos.get('cliente') else 'N/A'
        }
        
        return processed_data
        
    except Exception as e:
        print(f"❌ Error extrayendo datos: {e}")
        return None

def create_alegra_bill_data(datos, contact):
    """Crear estructura de datos para Alegra"""
    
    # Calcular subtotal
    subtotal = datos['total'] - datos['iva']
    
    # Crear items
    items = [{
        'id': 1,  # ID del item en Alegra
        'description': f"Factura {datos['numero_factura']} - {datos['proveedor']}",
        'quantity': 1,
        'price': subtotal,
        'discount': 0,
        'tax': [{
            'id': 1,  # ID del impuesto en Alegra
            'amount': datos['iva']
        }] if datos['iva'] > 0 else []
    }]
    
    # Estructura de la factura
    bill_data = {
        'date': datos['fecha'],
        'dueDate': datos['fecha'],  # Misma fecha de vencimiento
        'client': {
            'id': contact['id']
        },
        'items': items,
        'total': datos['total'],
        'subtotal': subtotal,
        'taxes': [{
            'id': 1,
            'amount': datos['iva']
        }] if datos['iva'] > 0 else [],
        'notes': f"Factura procesada automáticamente - Número: {datos['numero_factura']}",
        'status': 'open'
    }
    
    return bill_data

def process_invoice_to_alegra(file_path):
    """Procesar factura y subirla a Alegra"""
    
    print("=" * 60)
    print(f"🚀 PROCESANDO {file_path.upper()} A ALEGRA")
    print("=" * 60)
    
    # Inicializar cliente de Alegra
    alegra = AlegraRealClient()
    
    # Probar conexión
    print("\n🔌 Probando conexión con Alegra...")
    if not alegra.test_connection():
        return False
    
    # Extraer datos del PDF
    print(f"\n📄 Extrayendo datos de {file_path}...")
    datos = extract_pdf_data(file_path)
    if not datos:
        return False
    
    # Mostrar datos extraídos
    print("\n📊 Datos extraídos:")
    print(f"   📅 Fecha: {datos['fecha']}")
    print(f"   👤 Cliente: {datos['cliente']}")
    print(f"   🏢 Proveedor: {datos['proveedor']}")
    print(f"   🆔 NIT: {datos['nit_proveedor']}")
    print(f"   💰 Total: ${datos['total']:,.2f}")
    print(f"   🧾 IVA: ${datos['iva']:,.2f}")
    print(f"   📄 Número: {datos['numero_factura']}")
    
    # Crear o obtener contacto
    print(f"\n👤 Procesando contacto: {datos['cliente']}")
    contact_data = {
        'name': datos['cliente'],
        'nit': datos['nit_proveedor'],
        'email': f"{datos['cliente'].lower().replace(' ', '.')}@ejemplo.com",
        'phone': '300-000-0000',
        'address': 'Dirección no especificada'
    }
    
    contact = alegra.get_or_create_contact(contact_data)
    if not contact:
        print("❌ No se pudo procesar el contacto")
        return False
    
    # Crear estructura de factura para Alegra
    print(f"\n💾 Preparando factura para Alegra...")
    bill_data = create_alegra_bill_data(datos, contact)
    
    print("📋 Estructura de la factura:")
    print(f"   📅 Fecha: {bill_data['date']}")
    print(f"   👤 Cliente ID: {bill_data['client']['id']}")
    print(f"   💰 Total: ${bill_data['total']:,.2f}")
    print(f"   🧾 IVA: ${bill_data['taxes'][0]['amount']:,.2f}" if bill_data['taxes'] else "   🧾 IVA: $0.00")
    print(f"   📝 Notas: {bill_data['notes']}")
    
    # Crear factura en Alegra
    print(f"\n🚀 Creando factura en Alegra...")
    bill = alegra.create_bill(bill_data)
    
    if bill:
        print(f"\n✅ ¡FACTURA CREADA EXITOSAMENTE EN ALEGRA!")
        print(f"   🆔 ID Alegra: {bill['id']}")
        print(f"   📄 Número: {bill.get('number', 'N/A')}")
        print(f"   💰 Total: ${bill.get('total', 0):,.2f}")
        print(f"   📅 Fecha: {bill.get('date', 'N/A')}")
        print(f"   🔗 URL: https://app.alegra.com/bills/{bill['id']}")
        
        # Verificar que se creó correctamente
        print(f"\n🔍 Verificando factura creada...")
        verification = alegra.get_bill(bill['id'])
        if verification:
            print("✅ Verificación exitosa - La factura existe en Alegra")
        else:
            print("⚠️ No se pudo verificar la factura")
        
        return True
    else:
        print("❌ Error creando factura en Alegra")
        return False

def main():
    """Función principal"""
    print("🚀 SUBIENDO FACTURAS REALES A ALEGRA")
    print("=" * 60)
    
    # Verificar variables de entorno
    if not os.getenv('ALEGRA_EMAIL') or not os.getenv('ALEGRA_TOKEN'):
        print("❌ Error: Configura las variables de entorno primero:")
        print("   export ALEGRA_EMAIL='tu-email@ejemplo.com'")
        print("   export ALEGRA_TOKEN='tu-token-de-alegra'")
        print("\n💡 Puedes obtener tu token en: https://app.alegra.com/api")
        return False
    
    # Procesar testfactura1.pdf
    if os.path.exists('testfactura1.pdf'):
        success1 = process_invoice_to_alegra('testfactura1.pdf')
    else:
        print("❌ testfactura1.pdf no encontrado")
        success1 = False
    
    print("\n" + "=" * 60)
    
    # Procesar testfactura2.jpg (simulado)
    if os.path.exists('testfactura2.jpg'):
        print("📷 testfactura2.jpg detectado - Simulando procesamiento...")
        print("   (Para JPG necesitarías OCR real con Tesseract)")
        success2 = False
    else:
        print("❌ testfactura2.jpg no encontrado")
        success2 = False
    
    # Resumen final
    print("\n" + "=" * 60)
    print("📊 RESUMEN FINAL")
    print("=" * 60)
    
    if success1:
        print("✅ testfactura1.pdf: Subida exitosa a Alegra")
    else:
        print("❌ testfactura1.pdf: Error en la subida")
    
    if success2:
        print("✅ testfactura2.jpg: Subida exitosa a Alegra")
    else:
        print("❌ testfactura2.jpg: No procesado (requiere OCR)")
    
    print(f"\n🎉 ¡Proceso completado!")
    print(f"   📱 Revisa tu cuenta de Alegra para ver las facturas creadas")
    print(f"   🔗 https://app.alegra.com/bills")
    
    return success1 or success2

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)