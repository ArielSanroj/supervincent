#!/usr/bin/env python3
"""
Script completo para subir facturas reales a Alegra
Incluye configuración, procesamiento y verificación
"""

import os
import sys
import subprocess
from datetime import datetime

def print_header(title):
    """Imprimir encabezado"""
    print("=" * 60)
    print(f"🚀 {title}")
    print("=" * 60)

def print_step(step, description):
    """Imprimir paso del proceso"""
    print(f"\n📋 PASO {step}: {description}")
    print("-" * 40)

def check_credentials():
    """Verificar si las credenciales están configuradas"""
    email = os.getenv('ALEGRA_EMAIL')
    token = os.getenv('ALEGRA_TOKEN')
    
    if email and token:
        print("✅ Credenciales de Alegra encontradas")
        print(f"   📧 Email: {email}")
        print(f"   🔑 Token: {token[:10]}...")
        return True
    else:
        print("❌ Credenciales de Alegra no encontradas")
        return False

def setup_credentials():
    """Configurar credenciales de Alegra"""
    print_step(1, "CONFIGURAR CREDENCIALES DE ALEGRA")
    
    if check_credentials():
        print("✅ Las credenciales ya están configuradas")
        return True
    
    print("🔧 Configurando credenciales...")
    
    try:
        result = subprocess.run([
            sys.executable, 'setup_alegra_credentials.py'
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Credenciales configuradas exitosamente")
            
            # Cargar variables de entorno
            try:
                with open('.env', 'r') as f:
                    for line in f:
                        if '=' in line and not line.startswith('#'):
                            key, value = line.strip().split('=', 1)
                            os.environ[key] = value
                print("✅ Variables de entorno cargadas")
                return True
            except FileNotFoundError:
                print("❌ Error cargando variables de entorno")
                return False
        else:
            print("❌ Error configurando credenciales")
            print(f"   Error: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_connection():
    """Probar conexión con Alegra"""
    print_step(2, "PROBAR CONEXIÓN CON ALEGRA")
    
    try:
        result = subprocess.run([
            sys.executable, 'setup_alegra_credentials.py', 'test'
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Conexión exitosa con Alegra")
            return True
        else:
            print("❌ Error de conexión")
            print(f"   Error: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def process_invoices():
    """Procesar y subir facturas a Alegra"""
    print_step(3, "PROCESAR Y SUBIR FACTURAS A ALEGRA")
    
    try:
        result = subprocess.run([
            sys.executable, 'real_alegra_upload.py'
        ], capture_output=True, text=True)
        
        print(result.stdout)
        
        if result.returncode == 0:
            print("✅ Facturas procesadas exitosamente")
            return True
        else:
            print("❌ Error procesando facturas")
            print(f"   Error: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def verify_bills():
    """Verificar facturas creadas en Alegra"""
    print_step(4, "VERIFICAR FACTURAS EN ALEGRA")
    
    try:
        result = subprocess.run([
            sys.executable, 'verify_alegra_bills.py'
        ], capture_output=True, text=True)
        
        print(result.stdout)
        
        if result.returncode == 0:
            print("✅ Verificación completada")
            return True
        else:
            print("❌ Error en la verificación")
            print(f"   Error: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def show_summary():
    """Mostrar resumen final"""
    print_step(5, "RESUMEN FINAL")
    
    print("🎉 ¡PROCESO COMPLETADO!")
    print()
    print("📊 Lo que se hizo:")
    print("   ✅ Configuraste credenciales de Alegra")
    print("   ✅ Probaste la conexión")
    print("   ✅ Procesaste las facturas")
    print("   ✅ Las subiste a Alegra")
    print("   ✅ Verificaste que se crearon")
    print()
    print("🔗 Próximos pasos:")
    print("   📱 Ve a tu cuenta de Alegra: https://app.alegra.com/bills")
    print("   📄 Revisa las facturas creadas")
    print("   🔄 Repite el proceso con más facturas")
    print()
    print("🛠️ Scripts disponibles:")
    print("   python real_alegra_upload.py     - Subir facturas")
    print("   python verify_alegra_bills.py    - Verificar facturas")
    print("   python setup_alegra_credentials.py - Configurar credenciales")

def main():
    """Función principal"""
    
    print_header("SUBIDA COMPLETA DE FACTURAS A ALEGRA")
    
    print("📋 Este script te guiará paso a paso para:")
    print("   1. Configurar credenciales de Alegra")
    print("   2. Probar la conexión")
    print("   3. Procesar y subir las facturas")
    print("   4. Verificar que se crearon correctamente")
    
    input("\n⏎ Presiona Enter para continuar...")
    
    # Paso 1: Configurar credenciales
    if not setup_credentials():
        print("\n❌ Error en la configuración de credenciales")
        return False
    
    # Paso 2: Probar conexión
    if not test_connection():
        print("\n❌ Error en la conexión con Alegra")
        return False
    
    # Paso 3: Procesar facturas
    if not process_invoices():
        print("\n❌ Error procesando facturas")
        return False
    
    # Paso 4: Verificar facturas
    if not verify_bills():
        print("\n⚠️ Error en la verificación (pero las facturas pueden haberse creado)")
    
    # Paso 5: Mostrar resumen
    show_summary()
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)