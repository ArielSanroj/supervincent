# SuperVincent InvoiceBot Architecture

## Overview

SuperVincent InvoiceBot is an intelligent invoice processing system that automatically extracts data from invoices, calculates Colombian taxes, and integrates with the Alegra accounting system.

## System Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   File Input    │    │   API Layer     │    │   Web Interface │
│   (PDF/Images)  │    │   (FastAPI)     │    │   (Optional)    │
└─────────┬───────┘    └─────────┬───────┘    └─────────────────┘
          │                      │
          ▼                      ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Core Processing Layer                        │
├─────────────────┬─────────────────┬─────────────────────────────┤
│   Parser        │   Tax Service   │   Alegra Service            │
│   (OCR/PDF)     │   (Colombian)   │   (API Integration)         │
└─────────────────┴─────────────────┴─────────────────────────────┘
          │                      │                      │
          ▼                      ▼                      ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Data & Cache Layer                          │
├─────────────────┬─────────────────┬─────────────────────────────┤
│   Repository    │   Redis Cache   │   File Storage             │
│   (JSON/DB)     │   (Performance) │   (Backups)                │
└─────────────────┴─────────────────┴─────────────────────────────┘
```

## Component Details

### 1. API Layer (`src/api/`)

**FastAPI Application** (`app.py`)
- RESTful API endpoints
- Swagger/OpenAPI documentation
- Request validation and rate limiting
- CORS support for web clients

**Endpoints:**
- `POST /process` - Process single invoice
- `POST /process/batch` - Process multiple invoices
- `POST /process/directory` - Process directory of invoices
- `GET /health` - Health check
- `GET /cache/stats` - Cache statistics

### 2. Core Processing Layer

#### Parser (`src/core/parsers.py`)
- **PDF Processing**: Uses `pdfplumber` for text extraction
- **Image Processing**: OCR with `pytesseract` and `opencv`
- **Data Extraction**: Regex patterns for invoice data
- **Type Detection**: Automatic invoice type classification

#### Tax Service (`src/services/tax_service.py`)
- **Colombian Tax Rules**: IVA, ReteFuente, ICA calculations
- **UVT-based Thresholds**: Dynamic tax thresholds
- **Compliance Validation**: Tax rule compliance checking
- **Multi-year Support**: 2024 and 2025 tax rules

#### Alegra Service (`src/services/alegra_service.py`)
- **API Integration**: RESTful API calls to Alegra
- **Contact Management**: Automatic contact creation/retrieval
- **Item Management**: Product/service management
- **Bill/Invoice Creation**: Purchase and sale invoices

### 3. Data & Cache Layer

#### Repository Pattern (`src/repositories/`)
- **Invoice Repository**: JSON-based persistence
- **Base Repository**: Abstract base classes
- **Cache Repository**: Redis-backed caching

#### Cache Service (`src/services/cache_service.py`)
- **Redis Integration**: High-performance caching
- **Invoice Caching**: Parsed data and results
- **Tax Caching**: Calculated tax results
- **Alegra Caching**: API response caching

### 4. Security Layer (`src/core/security.py`)

#### Input Validation
- **File Validation**: Size, type, and path security
- **Text Validation**: SQL injection and XSS prevention
- **Email/NIT Validation**: Format and security checks

#### Rate Limiting
- **Redis-based**: Sliding window rate limiting
- **User-based**: Per-user rate limits
- **Burst Protection**: Configurable burst limits

#### Secrets Management
- **Encryption**: AES-256-GCM encryption
- **Key Derivation**: PBKDF2 with salt
- **Password Hashing**: Secure password storage

### 5. Async Processing (`src/services/async_service.py`)

#### Async Invoice Processor
- **Concurrent Processing**: Multiple invoices simultaneously
- **Semaphore Control**: Configurable concurrency limits
- **Error Handling**: Robust error recovery

#### Celery Integration
- **Background Tasks**: Long-running processing
- **Queue Management**: Task queuing and scheduling
- **Worker Scaling**: Horizontal scaling support

## Data Flow

### 1. Invoice Processing Flow

```
File Upload → Validation → Parsing → Tax Calculation → Alegra Creation → Caching
     │              │           │            │              │              │
     ▼              ▼           ▼            ▼              ▼              ▼
Security Check → OCR/PDF → Colombian → API Call → Redis Cache
```

### 2. Batch Processing Flow

```
Directory Scan → File Discovery → Concurrent Processing → Result Aggregation
       │              │                    │                      │
       ▼              ▼                    ▼                      ▼
   Validation → Parallel Tasks → Error Handling → Status Report
```

### 3. Caching Strategy

```
Request → Cache Check → Cache Miss → Process → Cache Store → Response
    │           │           │           │           │           │
    ▼           ▼           ▼           ▼           ▼           ▼
Rate Limit → Redis → Database → Service → Redis → Client
```

## Configuration

### Environment Variables
```bash
# Alegra API
ALEGRA_EMAIL=your-email@example.com
ALEGRA_TOKEN=your-api-token

# Redis
REDIS_URL=redis://localhost:6379/0

# Security
MASTER_SECRET_KEY=your-secret-key

# Processing
MAX_CONCURRENT_PROCESSES=10
CACHE_TTL=3600
```

### Configuration Files
- `config/settings.json` - Main configuration
- `config/tax_rules_CO_2025.json` - Tax rules
- `config/accounting_accounts.json` - Chart of accounts

## Deployment

### Development
```bash
# Install dependencies
pip install -r requirements-dev.txt

# Run tests
pytest

# Start development server
python -m uvicorn src.api.app:app --reload
```

### Production
```bash
# Build Docker image
docker build -t supervincent-invoicebot .

# Run with Docker Compose
docker-compose up -d

# Or run directly
python -m uvicorn src.api.app:app --host 0.0.0.0 --port 8000
```

### Docker Services
- **InvoiceBot**: Main application
- **Redis**: Caching and rate limiting
- **Celery**: Background task processing

## Monitoring & Observability

### Health Checks
- **API Health**: `/health` endpoint
- **Service Health**: Redis, Alegra API status
- **Cache Health**: Redis connection and performance

### Metrics
- **Processing Metrics**: Success/failure rates
- **Performance Metrics**: Processing times, cache hit rates
- **Business Metrics**: Invoice volumes, tax calculations

### Logging
- **Structured Logging**: JSON-formatted logs
- **Log Levels**: DEBUG, INFO, WARNING, ERROR, CRITICAL
- **Log Rotation**: Size-based rotation with retention

## Security Considerations

### Input Security
- **File Validation**: Size, type, and content validation
- **Path Security**: Prevention of directory traversal
- **Content Security**: Malware and virus scanning

### API Security
- **Rate Limiting**: Protection against abuse
- **Authentication**: API key or JWT token validation
- **Input Validation**: Request parameter validation

### Data Security
- **Encryption**: Sensitive data encryption at rest
- **Transmission**: HTTPS/TLS for all communications
- **Access Control**: Role-based access control

## Performance Optimization

### Caching Strategy
- **Multi-level Caching**: Redis + application cache
- **Cache Invalidation**: Smart invalidation policies
- **Cache Warming**: Pre-loading frequently accessed data

### Processing Optimization
- **Async Processing**: Non-blocking I/O operations
- **Concurrent Processing**: Parallel invoice processing
- **Resource Pooling**: Connection and thread pooling

### Database Optimization
- **Indexing**: Optimized database indexes
- **Query Optimization**: Efficient data retrieval
- **Connection Pooling**: Database connection management

## Scalability

### Horizontal Scaling
- **Load Balancing**: Multiple application instances
- **Database Sharding**: Distributed data storage
- **Cache Clustering**: Redis cluster for high availability

### Vertical Scaling
- **Resource Optimization**: CPU and memory optimization
- **Processing Limits**: Configurable concurrency limits
- **Queue Management**: Task queue optimization

## Future Enhancements

### Machine Learning
- **Invoice Classification**: ML-based invoice type detection
- **Data Extraction**: AI-powered data extraction
- **Anomaly Detection**: Fraud and error detection

### Microservices
- **Service Decomposition**: Split into microservices
- **API Gateway**: Centralized API management
- **Service Mesh**: Inter-service communication

### Advanced Features
- **Webhook Support**: Real-time notifications
- **Multi-tenant**: Support for multiple organizations
- **Mobile API**: Mobile application support

