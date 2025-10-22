#!/usr/bin/env python3
"""
Script de despliegue para InvoiceBot
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path
from datetime import datetime

def print_banner():
    """Mostrar banner de despliegue"""
    print("""
╔══════════════════════════════════════════════════════════════╗
║                    InvoiceBot - Deploy                      ║
║              Script de Despliegue                           ║
╚══════════════════════════════════════════════════════════════╝
""")

def check_git():
    """Verificar si Git está disponible"""
    print("🔍 Verificando Git...")
    
    try:
        result = subprocess.run(['git', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"   ✅ Git disponible: {result.stdout.strip()}")
            return True
        else:
            print("   ❌ Git no disponible")
            return False
    except FileNotFoundError:
        print("   ❌ Git no encontrado en el sistema")
        return False

def initialize_git():
    """Inicializar repositorio Git"""
    print("📦 Inicializando repositorio Git...")
    
    try:
        # Inicializar git si no existe
        if not os.path.exists('.git'):
            subprocess.run(['git', 'init'], check=True)
            print("   ✅ Repositorio Git inicializado")
        
        # Crear .gitignore
        gitignore_content = """
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Environment
.env
.venv
env/
venv/
ENV/
env.bak/
venv.bak/

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
.DS_Store?
._*
.Spotlight-V100
.Trashes
ehthumbs.db
Thumbs.db

# Logs
*.log
logs/*.log

# Reports
reports/*.json
reports/*.txt

# Facturas procesadas
facturas/processed/
facturas/error/

# Backup
backup/*.json
backup/*.txt
"""
        
        with open('.gitignore', 'w') as f:
            f.write(gitignore_content)
        print("   ✅ .gitignore creado")
        
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"   ❌ Error inicializando Git: {e}")
        return False

def create_requirements_prod():
    """Crear requirements.txt para producción"""
    print("📦 Creando requirements para producción...")
    
    prod_requirements = """# InvoiceBot - Production Requirements
requests>=2.31.0
pdfplumber>=0.10.0
python-dotenv>=1.0.0
watchdog>=3.0.0
lxml>=4.9.0
alegra-python>=0.1.3

# Optional: For PDF generation in tests
reportlab>=4.0.0

# Optional: For web interface (future)
flask>=2.0.0
gunicorn>=20.0.0

# Optional: For database (future)
sqlalchemy>=1.4.0
"""
    
    try:
        with open('requirements-prod.txt', 'w') as f:
            f.write(prod_requirements)
        print("   ✅ requirements-prod.txt creado")
        return True
    except Exception as e:
        print(f"   ❌ Error creando requirements: {e}")
        return False

def create_docker_files():
    """Crear archivos Docker"""
    print("🐳 Creando archivos Docker...")
    
    # Dockerfile
    dockerfile_content = """FROM python:3.9-slim

WORKDIR /app

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \\
    gcc \\
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements
COPY requirements-prod.txt .

# Instalar dependencias Python
RUN pip install --no-cache-dir -r requirements-prod.txt

# Copiar código
COPY . .

# Crear directorios necesarios
RUN mkdir -p logs reports facturas/processed facturas/error backup config

# Variables de entorno
ENV PYTHONPATH=/app
ENV LOG_LEVEL=INFO

# Comando por defecto
CMD ["python", "invoice_watcher.py", "facturas"]
"""
    
    try:
        with open('Dockerfile', 'w') as f:
            f.write(dockerfile_content)
        print("   ✅ Dockerfile creado")
    except Exception as e:
        print(f"   ❌ Error creando Dockerfile: {e}")
    
    # docker-compose.yml
    docker_compose_content = """version: '3.8'

services:
  invoicebot:
    build: .
    container_name: invoicebot
    volumes:
      - ./facturas:/app/facturas
      - ./logs:/app/logs
      - ./reports:/app/reports
      - ./.env:/app/.env
    environment:
      - LOG_LEVEL=INFO
    restart: unless-stopped
    depends_on:
      - redis

  redis:
    image: redis:alpine
    container_name: invoicebot-redis
    restart: unless-stopped
"""
    
    try:
        with open('docker-compose.yml', 'w') as f:
            f.write(docker_compose_content)
        print("   ✅ docker-compose.yml creado")
    except Exception as e:
        print(f"   ❌ Error creando docker-compose.yml: {e}")

def create_systemd_service():
    """Crear servicio systemd"""
    print("🔧 Creando servicio systemd...")
    
    service_content = f"""[Unit]
Description=InvoiceBot - Sistema de procesamiento de facturas
After=network.target

[Service]
Type=simple
User={os.getenv('USER', 'invoicebot')}
WorkingDirectory={os.getcwd()}
ExecStart={sys.executable} invoice_watcher.py facturas
Restart=always
RestartSec=10
Environment=PYTHONPATH={os.getcwd()}

[Install]
WantedBy=multi-user.target
"""
    
    try:
        with open('invoicebot.service', 'w') as f:
            f.write(service_content)
        print("   ✅ invoicebot.service creado")
        print("   📝 Para instalar: sudo cp invoicebot.service /etc/systemd/system/")
        print("   📝 Para habilitar: sudo systemctl enable invoicebot")
        print("   📝 Para iniciar: sudo systemctl start invoicebot")
        return True
    except Exception as e:
        print(f"   ❌ Error creando servicio: {e}")
        return False

def create_cron_jobs():
    """Crear trabajos cron"""
    print("⏰ Creando trabajos cron...")
    
    cron_content = f"""# InvoiceBot - Trabajos programados
# Editar con: crontab -e

# Generar reportes diarios a las 6:00 AM
0 6 * * * cd {os.getcwd()} && {sys.executable} invoice_processor_enhanced.py report --start-date $(date -d yesterday +\%Y-\%m-\%d) --end-date $(date -d yesterday +\%Y-\%m-\%d) >> logs/cron.log 2>&1

# Limpiar logs antiguos (más de 30 días) semanalmente
0 2 * * 0 find {os.getcwd()}/logs -name "*.log" -mtime +30 -delete

# Backup de datos diario a las 11:00 PM
0 23 * * * cd {os.getcwd()} && tar -czf backup/invoicebot_backup_$(date +\%Y\%m\%d).tar.gz facturas/processed/ reports/ logs/ --exclude="*.tmp"
"""
    
    try:
        with open('crontab.txt', 'w') as f:
            f.write(cron_content)
        print("   ✅ crontab.txt creado")
        print("   📝 Para instalar: crontab crontab.txt")
        return True
    except Exception as e:
        print(f"   ❌ Error creando crontab: {e}")
        return False

def create_deployment_script():
    """Crear script de despliegue"""
    print("🚀 Creando script de despliegue...")
    
    deploy_script = """#!/bin/bash
# Script de despliegue para InvoiceBot

echo "🚀 Desplegando InvoiceBot..."

# Verificar Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 no encontrado"
    exit 1
fi

# Crear entorno virtual
if [ ! -d "venv" ]; then
    echo "📦 Creando entorno virtual..."
    python3 -m venv venv
fi

# Activar entorno virtual
echo "🔧 Activando entorno virtual..."
source venv/bin/activate

# Instalar dependencias
echo "📦 Instalando dependencias..."
pip install -r requirements-prod.txt

# Ejecutar pruebas
echo "🧪 Ejecutando pruebas..."
python test_system.py

# Configurar permisos
echo "🔒 Configurando permisos..."
chmod +x start_invoicebot.sh
chmod 600 .env

echo "✅ Despliegue completado!"
echo "🚀 Para iniciar: ./start_invoicebot.sh"
"""
    
    try:
        with open('deploy.sh', 'w') as f:
            f.write(deploy_script)
        
        os.chmod('deploy.sh', 0o755)
        print("   ✅ deploy.sh creado")
        return True
    except Exception as e:
        print(f"   ❌ Error creando script de despliegue: {e}")
        return False

def create_documentation():
    """Crear documentación adicional"""
    print("📚 Creando documentación...")
    
    # CHANGELOG.md
    changelog_content = """# Changelog

## [1.0.0] - 2024-01-10

### Added
- Detección automática de tipo de factura (compra/venta)
- Integración completa con API de Alegra
- Generación de reportes contables (ledger, balance de prueba, diario)
- Sistema de monitoreo automático de carpetas
- Validación de configuración y seguridad
- Soporte para libros auxiliares
- Sistema de logging completo
- Scripts de instalación y despliegue

### Features
- Procesamiento de facturas de compra (bills)
- Procesamiento de facturas de venta (invoices)
- Creación automática de contactos e items
- Backup local de todas las transacciones
- Cumplimiento con estándares NIIF
- Interfaz de línea de comandos intuitiva

### Security
- Manejo seguro de credenciales
- Validación de permisos de archivos
- Logging de auditoría
- Verificación de configuración
"""
    
    try:
        with open('CHANGELOG.md', 'w') as f:
            f.write(changelog_content)
        print("   ✅ CHANGELOG.md creado")
    except Exception as e:
        print(f"   ❌ Error creando CHANGELOG: {e}")
    
    # LICENSE
    license_content = """MIT License

Copyright (c) 2024 InvoiceBot

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""
    
    try:
        with open('LICENSE', 'w') as f:
            f.write(license_content)
        print("   ✅ LICENSE creado")
    except Exception as e:
        print(f"   ❌ Error creando LICENSE: {e}")

def main():
    """Función principal de despliegue"""
    print_banner()
    
    print("🚀 Preparando InvoiceBot para despliegue...")
    print("=" * 50)
    
    # Verificar Git
    if not check_git():
        print("⚠️ Git no disponible, saltando inicialización de repositorio")
    else:
        initialize_git()
    
    # Crear archivos de producción
    create_requirements_prod()
    create_docker_files()
    create_systemd_service()
    create_cron_jobs()
    create_deployment_script()
    create_documentation()
    
    print("\n✅ ¡Despliegue preparado!")
    print("=" * 50)
    
    print("""
📋 ARCHIVOS CREADOS:

🐳 Docker:
   - Dockerfile
   - docker-compose.yml

🔧 Sistema:
   - invoicebot.service (systemd)
   - crontab.txt
   - deploy.sh

📦 Producción:
   - requirements-prod.txt

📚 Documentación:
   - CHANGELOG.md
   - LICENSE

🚀 PRÓXIMOS PASOS:

1. Configurar credenciales en .env
2. Ejecutar: ./deploy.sh
3. O usar Docker: docker-compose up -d
4. O instalar servicio: sudo systemctl enable invoicebot

¡InvoiceBot está listo para producción! 🎉
""")

if __name__ == "__main__":
    main()