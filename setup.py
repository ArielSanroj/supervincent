#!/usr/bin/env python3
"""
Script de instalación y configuración inicial para InvoiceBot
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def print_banner():
    """Mostrar banner de instalación"""
    print("""
╔══════════════════════════════════════════════════════════════╗
║                    InvoiceBot - Setup                       ║
║              Bot Contable Inteligente                       ║
╚══════════════════════════════════════════════════════════════╝
""")

def check_python_version():
    """Verificar versión de Python"""
    print("🐍 Verificando versión de Python...")
    
    if sys.version_info < (3, 8):
        print("❌ Se requiere Python 3.8 o superior")
        print(f"   Versión actual: {sys.version}")
        return False
    
    print(f"✅ Python {sys.version.split()[0]} detectado")
    return True

def create_directories():
    """Crear estructura de directorios"""
    print("📁 Creando estructura de directorios...")
    
    directories = [
        'logs',
        'reports',
        'facturas',
        'facturas/processed',
        'facturas/error',
        'backup',
        'config'
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"   ✅ {directory}/")
    
    print("✅ Estructura de directorios creada")

def install_dependencies():
    """Instalar dependencias"""
    print("📦 Instalando dependencias...")
    
    try:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'])
        print("✅ Dependencias instaladas correctamente")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error instalando dependencias: {e}")
        return False

def create_env_file():
    """Crear archivo .env si no existe"""
    print("🔐 Configurando archivo .env...")
    
    env_file = Path('.env')
    
    if env_file.exists():
        print("   ⚠️ Archivo .env ya existe")
        return True
    
    env_content = """# Configuración de Alegra API
ALEGRA_USER=tu_email@ejemplo.com
ALEGRA_TOKEN=tu_token_de_alegra

# Configuración opcional
ALEGRA_BASE_URL=https://api.alegra.com/api/v1

# Configuración de logging
LOG_LEVEL=INFO

# Configuración de monitoreo
WATCH_FOLDER=facturas
"""
    
    try:
        with open('.env', 'w') as f:
            f.write(env_content)
        print("   ✅ Archivo .env creado")
        print("   ⚠️ IMPORTANTE: Edita .env con tus credenciales de Alegra")
        return True
    except Exception as e:
        print(f"   ❌ Error creando .env: {e}")
        return False

def create_sample_config():
    """Crear archivos de configuración de ejemplo"""
    print("⚙️ Creando archivos de configuración...")
    
    # Configuración de logging
    logging_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "standard": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            }
        },
        "handlers": {
            "default": {
                "level": "INFO",
                "formatter": "standard",
                "class": "logging.StreamHandler"
            },
            "file": {
                "level": "INFO",
                "formatter": "standard",
                "class": "logging.FileHandler",
                "filename": "logs/invoicebot.log",
                "mode": "a"
            }
        },
        "loggers": {
            "": {
                "handlers": ["default", "file"],
                "level": "INFO",
                "propagate": False
            }
        }
    }
    
    try:
        import json
        with open('config/logging.json', 'w') as f:
            json.dump(logging_config, f, indent=2)
        print("   ✅ config/logging.json")
    except Exception as e:
        print(f"   ❌ Error creando logging.json: {e}")
    
    # Configuración de Alegra
    alegra_config = {
        "endpoints": {
            "invoices": "/api/v1/invoices",
            "bills": "/api/v1/bills",
            "contacts": "/api/v1/contacts",
            "items": "/api/v1/items",
            "accounts": "/api/v1/accounts",
            "reports": {
                "general_ledger": "/api/v1/reports/general-ledger",
                "trial_balance": "/api/v1/reports/trial-balance",
                "journal": "/api/v1/reports/journal"
            }
        },
        "timeouts": {
            "default": 30,
            "reports": 60
        },
        "retry_attempts": 3
    }
    
    try:
        with open('config/alegra.json', 'w') as f:
            json.dump(alegra_config, f, indent=2)
        print("   ✅ config/alegra.json")
    except Exception as e:
        print(f"   ❌ Error creando alegra.json: {e}")

def run_validation():
    """Ejecutar validación de configuración"""
    print("🔍 Ejecutando validación de configuración...")
    
    try:
        result = subprocess.run([sys.executable, 'config_validator.py', '--report'], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Validación completada")
        else:
            print("⚠️ Validación completada con advertencias")
            print(result.stdout)
    except Exception as e:
        print(f"❌ Error ejecutando validación: {e}")

def create_startup_scripts():
    """Crear scripts de inicio"""
    print("🚀 Creando scripts de inicio...")
    
    # Script para Windows
    windows_script = """@echo off
echo Iniciando InvoiceBot...
python invoice_watcher.py facturas
pause
"""
    
    try:
        with open('start_invoicebot.bat', 'w') as f:
            f.write(windows_script)
        print("   ✅ start_invoicebot.bat")
    except Exception as e:
        print(f"   ❌ Error creando script Windows: {e}")
    
    # Script para Unix/Linux/Mac
    unix_script = """#!/bin/bash
echo "Iniciando InvoiceBot..."
python3 invoice_watcher.py facturas
"""
    
    try:
        with open('start_invoicebot.sh', 'w') as f:
            f.write(unix_script)
        
        # Hacer ejecutable
        os.chmod('start_invoicebot.sh', 0o755)
        print("   ✅ start_invoicebot.sh")
    except Exception as e:
        print(f"   ❌ Error creando script Unix: {e}")

def print_next_steps():
    """Mostrar próximos pasos"""
    print("""
🎉 ¡Instalación completada!

📋 PRÓXIMOS PASOS:

1. 🔐 Configurar credenciales de Alegra:
   - Edita el archivo .env
   - Añade tu email y token de Alegra

2. 🧪 Probar la instalación:
   python config_validator.py --report

3. 📄 Procesar una factura de prueba:
   python invoice_processor_enhanced.py process /ruta/a/tu/factura.pdf

4. 🤖 Iniciar monitoreo automático:
   python invoice_watcher.py facturas

5. 📊 Generar reportes:
   python invoice_processor_enhanced.py report --start-date 2024-01-01 --end-date 2024-01-31

📚 Para más información, consulta el README.md

¡Disfruta usando InvoiceBot! 🚀
""")

def main():
    """Función principal de instalación"""
    print_banner()
    
    # Verificar Python
    if not check_python_version():
        sys.exit(1)
    
    # Crear directorios
    create_directories()
    
    # Instalar dependencias
    if not install_dependencies():
        print("❌ Instalación falló en dependencias")
        sys.exit(1)
    
    # Crear archivos de configuración
    create_env_file()
    create_sample_config()
    
    # Crear scripts de inicio
    create_startup_scripts()
    
    # Ejecutar validación
    run_validation()
    
    # Mostrar próximos pasos
    print_next_steps()

if __name__ == "__main__":
    main()