# ✅ Checklist de Deploy en Vercel

## ✅ Configuración Completada

- [x] `vercel.json` creado
- [x] `next.config.js` optimizado para Vercel
- [x] Variables de entorno configuradas
- [x] URLs hardcodeadas removidas
- [x] Almacenamiento de contactos adaptado para Vercel
- [x] `.gitignore` actualizado
- [x] Script de deploy creado

## 🚀 Deploy Rápido

### 1. Backend (Puerto 8010)

```bash
# En el servidor donde corre el backend
cd /Users/arielsanroj/supervincent
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
uvicorn src.api.app:app --host 0.0.0.0 --port 8010
```

### 2. Ngrok

```bash
# En otra terminal del mismo servidor
ngrok http 8010
```

**Copia la URL** (ejemplo: `https://abc123.ngrok-free.dev`)

### 3. Deploy Frontend

```bash
cd frontend

# Opción A: Script automático
./deploy.sh https://tu-ngrok-url.ngrok-free.dev

# Opción B: Manual
npm install
npm run build
vercel --prod
```

### 4. Variables de Entorno en Vercel

1. Ve a: https://vercel.com/dashboard
2. Tu proyecto → Settings → Environment Variables
3. Agrega:

```
NEXT_PUBLIC_API_URL = https://tu-ngrok-url.ngrok-free.dev
BACKEND_API_URL = https://tu-ngrok-url.ngrok-free.dev
```

4. Marca para: **Production**, **Preview**, **Development**
5. **Redeploy**

## 📋 Estructura

```
Backend (Servidor)          Frontend (Vercel)
     │                            │
     │─── Puerto 8010 ────────────┼─── Conecta vía ngrok
     │                            │
  ngrok ──► https://xxx.ngrok.io  │
```

## 🔧 Configuración del Backend

**Puerto único:** `8010`

El backend debe estar configurado para escuchar en:
- Host: `0.0.0.0` (todas las interfaces)
- Puerto: `8010`

## ⚠️ Notas Importantes

1. **Ngrok Free:** La URL cambia al reiniciar. Para producción, considera:
   - Ngrok con dominio fijo (plan pago)
   - O mantener ngrok corriendo siempre

2. **CORS:** Asegúrate de que el backend permita requests desde:
   - `https://tu-proyecto.vercel.app`
   - `https://*.vercel.app` (preview deployments)

3. **Contactos:** En Vercel, los contactos se guardan en `/tmp` (temporal).
   Para producción, considera usar:
   - Vercel KV (Redis)
   - Upstash
   - PostgreSQL (Vercel Postgres)
   - MongoDB Atlas

## 🧪 Verificar Deploy

1. ✅ Landing page carga: `https://tu-proyecto.vercel.app/landing`
2. ✅ Dashboard funciona: `https://tu-proyecto.vercel.app`
3. ✅ API routes responden: `https://tu-proyecto.vercel.app/api/finance`
4. ✅ Formulario de contacto guarda datos

## 📞 Soporte

Si hay problemas:
1. Revisa los logs en Vercel Dashboard → Deployments
2. Verifica que las variables de entorno estén configuradas
3. Verifica que ngrok esté corriendo y accesible
4. Revisa CORS en el backend

