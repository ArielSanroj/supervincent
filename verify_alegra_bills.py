#!/usr/bin/env python3
"""
Script para verificar facturas creadas en Alegra
"""

import os
import sys
import requests
from datetime import datetime, timedelta

class AlegraVerifier:
    """Verificador de facturas en Alegra"""
    
    def __init__(self):
        self.base_url = "https://app.alegra.com/api/v1"
        self.email = os.getenv('ALEGRA_EMAIL')
        self.token = os.getenv('ALEGRA_TOKEN')
        
        if not self.email or not self.token:
            print("❌ Error: Configura las variables de entorno ALEGRA_EMAIL y ALEGRA_TOKEN")
            print("   source load_alegra_env.sh")
            sys.exit(1)
        
        self.auth = (self.email, self.token)
        self.headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
    
    def get_recent_bills(self, days=7):
        """Obtener facturas recientes"""
        try:
            # Calcular fecha de inicio
            start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
            
            params = {
                'startDate': start_date,
                'limit': 50
            }
            
            response = requests.get(
                f"{self.base_url}/bills",
                auth=self.auth,
                headers=self.headers,
                params=params,
                timeout=10
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"❌ Error obteniendo facturas: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ Error: {e}")
            return None
    
    def search_bills_by_number(self, bill_number):
        """Buscar facturas por número"""
        try:
            params = {
                'query': bill_number,
                'limit': 10
            }
            
            response = requests.get(
                f"{self.base_url}/bills",
                auth=self.auth,
                headers=self.headers,
                params=params,
                timeout=10
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"❌ Error buscando facturas: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ Error: {e}")
            return None
    
    def get_bill_details(self, bill_id):
        """Obtener detalles de una factura específica"""
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
            print(f"❌ Error: {e}")
            return None

def print_bill_summary(bill):
    """Imprimir resumen de factura"""
    print(f"   🆔 ID: {bill.get('id', 'N/A')}")
    print(f"   📄 Número: {bill.get('number', 'N/A')}")
    print(f"   📅 Fecha: {bill.get('date', 'N/A')}")
    print(f"   👤 Cliente: {bill.get('client', {}).get('name', 'N/A')}")
    print(f"   💰 Total: ${bill.get('total', 0):,.2f}")
    print(f"   📊 Estado: {bill.get('status', 'N/A')}")
    print(f"   🔗 URL: https://app.alegra.com/bills/{bill.get('id', '')}")

def verify_recent_bills():
    """Verificar facturas recientes"""
    
    print("🔍 VERIFICANDO FACTURAS RECIENTES EN ALEGRA")
    print("=" * 60)
    
    verifier = AlegraVerifier()
    
    # Obtener facturas de los últimos 7 días
    print("📅 Buscando facturas de los últimos 7 días...")
    bills = verifier.get_recent_bills(7)
    
    if not bills:
        print("❌ No se pudieron obtener las facturas")
        return False
    
    if not bills:
        print("📭 No se encontraron facturas recientes")
        return True
    
    print(f"✅ Se encontraron {len(bills)} facturas recientes:")
    print()
    
    for i, bill in enumerate(bills, 1):
        print(f"📄 FACTURA {i}:")
        print_bill_summary(bill)
        print()
    
    return True

def search_specific_bills():
    """Buscar facturas específicas"""
    
    print("🔍 BUSCANDO FACTURAS ESPECÍFICAS")
    print("=" * 60)
    
    verifier = AlegraVerifier()
    
    # Buscar por números de factura conocidos
    search_terms = [
        "18764084252886",  # testfactura1.pdf
        "FAC-2025-001234",  # testfactura2.jpg
        "testfactura",
        "Ariel",
        "TECNOLOGIA AVANZADA"
    ]
    
    found_bills = []
    
    for term in search_terms:
        print(f"🔍 Buscando: '{term}'...")
        bills = verifier.search_bills_by_number(term)
        
        if bills and len(bills) > 0:
            print(f"   ✅ Encontradas {len(bills)} facturas")
            found_bills.extend(bills)
        else:
            print(f"   ❌ No encontradas")
    
    if found_bills:
        print(f"\n📊 RESUMEN DE BÚSQUEDA:")
        print(f"   Total facturas encontradas: {len(found_bills)}")
        print()
        
        for i, bill in enumerate(found_bills, 1):
            print(f"📄 FACTURA {i}:")
            print_bill_summary(bill)
            print()
    else:
        print("\n📭 No se encontraron facturas con los términos de búsqueda")
    
    return len(found_bills) > 0

def verify_connection():
    """Verificar conexión con Alegra"""
    
    print("🔌 VERIFICANDO CONEXIÓN CON ALEGRA")
    print("=" * 60)
    
    verifier = AlegraVerifier()
    
    try:
        response = requests.get(
            f"{verifier.base_url}/users/me",
            auth=verifier.auth,
            headers=verifier.headers,
            timeout=10
        )
        
        if response.status_code == 200:
            user_data = response.json()
            print("✅ Conexión exitosa con Alegra")
            print(f"   👤 Usuario: {user_data.get('name', 'N/A')}")
            print(f"   🏢 Empresa: {user_data.get('company', 'N/A')}")
            print(f"   📧 Email: {user_data.get('email', 'N/A')}")
            return True
        else:
            print(f"❌ Error de conexión: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error de conexión: {e}")
        return False

def main():
    """Función principal"""
    
    print("🔍 VERIFICADOR DE FACTURAS EN ALEGRA")
    print("=" * 60)
    
    # Verificar conexión
    if not verify_connection():
        print("\n❌ No se pudo conectar con Alegra")
        print("   Verifica tus credenciales con: source load_alegra_env.sh")
        return False
    
    print("\n" + "=" * 60)
    
    # Verificar facturas recientes
    if not verify_recent_bills():
        print("❌ Error verificando facturas recientes")
        return False
    
    print("\n" + "=" * 60)
    
    # Buscar facturas específicas
    if not search_specific_bills():
        print("⚠️ No se encontraron facturas específicas")
    
    print("\n" + "=" * 60)
    print("🎉 VERIFICACIÓN COMPLETADA")
    print("=" * 60)
    print("📱 Revisa tu cuenta de Alegra para ver todas las facturas")
    print("🔗 https://app.alegra.com/bills")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)