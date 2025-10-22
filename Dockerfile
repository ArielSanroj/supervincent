# Dockerfile multi-stage optimizado para BetiBot
# Etapa 1: Builder para dependencias y compilación
FROM python:3.14-slim as builder

# Variables de entorno para Python
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Instalar dependencias del sistema necesarias para compilación
RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    g++ \
    libffi-dev \
    libssl-dev \
    libxml2-dev \
    libxslt1-dev \
    zlib1g-dev \
    libjpeg-dev \
    libpng-dev \
    libtiff-dev \
    libwebp-dev \
    libopenjp2-7-dev \
    libtesseract-dev \
    tesseract-ocr \
    tesseract-ocr-spa \
    && rm -rf /var/lib/apt/lists/*

# Crear directorio de trabajo
WORKDIR /app

# Copiar archivos de dependencias
COPY requirements.txt requirements_performance.txt ./

# Crear entorno virtual y instalar dependencias
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Instalar dependencias de Python
RUN pip install --upgrade pip && \
    pip install -r requirements.txt && \
    pip install -r requirements_performance.txt

# Etapa 2: Runtime optimizado
FROM python:3.14-slim as runtime

# Variables de entorno
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/opt/venv/bin:$PATH" \
    PYTHONPATH="/app/src"

# Instalar dependencias del sistema para runtime
RUN apt-get update && apt-get install -y \
    libxml2 \
    libxslt1.1 \
    libjpeg62-turbo \
    libpng16-16 \
    libtiff5 \
    libwebp6 \
    libopenjp2-7 \
    libtesseract4 \
    tesseract-ocr \
    tesseract-ocr-spa \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Crear usuario no-root para seguridad
RUN groupadd -r betibot && useradd -r -g betibot betibot

# Crear directorios necesarios
RUN mkdir -p /app /app/logs /app/reports /app/facturas/processed /app/facturas/error /app/facturas/high_amount \
    && chown -R betibot:betibot /app

# Copiar entorno virtual desde builder
COPY --from=builder /opt/venv /opt/venv

# Establecer directorio de trabajo
WORKDIR /app

# Copiar código de la aplicación
COPY --chown=betibot:betibot src/ ./src/
COPY --chown=betibot:betibot config/ ./config/
COPY --chown=betibot:betibot scripts/ ./scripts/
COPY --chown=betibot:betibot *.py ./
COPY --chown=betibot:betibot requirements*.txt ./
COPY --chown=betibot:betibot Makefile ./

# Crear archivos de configuración por defecto si no existen
RUN touch /app/.env && \
    chown betibot:betibot /app/.env

# Cambiar a usuario no-root
USER betibot

# Exponer puertos
EXPOSE 8000 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Comando por defecto
CMD ["python", "-m", "src.core.invoice_processor"]

