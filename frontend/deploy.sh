#!/bin/bash

# Script de deploy rápido para Vercel
# Uso: ./deploy.sh [ngrok_url]

set -e

echo "🚀 Preparando deploy de SuperBincent en Vercel"
echo ""

# Verificar que estamos en el directorio correcto
if [ ! -f "package.json" ]; then
    echo "❌ Error: Debes ejecutar este script desde el directorio frontend/"
    exit 1
fi

# Obtener URL de ngrok
if [ -z "$1" ]; then
    echo "📋 No se proporcionó URL de ngrok"
    echo "💡 Uso: ./deploy.sh https://tu-backend.ngrok-free.dev"
    echo ""
    echo "🔍 Intentando obtener URL de ngrok automáticamente..."
    NGROK_URL=$(curl -s http://localhost:4040/api/tunnels 2>/dev/null | grep -o '"public_url":"[^"]*"' | head -1 | cut -d'"' -f4 || echo "")
    
    if [ -z "$NGROK_URL" ]; then
        echo "❌ No se pudo obtener la URL de ngrok automáticamente"
        echo "💡 Asegúrate de que ngrok esté corriendo: ngrok http 8010"
        echo "💡 Luego ejecuta: ./deploy.sh https://tu-backend.ngrok-free.dev"
        exit 1
    fi
    echo "✅ URL de ngrok detectada: $NGROK_URL"
else
    NGROK_URL=$1
    echo "✅ Usando URL de ngrok: $NGROK_URL"
fi

echo ""
echo "📦 Instalando dependencias..."
npm install

echo ""
echo "🔨 Ejecutando build..."
npm run build

if [ $? -ne 0 ]; then
    echo "❌ Error en el build. Revisa los errores arriba."
    exit 1
fi

echo ""
echo "✅ Build exitoso!"
echo ""
echo "📋 Próximos pasos:"
echo ""
echo "1. Deploy a Vercel:"
echo "   vercel --prod"
echo ""
echo "2. Configurar variables de entorno en Vercel Dashboard:"
echo "   NEXT_PUBLIC_API_URL = $NGROK_URL"
echo "   BACKEND_API_URL = $NGROK_URL"
echo ""
echo "3. Redeploy después de configurar las variables"
echo ""
echo "📖 Para más detalles, lee: DEPLOY-VERCEL.md"

