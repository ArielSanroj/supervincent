# ⚡ Deploy Rápido en Vercel

## Pasos Rápidos

### 1. Backend con Ngrok (en el servidor)

```bash
# Terminal 1: Iniciar backend en puerto 8010
cd /Users/arielsanroj/supervincent
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
uvicorn src.api.app:app --host 0.0.0.0 --port 8010

# Terminal 2: Iniciar ngrok
ngrok http 8010
```

**Copia la URL de ngrok** (ejemplo: `https://abc123.ngrok-free.dev`)

### 2. Deploy en Vercel

```bash
# Instalar Vercel CLI (si no lo tienes)
npm i -g vercel

# Desde el directorio frontend
cd frontend

# Login (solo primera vez)
vercel login

# Deploy
vercel --prod
```

### 3. Configurar Variables de Entorno

En https://vercel.com/dashboard:

1. Selecciona tu proyecto
2. Settings → Environment Variables
3. Agrega:

```
NEXT_PUBLIC_API_URL = https://tu-ngrok-url.ngrok-free.dev
BACKEND_API_URL = https://tu-ngrok-url.ngrok-free.dev
```

4. Marca para: Production, Preview, Development
5. Redeploy

### 4. Listo! 🎉

Tu app estará en: `https://tu-proyecto.vercel.app`

## Verificar

- ✅ Landing: `https://tu-proyecto.vercel.app/landing`
- ✅ Dashboard: `https://tu-proyecto.vercel.app`
- ✅ API funciona correctamente

## Notas

- **Ngrok:** La URL cambia al reiniciar. Considera ngrok con dominio fijo.
- **Backend:** Debe estar siempre corriendo en el puerto 8010.
- **CORS:** El backend debe permitir requests desde tu dominio de Vercel.

