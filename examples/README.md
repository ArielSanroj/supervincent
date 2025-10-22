# Ejemplos y Demos - InvoiceBot v2.0

## 📁 Contenido

Este directorio contiene ejemplos y demos de la versión anterior (v1.x) que han sido movidos aquí para referencia.

## 🎯 Ejemplos Disponibles

### Demos de Funcionalidad
- `demo_both_files.py` - Demo de procesamiento de ambos archivos
- `demo_superbincent_integrated.py` - Demo de integración SuperBincent
- `demo_tax_system.py` - Demo del sistema de impuestos
- `demo_token_alegra.py` - Demo de token de Alegra
- `demo_user_interface.py` - Demo de interfaz de usuario

### Ejemplos de Uso
- `example_usage.py` - Ejemplo básico de uso

## 🚀 Nuevos Ejemplos (v2.0)

### Procesamiento Básico
```python
from src.core import InvoiceProcessor

# Inicializar procesador
processor = InvoiceProcessor()

# Procesar factura PDF
result = processor.process_invoice_file('factura.pdf')
print(f"Tipo: {result['tipo']}")
print(f"Total: ${result['total']:,.2f}")
```

### Procesamiento con Nanobot
```python
from src.core import InvoiceProcessor

# Procesador con clasificación ML
processor = InvoiceProcessor(use_nanobot=True)

# Procesar con clasificación inteligente
result = processor.process_invoice_file('factura.pdf')
```

### Configuración Personalizada
```python
from src.core import InvoiceProcessor
from src.utils import ConfigManager

# Configuración personalizada
config = ConfigManager('config/custom.json')
processor = InvoiceProcessor(config_path='config/custom.json')
```

### Procesamiento Asíncrono
```python
from src.tasks.celery_tasks import process_invoice_async

# Procesar de forma asíncrona
task = process_invoice_async.delay('factura.pdf')
result = task.get()  # Esperar resultado
```

## 📊 Comparación de Ejemplos

### v1.x (Archivos en examples/)
```python
# Demo básico
from demo_both_files import process_both_files
process_both_files()
```

### v2.0 (Nueva arquitectura)
```python
# Procesamiento consolidado
from src.core import InvoiceProcessor
processor = InvoiceProcessor()
result = processor.process_invoice_file('factura.pdf')
```

## 🔧 Migración de Ejemplos

### Antes
```python
# demo_both_files.py
def process_both_files():
    processor = InvoiceProcessorEnhanced()
    # ... código específico
```

### Después
```python
# Nuevo ejemplo
from src.core import InvoiceProcessor

def process_multiple_files():
    processor = InvoiceProcessor()
    files = ['factura1.pdf', 'factura2.jpg']
    results = []
    for file in files:
        result = processor.process_invoice_file(file)
        results.append(result)
    return results
```

## 📝 Notas de Desarrollo

### ¿Por qué se movieron?
1. **Organización**: Separar demos de código principal
2. **Referencia**: Mantener ejemplos de v1.x
3. **Migración**: Facilitar transición a v2.0
4. **Limpieza**: Código principal más limpio

### ¿Cómo usar los ejemplos?
1. **v1.x**: Ejecutar directamente (solo para referencia)
2. **v2.0**: Usar como guía para nueva implementación
3. **Migración**: Adaptar ejemplos a nueva arquitectura

## 🆘 Soporte

### ¿Necesitas ayuda con los ejemplos?
1. **Revisa** la documentación en `README_NEW.md`
2. **Consulta** `docs/ARCHITECTURE.md` para entender la nueva arquitectura
3. **Ejecuta** `python invoicebot.py --help` para ver comandos disponibles
4. **Usa** `make help` para ver comandos de desarrollo

### ¿Quieres contribuir ejemplos?
1. **Crea** ejemplos para v2.0 en `examples/v2/`
2. **Documenta** con comentarios claros
3. **Incluye** tests si es necesario
4. **Sigue** las convenciones de código

---

**Nota**: Los archivos en este directorio son de referencia histórica. Para nuevos desarrollos, usa la nueva arquitectura en `src/` y crea ejemplos en `examples/v2/`.

