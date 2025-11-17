# 📋 Cómo Ver los Contactos Guardados

## Tu contacto actual:
- **Nombre:** ariel
- **Teléfono:** sanchez  
- **Correo:** ariel@gmail.com
- **Fecha:** 17 de noviembre de 2025, 17:48

---

## 🔍 Formas de Acceder a los Contactos

### 1. **Página Web (Más Fácil)** ⭐

Visita en tu navegador:
```
http://localhost:3000/ver-contactos
```

O si estás en producción:
```
https://tu-dominio.vercel.app/ver-contactos
```

Esta página muestra:
- ✅ Total de contactos
- ✅ Contactos del servidor
- ✅ Contactos en localStorage
- ✅ Tabla con todos los detalles

---

### 2. **Consola del Navegador (Rápido)**

1. Abre tu página web
2. Presiona **F12** (o clic derecho → Inspeccionar)
3. Ve a la pestaña **"Console"**
4. Copia y pega este código:

```javascript
// Ver todos los contactos
const contacts = JSON.parse(localStorage.getItem('contacts') || '[]');
console.table(contacts);

// O verlos uno por uno
contacts.forEach((c, i) => {
  console.log(`Contacto ${i+1}:`, c);
});
```

---

### 3. **DevTools - Application Tab**

1. Abre DevTools (F12)
2. Ve a la pestaña **"Application"** (Chrome) o **"Almacenamiento"** (Firefox)
3. Expande **"Local Storage"** → tu dominio
4. Busca la clave **`contacts`**
5. Haz clic para ver el valor JSON

---

### 4. **API Endpoint**

Visita en tu navegador:
```
http://localhost:3000/api/contact
```

Esto devuelve un JSON con los contactos guardados en el servidor.

---

## 📊 Comandos Útiles para la Consola

```javascript
// Ver todos los contactos
JSON.parse(localStorage.getItem('contacts') || '[]')

// Ver solo nombres
JSON.parse(localStorage.getItem('contacts') || '[]').map(c => c.nombre)

// Ver solo correos
JSON.parse(localStorage.getItem('contacts') || '[]').map(c => c.correo)

// Contar contactos
JSON.parse(localStorage.getItem('contacts') || '[]').length

// Ver el último contacto
const contacts = JSON.parse(localStorage.getItem('contacts') || '[]');
contacts[contacts.length - 1]

// Exportar como JSON (copiar)
JSON.stringify(JSON.parse(localStorage.getItem('contacts') || '[]'), null, 2)
```

---

## ⚠️ Nota Importante

Los contactos están guardados en **localStorage del navegador**, lo que significa:
- ✅ Se guardan automáticamente cuando alguien completa el formulario
- ✅ Persisten aunque cierres el navegador
- ⚠️ Solo están en **tu navegador actual**
- ⚠️ Si limpias el cache/localStorage, se pierden
- ⚠️ No se sincronizan entre dispositivos

**Para producción**, considera usar una base de datos real (PostgreSQL, MongoDB, etc.)

---

## 🔄 Sincronizar con el Servidor

Si quieres que los contactos se guarden permanentemente en el servidor, asegúrate de que:
1. El servidor esté corriendo
2. El endpoint `/api/contact` funcione correctamente
3. Los datos se guarden en `frontend/data/contacts.json` (desarrollo) o en una base de datos (producción)

