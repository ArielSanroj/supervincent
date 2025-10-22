#!/usr/bin/env python3
"""
Script para configurar credenciales de Alegra
"""

import os
import sys

def setup_alegra_credentials():
    """Configurar credenciales de Alegra"""
    
    print("🔧 CONFIGURACIÓN DE CREDENCIALES DE ALEGRA")
    print("=" * 50)
    
    print("\n📋 Para usar este script necesitas:")
    print("   1. Una cuenta de Alegra (https://app.alegra.com)")
    print("   2. Tu email de usuario")
    print("   3. Tu token de API")
    
    print("\n🔑 Para obtener tu token de API:")
    print("   1. Ve a https://app.alegra.com/api")
    print("   2. Inicia sesión en tu cuenta")
    print("   3. Copia tu token de API")
    
    print("\n" + "=" * 50)
    
    # Solicitar credenciales
    email = input("📧 Ingresa tu email de Alegra: ").strip()
    if not email:
        print("❌ Email requerido")
        return False
    
    token = input("🔑 Ingresa tu token de API: ").strip()
    if not token:
        print("❌ Token requerido")
        return False
    
    # Crear archivo .env
    env_content = f"""# Credenciales de Alegra
ALEGRA_EMAIL={email}
ALEGRA_TOKEN={token}
"""
    
    try:
        with open('.env', 'w') as f:
            f.write(env_content)
        
        print(f"\n✅ Credenciales guardadas en .env")
        print(f"   📧 Email: {email}")
        print(f"   🔑 Token: {token[:10]}...")
        
        # Crear script de carga de variables
        load_script = """#!/bin/bash
# Cargar variables de entorno para Alegra
export ALEGRA_EMAIL='{}'
export ALEGRA_TOKEN='{}'
echo "✅ Variables de entorno cargadas"
""".format(email, token)
        
        with open('load_alegra_env.sh', 'w') as f:
            f.write(load_script)
        
        os.chmod('load_alegra_env.sh', 0o755)
        
        print(f"\n📝 Script de carga creado: load_alegra_env.sh")
        print(f"   Ejecuta: source load_alegra_env.sh")
        
        return True
        
    except Exception as e:
        print(f"❌ Error guardando credenciales: {e}")
        return False

def test_connection():
    """Probar conexión con Alegra"""
    
    print("\n🔌 PROBANDO CONEXIÓN CON ALEGRA")
    print("=" * 50)
    
    # Cargar variables de entorno
    try:
        with open('.env', 'r') as f:
            for line in f:
                if '=' in line and not line.startswith('#'):
                    key, value = line.strip().split('=', 1)
                    os.environ[key] = value
    except FileNotFoundError:
        print("❌ Archivo .env no encontrado")
        return False
    
    # Probar conexión
    try:
        import requests
        
        email = os.getenv('ALEGRA_EMAIL')
        token = os.getenv('ALEGRA_TOKEN')
        
        if not email or not token:
            print("❌ Credenciales no encontradas")
            return False
        
        response = requests.get(
            "https://app.alegra.com/api/v1/users/me",
            auth=(email, token),
            headers={'Accept': 'application/json'},
            timeout=10
        )
        
        if response.status_code == 200:
            user_data = response.json()
            print("✅ Conexión exitosa con Alegra")
            print(f"   👤 Usuario: {user_data.get('name', 'N/A')}")
            print(f"   🏢 Empresa: {user_data.get('company', 'N/A')}")
            return True
        else:
            print(f"❌ Error de conexión: {response.status_code}")
            print(f"   Respuesta: {response.text}")
            return False
            
    except ImportError:
        print("❌ Error: Instala requests primero")
        print("   pip install requests")
        return False
    except Exception as e:
        print(f"❌ Error de conexión: {e}")
        return False

def main():
    """Función principal"""
    
    if len(sys.argv) > 1 and sys.argv[1] == 'test':
        # Solo probar conexión
        return test_connection()
    
    # Configurar credenciales
    if setup_alegra_credentials():
        print("\n🎉 ¡Configuración completada!")
        print("\n📋 Próximos pasos:")
        print("   1. Ejecuta: source load_alegra_env.sh")
        print("   2. Ejecuta: python setup_alegra_credentials.py test")
        print("   3. Ejecuta: python real_alegra_upload.py")
        return True
    else:
        print("\n❌ Error en la configuración")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)