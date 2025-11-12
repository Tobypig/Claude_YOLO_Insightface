# 🚀 Production Deployment Guide

This guide covers deploying the Video Frame Person & Face Detection System to production environments.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Docker Deployment](#docker-deployment)
3. [Cloud Deployment](#cloud-deployment)
4. [Security Hardening](#security-hardening)
5. [Performance Tuning](#performance-tuning)
6. [Monitoring & Logging](#monitoring--logging)
7. [Backup & Recovery](#backup--recovery)

---

## Prerequisites

### System Requirements

**Minimum:**
- CPU: 4 cores
- RAM: 8GB
- Storage: 50GB SSD
- OS: Ubuntu 20.04+ / Debian 11+ / RHEL 8+

**Recommended:**
- CPU: 8+ cores
- RAM: 16GB+
- GPU: NVIDIA GPU with 8GB+ VRAM (for optimal performance)
- Storage: 100GB+ NVMe SSD
- OS: Ubuntu 22.04 LTS

### Software Requirements

- Docker 20.10+
- Docker Compose 2.0+
- (Optional) NVIDIA Docker for GPU support
- (Optional) Reverse proxy (nginx/Traefik)
- (Optional) SSL certificates (Let's Encrypt)

---

## Docker Deployment

### 1. Basic Production Setup

```bash
# Clone repository
git clone https://github.com/yourusername/Claude_YOLO_Insightface.git
cd Claude_YOLO_Insightface

# Create production environment file
cp backend/.env.example backend/.env
cp frontend/.env.local.example frontend/.env.local

# Edit configuration for production
nano backend/.env
```

### 2. Production Environment Variables

**Backend (`backend/.env`):**

```env
# Use production values
DEVICE=cuda  # or cpu
API_RELOAD=False  # Disable auto-reload in production

# Security
CORS_ORIGINS=https://yourdomain.com

# Performance
MAX_CONCURRENT_JOBS=5
FRAME_EXTRACTION_QUALITY=2

# Paths
OUTPUT_DIR=/data/output
VIDEO_DIR=/data/videos
CLIPS_DIR=/data/clips
```

**Frontend (`frontend/.env.local`):**

```env
NEXT_PUBLIC_API_URL=https://api.yourdomain.com
```

### 3. Start Production Services

```bash
# Pull latest images (if using pre-built)
docker-compose pull

# Start services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f
```

### 4. With GPU Support

Ensure nvidia-docker is installed, then:

```bash
# Edit docker-compose.yml to uncomment GPU sections
nano docker-compose.yml

# Start with GPU
docker-compose up -d
```

---

## Cloud Deployment

### AWS Deployment

#### Option 1: EC2 with Docker

```bash
# Launch EC2 instance (p3.2xlarge for GPU)
# Security group: Allow ports 80, 443, 8000, 3000

# SSH into instance
ssh -i your-key.pem ubuntu@your-instance-ip

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# For GPU instances, install NVIDIA Docker
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | sudo tee /etc/apt/sources.list.d/nvidia-docker.list
sudo apt-get update && sudo apt-get install -y nvidia-docker2
sudo systemctl restart docker

# Deploy application
git clone your-repo
cd Claude_YOLO_Insightface
./setup.sh
docker-compose up -d
```

#### Option 2: ECS (Elastic Container Service)

1. **Build and push images to ECR:**

```bash
# Authenticate to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin YOUR_AWS_ACCOUNT.dkr.ecr.us-east-1.amazonaws.com

# Build images
docker build -t video-detection-backend backend/
docker build -t video-detection-frontend frontend/

# Tag images
docker tag video-detection-backend:latest YOUR_AWS_ACCOUNT.dkr.ecr.us-east-1.amazonaws.com/video-detection-backend:latest
docker tag video-detection-frontend:latest YOUR_AWS_ACCOUNT.dkr.ecr.us-east-1.amazonaws.com/video-detection-frontend:latest

# Push images
docker push YOUR_AWS_ACCOUNT.dkr.ecr.us-east-1.amazonaws.com/video-detection-backend:latest
docker push YOUR_AWS_ACCOUNT.dkr.ecr.us-east-1.amazonaws.com/video-detection-frontend:latest
```

2. **Create ECS task definitions and services** (use AWS Console or Terraform)

### Google Cloud Platform (GCP)

#### Cloud Run Deployment

```bash
# Build and deploy backend
gcloud builds submit --tag gcr.io/YOUR_PROJECT/video-detection-backend backend/
gcloud run deploy video-detection-backend \
  --image gcr.io/YOUR_PROJECT/video-detection-backend \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --memory 8Gi \
  --cpu 4

# Build and deploy frontend
gcloud builds submit --tag gcr.io/YOUR_PROJECT/video-detection-frontend frontend/
gcloud run deploy video-detection-frontend \
  --image gcr.io/YOUR_PROJECT/video-detection-frontend \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated
```

### Azure Deployment

#### Container Instances

```bash
# Create resource group
az group create --name video-detection-rg --location eastus

# Deploy backend
az container create \
  --resource-group video-detection-rg \
  --name video-detection-backend \
  --image your-registry.azurecr.io/video-detection-backend:latest \
  --cpu 4 \
  --memory 8 \
  --ports 8000

# Deploy frontend
az container create \
  --resource-group video-detection-rg \
  --name video-detection-frontend \
  --image your-registry.azurecr.io/video-detection-frontend:latest \
  --cpu 2 \
  --memory 4 \
  --ports 3000
```

---

## Security Hardening

### 1. SSL/TLS Configuration

```nginx
# nginx configuration for SSL
server {
    listen 443 ssl http2;
    server_name api.yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### 2. Firewall Configuration

```bash
# UFW (Ubuntu)
sudo ufw allow 22/tcp   # SSH
sudo ufw allow 80/tcp   # HTTP
sudo ufw allow 443/tcp  # HTTPS
sudo ufw enable

# Only allow backend from frontend
sudo ufw allow from FRONTEND_IP to any port 8000
```

### 3. API Authentication

Add JWT authentication to the backend:

```python
# Add to backend/main.py
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt

security = HTTPBearer()

@app.middleware("http")
async def authenticate_request(request: Request, call_next):
    if request.url.path.startswith("/api/"):
        # Verify JWT token
        pass
    return await call_next(request)
```

### 4. Rate Limiting

```python
# Add to backend/main.py
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.post("/api/process")
@limiter.limit("10/minute")
async def process_video(request: Request, ...):
    ...
```

---

## Performance Tuning

### 1. GPU Optimization

```python
# backend/.env
DEVICE=cuda
YOLO_MODEL=yolov8n.pt  # Use smaller model for faster inference
INSIGHTFACE_MODEL=buffalo_l
```

### 2. Caching Strategy

```python
# Add Redis caching
from redis import Redis
from functools import lru_cache

redis_client = Redis(host='localhost', port=6379, db=0)

@lru_cache(maxsize=100)
def get_cached_embedding(face_id: str):
    cached = redis_client.get(f"embed:{face_id}")
    return cached if cached else None
```

### 3. Load Balancing

```yaml
# docker-compose-production.yml
version: '3.8'
services:
  backend:
    image: video-detection-backend
    deploy:
      replicas: 3  # Run 3 instances
      resources:
        limits:
          cpus: '2'
          memory: 4G
```

### 4. Database Optimization

```python
# Use PostgreSQL for job persistence
# Add to backend/requirements.txt:
# psycopg2-binary==2.9.9
# sqlalchemy==2.0.23

from sqlalchemy import create_engine
engine = create_engine('postgresql://user:pass@localhost/video_detection')
```

---

## Monitoring & Logging

### 1. Prometheus Metrics

```yaml
# docker-compose.yml - add
  prometheus:
    image: prom/prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml

  grafana:
    image: grafana/grafana
    ports:
      - "3001:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
```

### 2. Application Monitoring

```python
# Add to backend/main.py
from prometheus_client import Counter, Histogram, make_asgi_app

REQUEST_COUNT = Counter('http_requests_total', 'Total HTTP requests')
REQUEST_DURATION = Histogram('http_request_duration_seconds', 'HTTP request duration')

# Mount metrics endpoint
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)
```

### 3. Log Aggregation

```yaml
# docker-compose.yml - add ELK stack
  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.11.0
    environment:
      - discovery.type=single-node

  logstash:
    image: docker.elastic.co/logstash/logstash:8.11.0
    volumes:
      - ./logstash.conf:/usr/share/logstash/pipeline/logstash.conf

  kibana:
    image: docker.elastic.co/kibana/kibana:8.11.0
    ports:
      - "5601:5601"
```

### 4. Health Checks

```python
# Add comprehensive health check
@app.get("/api/health/detailed")
async def detailed_health_check():
    return {
        "status": "healthy",
        "version": "1.0.0",
        "gpu_available": torch.cuda.is_available(),
        "gpu_name": torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,
        "disk_usage": get_disk_usage(),
        "memory_usage": get_memory_usage(),
    }
```

---

## Backup & Recovery

### 1. Data Backup

```bash
# Create backup script
#!/bin/bash
BACKUP_DIR=/backups/$(date +%Y%m%d)
mkdir -p $BACKUP_DIR

# Backup output data
tar -czf $BACKUP_DIR/output.tar.gz backend/data/output/

# Backup database
docker exec postgres pg_dump -U user video_detection > $BACKUP_DIR/database.sql

# Upload to S3
aws s3 cp $BACKUP_DIR s3://your-bucket/backups/$(date +%Y%m%d)/ --recursive
```

### 2. Automated Backups

```bash
# Add to crontab
0 2 * * * /path/to/backup.sh  # Daily at 2 AM
```

### 3. Disaster Recovery

```bash
# Restore from backup
tar -xzf output.tar.gz -C backend/data/
docker exec -i postgres psql -U user video_detection < database.sql
```

---

## Maintenance

### 1. Updates

```bash
# Pull latest code
git pull origin main

# Rebuild containers
docker-compose build

# Rolling update
docker-compose up -d --no-deps --build backend
docker-compose up -d --no-deps --build frontend
```

### 2. Cleanup

```bash
# Remove old outputs (keep last 30 days)
find backend/data/output -mtime +30 -type d -exec rm -rf {} \;

# Prune Docker
docker system prune -af --volumes
```

### 3. Monitoring Checklist

- [ ] Check disk space regularly
- [ ] Monitor GPU usage
- [ ] Review error logs daily
- [ ] Test backups monthly
- [ ] Update dependencies quarterly
- [ ] Review security patches

---

## Troubleshooting

### High Memory Usage

```bash
# Check container memory
docker stats

# Increase memory limits
# Edit docker-compose.yml:
    deploy:
      resources:
        limits:
          memory: 8G
```

### Slow Processing

```bash
# Enable GPU
DEVICE=cuda

# Use smaller models
YOLO_MODEL=yolov8n.pt

# Increase workers
MAX_CONCURRENT_JOBS=5
```

### Connection Issues

```bash
# Check service health
curl http://localhost:8000/api/health

# Check logs
docker-compose logs backend
docker-compose logs frontend

# Restart services
docker-compose restart
```

---

## Support

For production deployment issues:
- Check logs first: `docker-compose logs -f`
- Review [GETTING_STARTED.md](GETTING_STARTED.md)
- Open an issue on GitHub
- Contact DevOps team

---

**Note:** This guide assumes familiarity with Docker, cloud platforms, and system administration. Adjust configurations based on your specific requirements and infrastructure.
