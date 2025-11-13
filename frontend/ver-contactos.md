# 📋 Ver Datos del Formulario "Contáctame"

## Ubicación de los datos

Los datos del formulario "Contáctame" se almacenan en **2 lugares**:

### 1. Archivo JSON (Principal)
**Ubicación:** `/frontend/data/contacts.json`

Este es el método principal de almacenamiento. Cada vez que alguien envía el formulario, los datos se guardan aquí.

**Para ver los datos:**
```bash
cat frontend/data/contacts.json
```

**O desde el navegador:**
- Abre: `http://localhost:3001/api/contact` (GET)
- Verás todos los contactos almacenados

### 2. LocalStorage (Fallback)
Si el backend falla, los datos se guardan en `localStorage` del navegador.

**Para ver en el navegador:**
1. Abre las DevTools (F12)
2. Ve a la pestaña "Application" o "Almacenamiento"
3. Busca "Local Storage" → `http://localhost:3001`
4. Busca la clave `contacts`
5. O ejecuta en la consola:
```javascript
JSON.parse(localStorage.getItem('contacts') || '[]')
```

## Estructura de los datos

Cada contacto tiene esta estructura:
```json
{
  "nombre": "Juan Pérez",
  "telefono": "3001234567",
  "correo": "juan@example.com",
  "timestamp": "2025-01-13T10:30:00.000Z"
}
```

## Ver contactos vía API

**Endpoint GET:** `/api/contact`

**Ejemplo:**
```bash
curl http://localhost:3001/api/contact
```

**Respuesta:**
```json
{
  "success": true,
  "count": 2,
  "data": [
    {
      "nombre": "Juan Pérez",
      "telefono": "3001234567",
      "correo": "juan@example.com",
      "timestamp": "2025-01-13T10:30:00.000Z"
    }
  ]
}
```

## Próximos pasos recomendados

1. **Base de datos:** Migrar a PostgreSQL o MongoDB
2. **Email:** Configurar notificaciones por email
3. **CRM:** Integrar con HubSpot, Salesforce, etc.
4. **Validación:** Añadir validación más robusta

