# Arquitectura InvoiceBot v2.0

## Visión General

InvoiceBot v2.0 implementa una arquitectura modular y escalable que consolida 11+ archivos duplicados en un sistema cohesivo. La arquitectura sigue principios SOLID y patrones de diseño enterprise.

## Principios de Diseño

### 1. Separación de Responsabilidades
- **Core**: Lógica de negocio principal
- **Integrations**: Servicios externos (Alegra, DIAN, Nanobot)
- **Utils**: Utilidades compartidas
- **Tasks**: Procesamiento asíncrono

### 2. Inversión de Dependencias
- Interfaces para servicios externos
- Inyección de dependencias
- Configuración externa

### 3. Principio Abierto/Cerrado
- Extensible para nuevos parsers
- Extensible para nuevas integraciones
- Configuración sin modificar código

## Componentes Principales

### Core Module (`src/core/`)

#### InvoiceProcessor
- **Responsabilidad**: Orquestar el procesamiento completo
- **Patrones**: Facade, Strategy
- **Dependencias**: Parsers, Validators, Integrations

```python
class InvoiceProcessor:
    def __init__(self, config, use_nanobot=False):
        self.config = ConfigManager(config)
        self.pdf_parser = PDFParser(self.config)
        self.image_parser = ImageParser(self.config)
        self.alegra_client = AlegraClient(...)
```

#### Parsers
- **PDFParser**: Múltiples estrategias de parsing
- **ImageParser**: OCR con preprocesamiento
- **Patrón**: Strategy para diferentes estrategias

#### Validators
- **InputValidator**: Sanitización y validación de entrada
- **TaxValidator**: Validación fiscal y enriquecimiento

### Integrations Module (`src/integrations/`)

#### AlegraClient
- **Connection Pooling**: Reutilización de conexiones
- **Circuit Breaker**: Recuperación de fallos
- **Rate Limiting**: Protección contra abuso
- **Caché**: Contactos e items

#### NanobotClient
- **Feature Flag**: Integración experimental
- **Fallback**: Clasificación legacy si falla
- **Triage**: Corrección de clasificaciones

### Utils Module (`src/utils/`)

#### ConfigManager
- **Schema Validation**: Validación de configuración
- **Environment Override**: Variables de entorno
- **Hot Reload**: Recarga sin reiniciar
- **Secrets Management**: Credenciales encriptadas

#### SecurityManager
- **Input Sanitization**: Limpieza de datos
- **Rate Limiting**: Control de velocidad
- **Audit Logging**: Registro de seguridad

#### StructuredLogger
- **JSON Logs**: Formato estructurado
- **Correlation IDs**: Tracking de requests
- **Performance Metrics**: Tiempos de procesamiento

## Patrones de Diseño Implementados

### 1. Factory Pattern
```python
def create_parser(file_type: str) -> Parser:
    if file_type == 'pdf':
        return PDFParser()
    elif file_type in ['jpg', 'png']:
        return ImageParser()
```

### 2. Strategy Pattern
```python
class PDFParser:
    def __init__(self):
        self.strategies = [
            self._parse_with_standard_patterns,
            self._parse_with_advanced_patterns,
            self._parse_with_fallback_patterns
        ]
```

### 3. Circuit Breaker Pattern
```python
class AlegraClient:
    def _check_circuit_breaker(self) -> bool:
        if self.circuit_state == CircuitState.OPEN:
            return False
        return True
```

### 4. Observer Pattern
```python
class InvoiceProcessor:
    def process_invoice(self, file_path: str):
        # Notificar inicio
        self.notify_observers('processing_started', file_path)
        # Procesar...
        # Notificar fin
        self.notify_observers('processing_completed', result)
```

## Flujo de Datos

### 1. Procesamiento de Factura
```
Archivo → InputValidator → Parser → TaxValidator → AlegraClient → Resultado
```

### 2. Clasificación con Nanobot
```
Texto → NanobotClient → Clasificación → Triage (si necesario) → Resultado
```

### 3. Creación en Alegra
```
Datos → AlegraClient → Contact/Item Cache → API Call → Circuit Breaker → Resultado
```

## Manejo de Errores

### Jerarquía de Excepciones
```
InvoiceBotError
├── ValidationError
├── ParsingError
├── IntegrationError
│   ├── AlegraAPIError
│   ├── DIANAPIError
│   └── NanobotAPIError
└── ConfigurationError
```

### Estrategias de Recuperación
1. **Retry con Exponential Backoff**
2. **Circuit Breaker**
3. **Fallback a valores por defecto**
4. **Cache de resultados**

## Configuración y Extensibilidad

### Configuración Jerárquica
1. **Archivo JSON**: `config/settings.json`
2. **Variables de entorno**: Override de configuración
3. **Argumentos CLI**: Override temporal

### Extension Points
- **Nuevos Parsers**: Implementar interfaz Parser
- **Nuevas Integraciones**: Implementar interfaz Integration
- **Nuevos Validators**: Implementar interfaz Validator

## Escalabilidad

### Horizontal
- **Celery Workers**: Procesamiento distribuido
- **Redis**: Cache compartido
- **Load Balancer**: Múltiples instancias

### Vertical
- **Connection Pooling**: Reutilización de recursos
- **Caché**: Reducción de llamadas a API
- **Lazy Loading**: Carga bajo demanda

## Monitoreo y Observabilidad

### Métricas
- **Prometheus**: Métricas de negocio y técnicos
- **Grafana**: Dashboards
- **Alerting**: Notificaciones automáticas

### Logging
- **Structured Logs**: JSON con metadatos
- **Correlation IDs**: Tracking de requests
- **Performance**: Tiempos de procesamiento

### Health Checks
- **Liveness**: ¿Está funcionando?
- **Readiness**: ¿Puede procesar requests?
- **Dependencies**: ¿APIs externas disponibles?

## Seguridad

### Input Validation
- **File Type Whitelist**: Solo PDF, JPG, PNG
- **Size Limits**: Máximo 50MB
- **Content Sanitization**: Limpieza de datos

### API Security
- **Rate Limiting**: 60 requests/minuto
- **Authentication**: Basic Auth con Alegra
- **Audit Logging**: Registro de operaciones

### Data Protection
- **Encryption**: Credenciales en memoria
- **Secrets Management**: Variables de entorno
- **Access Control**: Permisos de archivo

## Testing Strategy

### Unit Tests
- **Parsers**: Diferentes tipos de documentos
- **Validators**: Casos edge y maliciosos
- **Integrations**: Mocking de APIs

### Integration Tests
- **End-to-End**: Flujo completo
- **API Testing**: Alegra, DIAN, Nanobot
- **Database**: Cache y persistencia

### Performance Tests
- **Load Testing**: Múltiples facturas
- **Stress Testing**: Límites del sistema
- **Memory Testing**: Memory leaks

## Deployment

### Containerización
- **Multi-stage Build**: Optimización de imagen
- **Non-root User**: Seguridad
- **Health Checks**: Monitoreo

### Orchestration
- **Docker Compose**: Desarrollo
- **Kubernetes**: Producción
- **Service Mesh**: Comunicación

### CI/CD
- **GitHub Actions**: Automatización
- **Testing**: Automático en PR
- **Deployment**: Automático en main

## Migración desde v1.x

### Estrategia de Migración
1. **Coexistencia**: v1.x y v2.0 en paralelo
2. **Testing**: Validación exhaustiva
3. **Rollback**: Plan de contingencia
4. **Monitoring**: Métricas de migración

### Compatibilidad
- **CLI**: Mismo formato de comandos
- **API**: Misma funcionalidad
- **Configuración**: Migración automática
- **Datos**: Formato compatible

## Roadmap Técnico

### v2.1
- **API REST**: FastAPI con OpenAPI
- **WebSocket**: Progress updates
- **Dashboard**: Interfaz web

### v2.2
- **Machine Learning**: Modelos entrenados
- **Multi-tenant**: Aislamiento de datos
- **Cloud Native**: Kubernetes nativo

### v3.0
- **Microservices**: Arquitectura distribuida
- **Event Sourcing**: Auditoría completa
- **CQRS**: Separación de lecturas/escrituras

