# 🚀 Guía Rápida de Deploy

## Pre-Deploy Checklist

✅ **Endpoints corregidos:**
- URLs hardcodeadas reemplazadas por variables de entorno
- Endpoints faltantes creados (`/api/reports/*`, `/api/tax/*`)
- Variables de entorno configuradas correctamente

✅ **Script de prueba creado:**
```bash
npm run test:endpoints [backend_url]
```

## Pasos para Deploy

### 1. Configurar Variables de Entorno

Crea `.env.production` o configura en tu plataforma de deploy:

```bash
NEXT_PUBLIC_API_URL=https://tu-ngrok-url.ngrok.io
BACKEND_API_URL=https://tu-ngrok-url.ngrok.io
```

### 2. Probar Endpoints

```bash
# Con backend local
npm run test:endpoints

# Con backend en ngrok
npm run test:endpoints https://tu-ngrok-url.ngrok.io
```

### 3. Build

```bash
npm run build
```

### 4. Deploy

**Vercel (Recomendado):**
```bash
npm i -g vercel
vercel
```

**Otra plataforma:**
- Sigue las instrucciones en `DEPLOY.md`

## Endpoints Implementados

### Frontend API Routes
- ✅ `/api/finance` - Dashboard
- ✅ `/api/finance/recent` - Facturas recientes
- ✅ `/api/finance/withholdings` - Retenciones
- ✅ `/api/finance/bulk-upload` - Carga masiva
- ✅ `/api/reports/general-ledger` - Libro mayor
- ✅ `/api/reports/trial-balance` - Balance de prueba
- ✅ `/api/reports/aging` - Reporte antigüedad
- ✅ `/api/tax/rules` - Reglas de impuestos

### Backend Endpoints (vía ngrok)
- ✅ `/processed/recent`
- ✅ `/process/upload`
- ✅ `/process`
- ✅ `/process/manual`
- ✅ `/process/upload-multiple`
- ✅ `/cache/stats`
- ✅ `/reports/*`
- ✅ `/tax/rules`

## Notas Importantes

1. **Backend en ngrok:** El backend debe estar corriendo y accesible vía ngrok
2. **CORS:** Asegúrate de que el backend permita requests desde tu dominio de producción
3. **Variables de entorno:** `NEXT_PUBLIC_*` son públicas, `BACKEND_API_URL` es solo servidor

