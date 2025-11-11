# Guía de Deploy - SuperBincent Frontend

## Configuración para Producción

### 1. Variables de Entorno

Crea un archivo `.env.local` o `.env.production` con:

```bash
# URL del backend (ngrok en producción)
NEXT_PUBLIC_API_URL=https://your-ngrok-url.ngrok.io

# URL del backend para API routes del servidor
BACKEND_API_URL=https://your-ngrok-url.ngrok.io
```

**Importante:** 
- `NEXT_PUBLIC_API_URL` es accesible desde el cliente (navegador)
- `BACKEND_API_URL` es solo para las API routes del servidor Next.js
- En producción, ambas deben apuntar a tu URL de ngrok

### 2. Probar Endpoints

Antes de hacer deploy, prueba todos los endpoints:

```bash
# Con backend local
npm run test:endpoints

# Con backend en ngrok
npm run test:endpoints https://your-ngrok-url.ngrok.io
```

### 3. Build para Producción

```bash
# Instalar dependencias
npm install

# Build
npm run build

# Verificar que el build fue exitoso
npm start
```

### 4. Deploy

#### Opción A: Vercel (Recomendado)

1. Instala Vercel CLI: `npm i -g vercel`
2. Ejecuta: `vercel`
3. Configura las variables de entorno en el dashboard de Vercel:
   - `NEXT_PUBLIC_API_URL`
   - `BACKEND_API_URL`

#### Opción B: Docker

```dockerfile
FROM node:18-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM node:18-alpine AS runner
WORKDIR /app
ENV NODE_ENV production
COPY --from=builder /app/public ./public
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static
EXPOSE 3000
CMD ["node", "server.js"]
```

#### Opción C: Servidor propio

```bash
# Build
npm run build

# Iniciar servidor de producción
npm start
```

## Endpoints Disponibles

### Frontend API Routes (Next.js)

- `GET /api/finance` - Dashboard financiero
- `GET /api/finance/recent` - Facturas recientes
- `GET /api/finance/withholdings` - Retenciones
- `POST /api/finance/bulk-upload` - Carga masiva
- `GET /api/reports/general-ledger` - Libro mayor
- `GET /api/reports/trial-balance` - Balance de prueba
- `GET /api/reports/aging` - Reporte de antigüedad
- `GET /api/tax/rules` - Reglas de impuestos

### Backend Endpoints (vía ngrok)

- `GET /processed/recent` - Facturas procesadas recientes
- `POST /process/upload` - Subir factura
- `POST /process` - Procesar factura por ruta
- `POST /process/manual` - Crear factura manual
- `POST /process/upload-multiple` - Carga masiva
- `POST /process/confirm-duplicate` - Confirmar duplicado
- `GET /cache/stats` - Estadísticas de cache
- `GET /reports/general-ledger` - Libro mayor
- `GET /reports/trial-balance` - Balance de prueba
- `GET /reports/aging` - Reporte de antigüedad
- `GET /tax/rules` - Reglas de impuestos

## Troubleshooting

### Error: "Cannot connect to backend"

1. Verifica que el backend esté corriendo
2. Verifica que la URL de ngrok sea correcta
3. Verifica que las variables de entorno estén configuradas
4. Verifica CORS en el backend

### Error: "API route not found"

1. Verifica que los archivos estén en `src/pages/api/`
2. Verifica que el build haya sido exitoso
3. Verifica los logs del servidor

### Error: "Environment variable not found"

1. Verifica que las variables estén en `.env.local` o `.env.production`
2. Reinicia el servidor después de cambiar variables de entorno
3. En Vercel, configura las variables en el dashboard

