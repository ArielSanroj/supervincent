# 🚀 Deploy en Vercel - SuperBincent

## Prerequisitos

1. ✅ Cuenta en Vercel (gratis): https://vercel.com
2. ✅ Backend corriendo en puerto 8010
3. ✅ Ngrok instalado y configurado
4. ✅ Repositorio en GitHub/GitLab/Bitbucket

## Paso 1: Configurar Ngrok para el Backend

```bash
# En el servidor donde corre el backend (puerto 8010)
ngrok http 8010
```

**Copia la URL de ngrok** (ejemplo: `https://abc123.ngrok-free.dev`)

## Paso 2: Deploy en Vercel

### Opción A: Vía CLI (Recomendado)

```bash
# Instalar Vercel CLI
npm i -g vercel

# Desde el directorio frontend
cd frontend

# Login en Vercel
vercel login

# Deploy (primera vez)
vercel

# Deploy a producción
vercel --prod
```

### Opción B: Vía Dashboard de Vercel

1. Ve a https://vercel.com/new
2. Conecta tu repositorio de GitHub
3. Selecciona el proyecto
4. **Configuración del proyecto:**
   - **Framework Preset:** Next.js
   - **Root Directory:** `frontend`
   - **Build Command:** `npm run build`
   - **Output Directory:** `.next` (automático)

## Paso 3: Configurar Variables de Entorno

En el dashboard de Vercel:

1. Ve a tu proyecto → Settings → Environment Variables
2. Agrega las siguientes variables:

```
NEXT_PUBLIC_API_URL = https://tu-backend.ngrok-free.dev
BACKEND_API_URL = https://tu-backend.ngrok-free.dev
```

**Importante:**
- `NEXT_PUBLIC_API_URL` debe ser la URL de ngrok de tu backend
- Ambas variables deben tener el mismo valor
- Marca ambas para **Production**, **Preview** y **Development**

## Paso 4: Redeploy

Después de agregar las variables de entorno:

1. Ve a Deployments
2. Haz clic en los 3 puntos del último deployment
3. Selecciona "Redeploy"

## Paso 5: Verificar

1. Abre tu URL de Vercel (ejemplo: `https://superbincent.vercel.app`)
2. Verifica que la landing page carga correctamente
3. Prueba el formulario de contacto
4. Verifica que los endpoints funcionan

## Troubleshooting

### Error: "NEXT_PUBLIC_API_URL is not defined"

**Solución:** Asegúrate de configurar la variable en Vercel Dashboard y hacer redeploy.

### Error: "Cannot connect to backend"

**Solución:** 
1. Verifica que ngrok esté corriendo
2. Verifica que la URL en Vercel sea correcta (sin trailing slash)
3. Verifica CORS en el backend

### Error: "Build failed"

**Solución:**
1. Verifica que `npm run build` funcione localmente
2. Revisa los logs de build en Vercel
3. Asegúrate de que todas las dependencias estén en `package.json`

## Estructura del Proyecto

```
supervincent/
├── frontend/          # ← Deploy esto en Vercel
│   ├── src/
│   ├── public/
│   ├── package.json
│   ├── next.config.js
│   └── vercel.json
└── src/              # Backend (corre en servidor con ngrok)
    └── api/
```

## Backend en Ngrok

El backend debe estar corriendo en el puerto **8010** y expuesto vía ngrok:

```bash
# En el servidor del backend
cd /Users/arielsanroj/supervincent
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
uvicorn src.api.app:app --host 0.0.0.0 --port 8010

# En otra terminal
ngrok http 8010
```

## URLs Finales

- **Frontend (Vercel):** `https://tu-proyecto.vercel.app`
- **Backend (Ngrok):** `https://tu-backend.ngrok-free.dev`
- **Landing Page:** `https://tu-proyecto.vercel.app/landing`

## Notas Importantes

1. **Ngrok Free:** La URL cambia cada vez que reinicias ngrok. Considera usar ngrok con dominio fijo.
2. **Variables de Entorno:** Siempre usa `NEXT_PUBLIC_*` para variables accesibles en el cliente.
3. **CORS:** Asegúrate de que el backend permita requests desde tu dominio de Vercel.
4. **Contactos:** Los datos del formulario se guardan en `/frontend/data/contacts.json` (solo en desarrollo). En producción, considera usar una base de datos.

