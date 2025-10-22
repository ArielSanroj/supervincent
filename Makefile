# InvoiceBot v2.0 - Makefile

.PHONY: help install test lint format clean setup dev run docker-build docker-run

# Default target
help:
	@echo "InvoiceBot v2.0 - Comandos disponibles:"
	@echo ""
	@echo "Setup:"
	@echo "  setup          - Configurar ambiente de desarrollo"
	@echo "  install        - Instalar dependencias"
	@echo "  dev            - Setup completo para desarrollo"
	@echo ""
	@echo "Desarrollo:"
	@echo "  run            - Ejecutar InvoiceBot"
	@echo "  test           - Ejecutar tests"
	@echo "  lint           - Ejecutar linting"
	@echo "  format         - Formatear código"
	@echo "  clean          - Limpiar archivos temporales"
	@echo ""
	@echo "Docker:"
	@echo "  docker-build   - Construir imagen Docker"
	@echo "  docker-run     - Ejecutar contenedor"
	@echo "  docker-compose - Ejecutar con docker-compose"
	@echo ""
	@echo "Deploy:"
	@echo "  deploy-dev     - Deploy a desarrollo"
	@echo "  deploy-prod    - Deploy a producción"

# Setup
setup:
	@echo "🔧 Configurando ambiente de desarrollo..."
	python -m venv venv
	@echo "✅ Ambiente virtual creado"
	@echo "📦 Instalando dependencias..."
	pip install -r requirements_updated.txt
	@echo "✅ Dependencias instaladas"
	@echo "🔧 Configurando pre-commit hooks..."
	pre-commit install
	@echo "✅ Pre-commit hooks configurados"
	@echo "📁 Creando directorios necesarios..."
	mkdir -p logs reports backup cache
	@echo "✅ Directorios creados"
	@echo "📝 Copiando archivo de configuración..."
	cp .env.example .env
	@echo "✅ Archivo .env creado"
	@echo "🎉 Setup completado! Edita .env con tus credenciales"

install:
	@echo "📦 Instalando dependencias..."
	pip install -r requirements_updated.txt
	@echo "✅ Dependencias instaladas"

dev: setup
	@echo "🚀 Configurando ambiente de desarrollo completo..."
	@echo "📊 Ejecutando tests iniciales..."
	pytest tests/unit/ -v
	@echo "✅ Tests unitarios pasaron"
	@echo "🎉 Ambiente de desarrollo listo!"

# Desarrollo
run:
	@echo "🚀 Ejecutando InvoiceBot..."
	python invoicebot.py --help

test:
	@echo "🧪 Ejecutando tests..."
	pytest tests/ -v --cov=src --cov-report=html --cov-report=term
	@echo "✅ Tests completados"

test-unit:
	@echo "🧪 Ejecutando tests unitarios..."
	pytest tests/unit/ -v
	@echo "✅ Tests unitarios completados"

test-integration:
	@echo "🧪 Ejecutando tests de integración..."
	pytest tests/integration/ -v
	@echo "✅ Tests de integración completados"

test-e2e:
	@echo "🧪 Ejecutando tests E2E..."
	pytest tests/e2e/ -v
	@echo "✅ Tests E2E completados"

lint:
	@echo "🔍 Ejecutando linting..."
	flake8 src/ tests/
	mypy src/
	@echo "✅ Linting completado"

format:
	@echo "🎨 Formateando código..."
	black src/ tests/
	@echo "✅ Código formateado"

format-check:
	@echo "🔍 Verificando formato..."
	black --check src/ tests/
	@echo "✅ Formato verificado"

# Limpieza
clean:
	@echo "🧹 Limpiando archivos temporales..."
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf .pytest_cache/
	rm -rf .coverage
	rm -rf htmlcov/
	rm -rf .mypy_cache/
	@echo "✅ Limpieza completada"

clean-logs:
	@echo "🧹 Limpiando logs..."
	rm -rf logs/*.log
	rm -rf logs/*.json
	@echo "✅ Logs limpiados"

# Docker
docker-build:
	@echo "🐳 Construyendo imagen Docker..."
	docker build -t invoicebot:2.0 .
	@echo "✅ Imagen construida"

docker-run:
	@echo "🐳 Ejecutando contenedor..."
	docker run -it --rm \
		-e ALEGRA_USER=$$ALEGRA_USER \
		-e ALEGRA_TOKEN=$$ALEGRA_TOKEN \
		-v $$(pwd)/facturas:/app/facturas \
		invoicebot:2.0

docker-compose:
	@echo "🐳 Ejecutando con docker-compose..."
	docker-compose up -d
	@echo "✅ Servicios iniciados"

docker-compose-down:
	@echo "🐳 Deteniendo servicios..."
	docker-compose down
	@echo "✅ Servicios detenidos"

# Deploy
deploy-dev:
	@echo "🚀 Deploy a desarrollo..."
	@echo "📝 Verificando configuración..."
	@test -f .env || (echo "❌ Archivo .env no encontrado" && exit 1)
	@echo "✅ Configuración verificada"
	@echo "🧪 Ejecutando tests..."
	pytest tests/unit/ -v
	@echo "✅ Tests pasaron"
	@echo "🐳 Construyendo imagen..."
	docker build -t invoicebot:dev .
	@echo "✅ Deploy a desarrollo completado"

deploy-prod:
	@echo "🚀 Deploy a producción..."
	@echo "📝 Verificando configuración..."
	@test -f .env || (echo "❌ Archivo .env no encontrado" && exit 1)
	@echo "✅ Configuración verificada"
	@echo "🧪 Ejecutando tests completos..."
	pytest tests/ -v
	@echo "✅ Tests pasaron"
	@echo "🔍 Ejecutando linting..."
	flake8 src/ tests/
	mypy src/
	@echo "✅ Linting pasó"
	@echo "🐳 Construyendo imagen de producción..."
	docker build -t invoicebot:prod .
	@echo "✅ Deploy a producción completado"

# Monitoreo
logs:
	@echo "📊 Mostrando logs..."
	tail -f logs/invoicebot.log

logs-json:
	@echo "📊 Mostrando logs JSON..."
	tail -f logs/invoicebot.json | jq .

status:
	@echo "📊 Estado del sistema..."
	@echo "🐍 Python: $$(python --version)"
	@echo "📦 Pip: $$(pip --version)"
	@echo "🧪 Pytest: $$(pytest --version)"
	@echo "🎨 Black: $$(black --version)"
	@echo "🔍 Flake8: $$(flake8 --version)"
	@echo "🔧 MyPy: $$(mypy --version)"
	@echo "📁 Archivos: $$(find src/ -name '*.py' | wc -l) archivos Python"
	@echo "🧪 Tests: $$(find tests/ -name '*.py' | wc -l) archivos de test"

# Backup
backup:
	@echo "💾 Creando backup..."
	tar -czf backup_$$(date +%Y%m%d_%H%M%S).tar.gz \
		--exclude=venv \
		--exclude=__pycache__ \
		--exclude=.git \
		.
	@echo "✅ Backup creado"

# Help específico
help-setup:
	@echo "🔧 Setup detallado:"
	@echo "1. make setup          - Configuración básica"
	@echo "2. Editar .env         - Configurar credenciales"
	@echo "3. make test           - Verificar instalación"
	@echo "4. make run            - Ejecutar InvoiceBot"

help-docker:
	@echo "🐳 Docker detallado:"
	@echo "1. make docker-build   - Construir imagen"
	@echo "2. make docker-run     - Ejecutar contenedor"
	@echo "3. make docker-compose - Servicios completos"

help-deploy:
	@echo "🚀 Deploy detallado:"
	@echo "1. make deploy-dev     - Deploy a desarrollo"
	@echo "2. make deploy-prod    - Deploy a producción"
	@echo "3. make status          - Verificar estado"

