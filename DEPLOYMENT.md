# SuperVincent InvoiceBot Deployment Guide

## Overview

This guide covers deployment options for SuperVincent InvoiceBot, from development to production environments.

## Prerequisites

### System Requirements
- **Python**: 3.8 or higher
- **Memory**: 2GB RAM minimum, 4GB recommended
- **Storage**: 10GB free space
- **Network**: Internet access for API calls

### External Dependencies
- **Redis**: For caching and rate limiting
- **Alegra API**: Accounting system integration
- **Tesseract OCR**: For image processing (optional)

## Development Deployment

### 1. Local Development Setup

```bash
# Clone repository
git clone <repository-url>
cd supervincent

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements-dev.txt

# Install pre-commit hooks
pre-commit install

# Set up environment variables
cp .env.example .env
# Edit .env with your configuration
```

### 2. Configuration

Create `.env` file:
```bash
# Alegra API Configuration
ALEGRA_EMAIL=your-email@example.com
ALEGRA_TOKEN=your-api-token
ALEGRA_BASE_URL=https://api.alegra.com/api/v1

# Redis Configuration
REDIS_URL=redis://localhost:6379/0

# Security
MASTER_SECRET_KEY=your-secret-key-here

# Processing Configuration
MAX_CONCURRENT_PROCESSES=5
CACHE_TTL=3600
RATE_LIMIT_PER_HOUR=100

# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/invoicebot.log
```

### 3. Start Services

```bash
# Start Redis (if not running)
redis-server

# Start development server
python -m uvicorn src.api.app:app --reload --host 0.0.0.0 --port 8000

# Or start with specific configuration
python -m uvicorn src.api.app:app --reload --host 0.0.0.0 --port 8000 --log-level info
```

### 4. Verify Installation

```bash
# Check health endpoint
curl http://localhost:8000/health

# Check API documentation
open http://localhost:8000/docs
```

## Docker Deployment

### 1. Build Docker Image

```bash
# Build image
docker build -t supervincent-invoicebot:latest .

# Build with specific tag
docker build -t supervincent-invoicebot:v1.0.0 .
```

### 2. Run with Docker Compose

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### 3. Docker Compose Configuration

```yaml
version: '3.8'

services:
  invoicebot:
    build: .
    container_name: invoicebot_app
    env_file:
      - .env
    volumes:
      - .:/app
      - ./logs:/app/logs
      - ./reports:/app/reports
      - ./facturas:/app/facturas
      - ./backup:/app/backup
    ports:
      - "8000:8000"
    depends_on:
      - redis
    command: python -m uvicorn src.api.app:app --host 0.0.0.0 --port 8000

  redis:
    image: "redis:alpine"
    container_name: invoicebot_redis
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    command: redis-server --appendonly yes

  celery:
    build: .
    container_name: invoicebot_celery
    env_file:
      - .env
    volumes:
      - .:/app
    depends_on:
      - redis
    command: celery -A src.services.async_service worker --loglevel=info

volumes:
  redis_data:
```

## Production Deployment

### 1. Server Setup

#### Ubuntu/Debian
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python 3.8+
sudo apt install python3.8 python3.8-venv python3-pip

# Install Redis
sudo apt install redis-server

# Install Tesseract OCR
sudo apt install tesseract-ocr tesseract-ocr-spa

# Install system dependencies
sudo apt install libgl1-mesa-glx libglib2.0-0 libsm6 libxext6 libxrender-dev libgomp1
```

#### CentOS/RHEL
```bash
# Update system
sudo yum update -y

# Install Python 3.8+
sudo yum install python38 python38-pip

# Install Redis
sudo yum install redis

# Install Tesseract OCR
sudo yum install tesseract tesseract-langpack-spa

# Install system dependencies
sudo yum install mesa-libGL glib2 libSM libXext libXrender libgomp
```

### 2. Application Deployment

```bash
# Create application user
sudo useradd -m -s /bin/bash invoicebot
sudo su - invoicebot

# Clone repository
git clone <repository-url>
cd supervincent

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install production dependencies
pip install -r requirements-prod.txt

# Set up configuration
cp .env.example .env
# Edit .env with production values
```

### 3. Systemd Service

Create `/etc/systemd/system/invoicebot.service`:
```ini
[Unit]
Description=SuperVincent InvoiceBot
After=network.target redis.service

[Service]
Type=exec
User=invoicebot
Group=invoicebot
WorkingDirectory=/home/invoicebot/supervincent
Environment=PATH=/home/invoicebot/supervincent/venv/bin
ExecStart=/home/invoicebot/supervincent/venv/bin/python -m uvicorn src.api.app:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Create `/etc/systemd/system/invoicebot-celery.service`:
```ini
[Unit]
Description=SuperVincent InvoiceBot Celery Worker
After=network.target redis.service

[Service]
Type=exec
User=invoicebot
Group=invoicebot
WorkingDirectory=/home/invoicebot/supervincent
Environment=PATH=/home/invoicebot/supervincent/venv/bin
ExecStart=/home/invoicebot/supervincent/venv/bin/celery -A src.services.async_service worker --loglevel=info
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### 4. Start Services

```bash
# Enable and start services
sudo systemctl enable invoicebot
sudo systemctl enable invoicebot-celery
sudo systemctl start invoicebot
sudo systemctl start invoicebot-celery

# Check status
sudo systemctl status invoicebot
sudo systemctl status invoicebot-celery
```

### 5. Nginx Configuration

Create `/etc/nginx/sites-available/invoicebot`:
```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /health {
        proxy_pass http://127.0.0.1:8000/health;
        access_log off;
    }
}
```

Enable site:
```bash
sudo ln -s /etc/nginx/sites-available/invoicebot /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

## Cloud Deployment

### 1. AWS Deployment

#### EC2 Instance
```bash
# Launch EC2 instance (t3.medium or larger)
# Install Docker
sudo yum update -y
sudo yum install -y docker
sudo systemctl start docker
sudo systemctl enable docker

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/1.29.2/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Deploy application
git clone <repository-url>
cd supervincent
docker-compose up -d
```

#### ECS Deployment
```yaml
# ecs-task-definition.json
{
  "family": "invoicebot",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "512",
  "memory": "1024",
  "executionRoleArn": "arn:aws:iam::account:role/ecsTaskExecutionRole",
  "containerDefinitions": [
    {
      "name": "invoicebot",
      "image": "your-account.dkr.ecr.region.amazonaws.com/invoicebot:latest",
      "portMappings": [
        {
          "containerPort": 8000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "REDIS_URL",
          "value": "redis://your-redis-cluster.cache.amazonaws.com:6379"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/invoicebot",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ]
}
```

### 2. Google Cloud Deployment

#### Cloud Run
```bash
# Build and push image
gcloud builds submit --tag gcr.io/PROJECT-ID/invoicebot

# Deploy to Cloud Run
gcloud run deploy invoicebot \
  --image gcr.io/PROJECT-ID/invoicebot \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --memory 1Gi \
  --cpu 1 \
  --max-instances 10
```

### 3. Azure Deployment

#### Container Instances
```bash
# Build and push image
az acr build --registry myregistry --image invoicebot:latest .

# Deploy to Container Instances
az container create \
  --resource-group myResourceGroup \
  --name invoicebot \
  --image myregistry.azurecr.io/invoicebot:latest \
  --cpu 1 \
  --memory 2 \
  --ports 8000 \
  --environment-variables \
    REDIS_URL=redis://myredis.redis.cache.windows.net:6380 \
    ALEGRA_EMAIL=your-email@example.com \
    ALEGRA_TOKEN=your-token
```

## Monitoring & Maintenance

### 1. Health Monitoring

```bash
# Check application health
curl http://localhost:8000/health

# Check Redis connection
redis-cli ping

# Check Celery workers
celery -A src.services.async_service inspect active
```

### 2. Log Monitoring

```bash
# View application logs
sudo journalctl -u invoicebot -f

# View Celery logs
sudo journalctl -u invoicebot-celery -f

# View Docker logs
docker-compose logs -f invoicebot
```

### 3. Performance Monitoring

```bash
# Check cache statistics
curl http://localhost:8000/cache/stats

# Monitor Redis
redis-cli info stats

# Monitor system resources
htop
```

### 4. Backup & Recovery

```bash
# Backup Redis data
redis-cli BGSAVE

# Backup application data
tar -czf backup-$(date +%Y%m%d).tar.gz \
  data/ \
  logs/ \
  reports/ \
  backup/

# Restore from backup
tar -xzf backup-20250110.tar.gz
```

## Troubleshooting

### Common Issues

#### 1. Redis Connection Issues
```bash
# Check Redis status
sudo systemctl status redis

# Check Redis logs
sudo journalctl -u redis -f

# Test Redis connection
redis-cli ping
```

#### 2. Application Startup Issues
```bash
# Check application logs
sudo journalctl -u invoicebot -f

# Check configuration
python -c "from src.core.config import Settings; print(Settings())"

# Test imports
python -c "import src.api.app"
```

#### 3. Celery Worker Issues
```bash
# Check Celery status
celery -A src.services.async_service inspect active

# Restart Celery workers
sudo systemctl restart invoicebot-celery

# Check Celery logs
sudo journalctl -u invoicebot-celery -f
```

#### 4. OCR Issues
```bash
# Check Tesseract installation
tesseract --version

# Test OCR
tesseract test-image.png output -l spa

# Install additional language packs
sudo apt install tesseract-ocr-spa
```

### Performance Optimization

#### 1. Redis Optimization
```bash
# Configure Redis for production
sudo nano /etc/redis/redis.conf

# Set memory limit
maxmemory 512mb
maxmemory-policy allkeys-lru

# Enable persistence
save 900 1
save 300 10
save 60 10000
```

#### 2. Application Optimization
```bash
# Increase worker processes
gunicorn src.api.app:app -w 4 -k uvicorn.workers.UvicornWorker

# Configure Celery workers
celery -A src.services.async_service worker --concurrency=4
```

## Security Considerations

### 1. Firewall Configuration
```bash
# Configure UFW
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

### 2. SSL/TLS Configuration
```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx

# Obtain SSL certificate
sudo certbot --nginx -d your-domain.com

# Auto-renewal
sudo crontab -e
# Add: 0 12 * * * /usr/bin/certbot renew --quiet
```

### 3. Environment Security
```bash
# Secure environment file
chmod 600 .env

# Use secrets management
# AWS Secrets Manager, HashiCorp Vault, etc.
```

## Scaling Considerations

### 1. Horizontal Scaling
- **Load Balancer**: Nginx, HAProxy, or cloud load balancer
- **Multiple Instances**: Deploy multiple application instances
- **Database Clustering**: Redis cluster for high availability

### 2. Vertical Scaling
- **Resource Monitoring**: CPU, memory, and disk usage
- **Instance Sizing**: Upgrade instance types as needed
- **Performance Tuning**: Optimize application and database settings

### 3. Auto-scaling
- **Cloud Auto-scaling**: AWS Auto Scaling, GCP Autoscaler
- **Container Orchestration**: Kubernetes, Docker Swarm
- **Queue-based Scaling**: Scale based on queue depth

