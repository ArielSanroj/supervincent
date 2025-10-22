#!/bin/bash
# InvoiceBot v2.0 - Script de setup para desarrollo

set -e

echo "🚀 InvoiceBot v2.0 - Setup de Desarrollo"
echo "========================================"

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Función para logging
log() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Verificar Python
log "Verificando Python..."
if ! command -v python3 &> /dev/null; then
    error "Python 3 no está instalado"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
log "Python version: $PYTHON_VERSION"

# Verificar pip
log "Verificando pip..."
if ! command -v pip3 &> /dev/null; then
    error "pip3 no está instalado"
    exit 1
fi

# Crear ambiente virtual
log "Creando ambiente virtual..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    log "Ambiente virtual creado"
else
    log "Ambiente virtual ya existe"
fi

# Activar ambiente virtual
log "Activando ambiente virtual..."
source venv/bin/activate

# Actualizar pip
log "Actualizando pip..."
pip install --upgrade pip

# Instalar dependencias
log "Instalando dependencias..."
pip install -r requirements_updated.txt

# Instalar dependencias de desarrollo
log "Instalando dependencias de desarrollo..."
pip install pytest pytest-cov pytest-mock hypothesis
pip install black flake8 mypy pre-commit
pip install bandit safety

# Configurar pre-commit hooks
log "Configurando pre-commit hooks..."
pre-commit install

# Crear directorios necesarios
log "Creando directorios necesarios..."
mkdir -p logs reports backup cache tests/unit tests/integration tests/e2e

# Crear archivo .env si no existe
if [ ! -f ".env" ]; then
    log "Creando archivo .env..."
    cp .env.example .env
    warn "Archivo .env creado. Edita con tus credenciales de Alegra"
else
    log "Archivo .env ya existe"
fi

# Crear archivo de configuración si no existe
if [ ! -f "config/settings.json" ]; then
    log "Creando configuración por defecto..."
    mkdir -p config
    cat > config/settings.json << EOF
{
  "version": "2.0.0",
  "alegra": {
    "base_url": "https://api.alegra.com/api/v1",
    "timeout": 30,
    "max_retries": 3,
    "rate_limit_delay": 1.0
  },
  "nanobot": {
    "enabled": false,
    "host": "http://localhost:8080",
    "confidence_threshold": 0.75
  },
  "security": {
    "encrypt_credentials": true,
    "max_file_size_mb": 50,
    "rate_limit_per_minute": 60
  },
  "cache": {
    "enabled": true,
    "ttl_seconds": 3600,
    "redis_url": "redis://localhost:6379/0"
  }
}
EOF
    log "Configuración creada"
fi

# Verificar instalación
log "Verificando instalación..."
python -c "import src.core; print('✅ Core modules OK')"
python -c "import src.utils; print('✅ Utils modules OK')"
python -c "import src.integrations; print('✅ Integrations modules OK')"

# Ejecutar tests básicos
log "Ejecutando tests básicos..."
python -m pytest tests/unit/ -v --tb=short || warn "Algunos tests fallaron (normal en setup inicial)"

# Verificar herramientas de desarrollo
log "Verificando herramientas de desarrollo..."
black --version
flake8 --version
mypy --version
pytest --version

log "🎉 Setup de desarrollo completado!"
echo ""
echo "📝 Próximos pasos:"
echo "1. Edita .env con tus credenciales de Alegra"
echo "2. Ejecuta: make test"
echo "3. Ejecuta: make run"
echo ""
echo "🔧 Comandos útiles:"
echo "  make help          - Ver todos los comandos"
echo "  make test          - Ejecutar tests"
echo "  make lint          - Ejecutar linting"
echo "  make format        - Formatear código"
echo "  make run           - Ejecutar InvoiceBot"
echo ""
echo "📚 Documentación:"
echo "  README_NEW.md      - Guía principal"
echo "  docs/ARCHITECTURE.md - Arquitectura del sistema"
echo ""

