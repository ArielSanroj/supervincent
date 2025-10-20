# 🚀 Subida Real de Facturas a Alegra

Este conjunto de scripts te permite subir **realmente** las facturas procesadas a tu cuenta de Alegra, no solo simular el proceso.

## 📋 Archivos Incluidos

- `real_alegra_upload.py` - Script principal para subir facturas a Alegra
- `setup_alegra_credentials.py` - Configurar credenciales de Alegra
- `verify_alegra_bills.py` - Verificar facturas creadas en Alegra
- `upload_to_alegra_complete.py` - Script maestro que ejecuta todo el proceso

## 🔧 Configuración Inicial

### 1. Obtener Credenciales de Alegra

1. Ve a [https://app.alegra.com/api](https://app.alegra.com/api)
2. Inicia sesión en tu cuenta de Alegra
3. Copia tu **token de API**

### 2. Configurar Credenciales

```bash
# Ejecutar el script de configuración
python setup_alegra_credentials.py
```

Esto te pedirá:
- 📧 Tu email de Alegra
- 🔑 Tu token de API

### 3. Cargar Variables de Entorno

```bash
# Cargar las credenciales
source load_alegra_env.sh
```

## 🚀 Uso

### Opción 1: Script Completo (Recomendado)

```bash
# Ejecutar todo el proceso automáticamente
python upload_to_alegra_complete.py
```

### Opción 2: Pasos Individuales

```bash
# 1. Configurar credenciales
python setup_alegra_credentials.py

# 2. Cargar variables de entorno
source load_alegra_env.sh

# 3. Probar conexión
python setup_alegra_credentials.py test

# 4. Subir facturas
python real_alegra_upload.py

# 5. Verificar facturas
python verify_alegra_bills.py
```

## 📄 Facturas Soportadas

- ✅ **testfactura1.pdf** - Procesamiento completo con PDF
- ⚠️ **testfactura2.jpg** - Requiere OCR real (Tesseract)

## 🔍 Verificación

Después de subir las facturas, puedes verificar que se crearon correctamente:

1. **En la interfaz web**: Ve a [https://app.alegra.com/bills](https://app.alegra.com/bills)
2. **Con el script**: `python verify_alegra_bills.py`

## 📊 Datos que se Extraen

### De testfactura1.pdf:
- 📅 Fecha: 10-10-2025
- 👤 Cliente: ARIEL ANDRES SANCHEZ
- 🆔 NIT: 52147745-1
- 💰 Total: $203,343.81
- 🧾 IVA: $0.00
- 📄 Número: 18764084252886

### De testfactura2.jpg (simulado):
- 📅 Fecha: 15-10-2025
- 👤 Cliente: EMPRESA EJEMPLO LTDA
- 🏢 Proveedor: TECNOLOGIA AVANZADA S.A.S
- 🆔 NIT: 900123456-1
- 💰 Total: $125,000.00
- 🧾 IVA: $23,750.00
- 📄 Número: FAC-2025-001234

## 🏗️ Estructura de Factura en Alegra

Las facturas se crean con la siguiente estructura:

```json
{
  "date": "2025-10-10",
  "dueDate": "2025-10-10",
  "client": {
    "id": "12345"
  },
  "items": [{
    "id": 1,
    "description": "Factura 18764084252886 - Proveedor",
    "quantity": 1,
    "price": 203343.81,
    "discount": 0,
    "tax": [{
      "id": 1,
      "amount": 0
    }]
  }],
  "total": 203343.81,
  "subtotal": 203343.81,
  "taxes": [{
    "id": 1,
    "amount": 0
  }],
  "notes": "Factura procesada automáticamente - Número: 18764084252886",
  "status": "open"
}
```

## 🔧 Configuración Avanzada

### Variables de Entorno

```bash
export ALEGRA_EMAIL="tu-email@ejemplo.com"
export ALEGRA_TOKEN="tu-token-de-alegra"
```

### Archivo .env

```env
# Credenciales de Alegra
ALEGRA_EMAIL=tu-email@ejemplo.com
ALEGRA_TOKEN=tu-token-de-alegra
```

## 🐛 Solución de Problemas

### Error: "Credenciales no encontradas"
```bash
# Cargar variables de entorno
source load_alegra_env.sh
```

### Error: "Error de conexión"
```bash
# Verificar credenciales
python setup_alegra_credentials.py test
```

### Error: "No se pudo crear contacto"
- Verifica que el cliente tenga un nombre válido
- Revisa que el NIT tenga el formato correcto

### Error: "No se pudo crear factura"
- Verifica que el total sea mayor a 0
- Revisa que el cliente exista en Alegra
- Verifica que los items tengan precios válidos

## 📱 Interfaz de Usuario

El script muestra una interfaz clara con:

- 🔌 Estado de conexión
- 📄 Datos extraídos
- 👤 Procesamiento de contactos
- 💾 Creación de facturas
- ✅ Verificación de resultados

## 🎯 Próximos Pasos

1. **Configura tus credenciales** de Alegra
2. **Ejecuta el script completo** para subir las facturas
3. **Verifica en Alegra** que las facturas se crearon
4. **Personaliza** el script para tus necesidades específicas

## 🔗 Enlaces Útiles

- [API de Alegra](https://app.alegra.com/api)
- [Documentación de Alegra](https://developer.alegra.com/)
- [Interfaz web de Alegra](https://app.alegra.com/bills)

---

**¡Ahora sí verás las facturas reales en tu cuenta de Alegra! 🎉**