# Archivos Deprecados - InvoiceBot v1.x

## ⚠️ Advertencia

Los archivos en este directorio son de la versión anterior (v1.x) y han sido **deprecados** en favor de la nueva arquitectura consolidada en `src/`.

## 📁 Archivos Deprecados

### Procesadores de Facturas (11 archivos)
- `invoice_processor.py` → `src/core/invoice_processor.py`
- `invoice_processor_v2.py` → `src/core/invoice_processor.py`
- `invoice_processor_v3.py` → `src/core/invoice_processor.py`
- `invoice_processor_complete.py` → `src/core/invoice_processor.py`
- `invoice_processor_final.py` → `src/core/invoice_processor.py`
- `invoice_processor_fixed.py` → `src/core/invoice_processor.py`
- `invoice_processor_robust.py` → `src/core/invoice_processor.py`
- `invoice_processor_enhanced.py` → `src/core/invoice_processor.py`
- `invoice_processor_conversational.py` → `src/core/invoice_processor.py`
- `invoice_processor_with_taxes.py` → `src/core/invoice_processor.py`
- `invoice_processor_fixed_complete.py` → `src/core/invoice_processor.py`

## 🔄 Migración

### Antes (v1.x)
```python
from invoice_processor_enhanced import InvoiceProcessor
processor = InvoiceProcessor()
result = processor.process_invoice_file('factura.pdf')
```

### Después (v2.0)
```python
from src.core import InvoiceProcessor
processor = InvoiceProcessor()
result = processor.process_invoice_file('factura.pdf')
```

## 📊 Comparación de Funcionalidades

| Funcionalidad | v1.x | v2.0 | Mejora |
|---------------|------|------|--------|
| Procesadores | 11 archivos | 1 archivo | ✅ Consolidado |
| Type hints | Parcial | 100% | ✅ Completo |
| Error handling | Básico | Robusto | ✅ Mejorado |
| Security | Mínima | Enterprise | ✅ Hardening |
| Caching | No | Redis + LRU | ✅ Agregado |
| Monitoring | No | Prometheus | ✅ Agregado |
| Testing | Manual | Automatizado | ✅ CI/CD |

## 🚀 Beneficios de la Migración

### 1. Mantenibilidad
- **Un solo archivo** vs 11 archivos duplicados
- **Código limpio** con type hints completos
- **Documentación** integrada

### 2. Performance
- **Connection pooling** para APIs
- **Caché inteligente** con Redis
- **Lazy loading** de dependencias

### 3. Seguridad
- **Input validation** robusta
- **Rate limiting** automático
- **Audit logging** completo

### 4. Escalabilidad
- **Celery integration** para procesamiento asíncrono
- **Circuit breaker** para recuperación de fallos
- **Monitoring** con métricas

## 🔧 Compatibilidad

### CLI
```bash
# v1.x
python invoice_processor_enhanced.py process factura.pdf

# v2.0 (mismo comando)
python invoicebot.py process factura.pdf
```

### API
```python
# v1.x
from invoice_processor_enhanced import InvoiceProcessor

# v2.0 (misma interfaz)
from src.core import InvoiceProcessor
```

## 📅 Timeline de Deprecación

- **v2.0 (Actual)**: Archivos movidos a `deprecated/` con warnings
- **v2.1**: Warnings más agresivos
- **v2.2**: Archivos marcados como obsoletos
- **v3.0**: Archivos eliminados

## 🆘 Soporte

### ¿Necesitas ayuda con la migración?
1. **Revisa** `README_NEW.md` para la nueva documentación
2. **Consulta** `docs/ARCHITECTURE.md` para entender la nueva arquitectura
3. **Ejecuta** `make help` para ver comandos disponibles
4. **Usa** `python invoicebot.py --help` para la nueva CLI

### ¿Encontraste un bug?
- **Reporta** en el issue tracker
- **Incluye** logs de la nueva versión
- **Menciona** si es relacionado con migración

## 📝 Notas de Desarrollo

### ¿Por qué se deprecaron?
1. **Duplicación**: 11 archivos con funcionalidad similar
2. **Mantenimiento**: Difícil mantener consistencia
3. **Testing**: Tests dispersos y duplicados
4. **Performance**: Código no optimizado
5. **Security**: Vulnerabilidades no corregidas

### ¿Qué se conservó?
- **Toda la funcionalidad** de los archivos originales
- **Compatibilidad** de API y CLI
- **Configuración** existente
- **Datos** y resultados

### ¿Qué se mejoró?
- **Arquitectura** modular y escalable
- **Seguridad** enterprise-grade
- **Performance** optimizado
- **Testing** automatizado
- **Monitoring** integrado

---

**Nota**: Los archivos en este directorio se mantienen solo para referencia histórica y migración. Se recomienda usar la nueva arquitectura en `src/` para todos los desarrollos futuros.

