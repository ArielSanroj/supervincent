# 🔧 Solución al Error 404 en Vercel

## Problema
Error `404: NOT_FOUND` al acceder a la aplicación en Vercel.

## Soluciones

### ✅ Solución 1: Configurar Root Directory en Vercel

1. Ve a tu proyecto en Vercel Dashboard
2. Settings → General
3. En **"Root Directory"**, configura: `frontend`
4. Guarda los cambios
5. Ve a Deployments y haz un **Redeploy**

### ✅ Solución 2: Verificar Framework Detection

Vercel debería detectar automáticamente Next.js, pero si no:

1. Settings → General
2. **Framework Preset:** Next.js
3. **Build Command:** `npm run build` (o dejar vacío para auto-detect)
4. **Output Directory:** `.next` (o dejar vacío)
5. **Install Command:** `npm install` (o dejar vacío)

### ✅ Solución 3: Verificar Variables de Entorno

Asegúrate de tener configuradas:

```
NEXT_PUBLIC_API_URL = https://tu-ngrok-url.ngrok-free.dev
BACKEND_API_URL = https://tu-ngrok-url.ngrok-free.dev
```

**Importante:** Marca ambas para **Production**, **Preview** y **Development**.

### ✅ Solución 4: Verificar que el Build Funciona

En el dashboard de Vercel:
1. Ve a la pestaña **"Deployments"**
2. Revisa los logs del último deployment
3. Si hay errores de build, corrígelos primero

### ✅ Solución 5: Limpiar y Re-deploy

Si nada funciona:

1. En Vercel Dashboard → Settings → General
2. Scroll hasta abajo → **"Delete Project"** (solo si es necesario)
3. O mejor: **"Redeploy"** desde Deployments
4. Selecciona el commit más reciente

## Verificación

Después de aplicar las soluciones:

1. ✅ La URL raíz (`https://tu-proyecto.vercel.app/`) debería redirigir a `/landing`
2. ✅ `/landing` debería mostrar la landing page completa
3. ✅ El formulario de contacto debería funcionar
4. ✅ Los endpoints `/api/*` deberían responder

## Notas Importantes

- **Root Directory:** Debe ser `frontend` (no el root del repo)
- **Build Command:** `npm run build` (se ejecuta desde `frontend/`)
- **Node Version:** Asegúrate de usar Node 18+ (configurado en `package.json`)

## Si el problema persiste

1. Revisa los logs de build en Vercel
2. Verifica que todos los archivos estén en el repositorio
3. Asegúrate de que `package.json` esté en `frontend/`
4. Verifica que `next.config.js` esté presente


