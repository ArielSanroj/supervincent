# 🔗 Explicación de URLs en Vercel

## ¿Por qué hay URLs diferentes?

Vercel genera **3 tipos de URLs** para cada proyecto:

### 1. **URL de Producción (Principal)** ⭐
```
https://supervincent-git-main-arielsanrojs-projects.vercel.app
```
- ✅ Esta es la URL **principal** de producción
- ✅ Se actualiza automáticamente con cada push a `main`
- ✅ Es la URL que debes usar para compartir tu app
- ✅ Funciona para todas las rutas: `/`, `/app`, `/landing`, etc.

### 2. **URL de Preview (Temporal)**
```
https://supervincent-dzkh010cj-arielsanrojs-projects.vercel.app
```
- ⚠️ Esta es una URL de **preview** para un deployment específico
- ⚠️ Tiene un hash único (`dzkh010cj`) que identifica ese deployment
- ⚠️ Se genera para cada push, pull request, o deployment manual
- ⚠️ Es temporal y puede cambiar

### 3. **URL de Dominio Personalizado** (si lo configuras)
```
https://supervincent.vercel.app
```
- ✅ URL más corta y profesional
- ✅ Necesitas configurarla en Vercel Dashboard

---

## 🎯 Solución: Usa la URL Principal

**Para todo, usa esta URL:**
```
https://supervincent-git-main-arielsanrojs-projects.vercel.app
```

### Rutas disponibles:
- **Landing:** `https://supervincent-git-main-arielsanrojs-projects.vercel.app/landing`
- **App (Dashboard):** `https://supervincent-git-main-arielsanrojs-projects.vercel.app/app`
- **Raíz (redirige a /app):** `https://supervincent-git-main-arielsanrojs-projects.vercel.app/`
- **Ver Contactos:** `https://supervincent-git-main-arielsanrojs-projects.vercel.app/ver-contactos`

---

## 🔧 Cómo Encontrar tu URL Principal

1. Ve a **Vercel Dashboard**: https://vercel.com/dashboard
2. Selecciona tu proyecto: **supervincent**
3. Ve a la pestaña **"Deployments"**
4. Busca el deployment marcado como **"Production"** (con el badge verde)
5. Haz clic en el deployment
6. Copia la URL que aparece en la parte superior

**O simplemente:**
- La URL principal siempre tiene el formato: `https://[proyecto]-git-main-[usuario]-projects.vercel.app`

---

## 🌐 Configurar Dominio Personalizado (Opcional)

Si quieres una URL más corta:

1. Ve a **Vercel Dashboard** → Tu proyecto → **Settings** → **Domains**
2. Agrega un dominio personalizado:
   - `supervincent.vercel.app` (gratis, subdominio de Vercel)
   - O tu propio dominio: `supervincent.com`
3. Sigue las instrucciones para verificar el dominio
4. Una vez configurado, todas las rutas funcionarán con el nuevo dominio

---

## 📝 Resumen

| Tipo de URL | Cuándo Usarla | Ejemplo |
|------------|---------------|---------|
| **Producción** | ✅ Para compartir, producción | `supervincent-git-main-...vercel.app` |
| **Preview** | ⚠️ Solo para testing temporal | `supervincent-dzkh010cj-...vercel.app` |
| **Personalizado** | ✅ Si lo configuraste | `supervincent.vercel.app` |

---

## ✅ Recomendación

**Usa siempre la URL de producción:**
```
https://supervincent-git-main-arielsanrojs-projects.vercel.app
```

Esta URL funciona para:
- ✅ `/` → Redirige a `/app`
- ✅ `/app` → Dashboard de finanzas
- ✅ `/landing` → Landing page
- ✅ `/ver-contactos` → Ver contactos guardados
- ✅ Todas las demás rutas

**No uses las URLs de preview** (las que tienen hash único) porque son temporales y pueden desaparecer.

