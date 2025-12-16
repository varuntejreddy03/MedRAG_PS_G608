# AWS Deployment Guide - MedRAG Backend

## Quick Deploy (Recommended: AWS EC2)

### 1. Launch EC2 Instance
```bash
# Instance Type: t3.large (2 vCPU, 8GB RAM) - for FAISS + Gemini
# AMI: Ubuntu 22.04 LTS
# Storage: 30GB gp3
# Security Group: Allow ports 22 (SSH), 8000 (FastAPI)
```

### 2. Connect to EC2
```bash
ssh -i your-key.pem ubuntu@your-ec2-ip
```

### 3. Install Dependencies
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python 3.11
sudo apt install python3.11 python3.11-venv python3-pip -y

# Install system dependencies
sudo apt install build-essential libpq-dev -y
```

### 4. Setup Application
```bash
# Clone or upload your code
cd /home/ubuntu
mkdir medrag && cd medrag

# Upload backend files (use scp or git)
scp -i your-key.pem -r backend/ ubuntu@your-ec2-ip:/home/ubuntu/medrag/

# Create virtual environment
cd backend
python3.11 -m venv venv
source venv/bin/activate

# Install requirements
pip install --upgrade pip
pip install -r requirements.txt
```

### 5. Configure Environment
```bash
# Create .env file
nano .env
```

Add:
```env
DATABASE_URL=postgresql://user:pass@your-neon-db.neon.tech/neondb
GEMINI_API_KEY=AIzaSyAYN4PHFXeCxgITThJr4KIwke7ZkxSmUS4
GEMINI_MODEL=gemini-2.0-flash-exp
GMAIL_USER=your-email@gmail.com
GMAIL_APP_PASSWORD=your-app-password
AWS_ACCESS_KEY_ID=your-key
AWS_SECRET_ACCESS_KEY=your-secret
S3_BUCKET_NAME=medrag-data-bucket
AWS_REGION=us-east-1
```

### 6. Download Models from S3
```bash
python3 -c "from app.services.s3_loader import download_from_s3; download_from_s3()"
```

### 7. Setup Systemd Service
```bash
sudo nano /etc/systemd/system/medrag.service
```

Add:
```ini
[Unit]
Description=MedRAG FastAPI Backend
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/medrag/backend
Environment="PATH=/home/ubuntu/medrag/backend/venv/bin"
ExecStart=/home/ubuntu/medrag/backend/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### 8. Start Service
```bash
sudo systemctl daemon-reload
sudo systemctl enable medrag
sudo systemctl start medrag
sudo systemctl status medrag
```

### 9. Setup Nginx (Optional - for HTTPS)
```bash
sudo apt install nginx -y

sudo nano /etc/nginx/sites-available/medrag
```

Add:
```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

```bash
sudo ln -s /etc/nginx/sites-available/medrag /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### 10. Setup SSL with Certbot
```bash
sudo apt install certbot python3-certbot-nginx -y
sudo certbot --nginx -d your-domain.com
```

---

## Alternative: AWS Lambda + API Gateway (Serverless)

### 1. Install Serverless Framework
```bash
npm install -g serverless
```

### 2. Create serverless.yml
```yaml
service: medrag-api

provider:
  name: aws
  runtime: python3.11
  region: us-east-1
  environment:
    DATABASE_URL: ${env:DATABASE_URL}
    GEMINI_API_KEY: ${env:GEMINI_API_KEY}

functions:
  api:
    handler: app.main.handler
    events:
      - http:
          path: /{proxy+}
          method: ANY
    timeout: 30
    memorySize: 3008
```

### 3. Create Lambda Handler
```python
# app/main.py - Add at bottom
from mangum import Mangum
handler = Mangum(app)
```

### 4. Deploy
```bash
pip install mangum
serverless deploy
```

---

## Alternative: AWS ECS Fargate (Docker)

### 1. Create Dockerfile
```dockerfile
FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 2. Build and Push to ECR
```bash
# Create ECR repository
aws ecr create-repository --repository-name medrag-backend

# Login to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin YOUR_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com

# Build and push
docker build -t medrag-backend .
docker tag medrag-backend:latest YOUR_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/medrag-backend:latest
docker push YOUR_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/medrag-backend:latest
```

### 3. Create ECS Task Definition
```json
{
  "family": "medrag-backend",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "2048",
  "memory": "4096",
  "containerDefinitions": [
    {
      "name": "medrag-api",
      "image": "YOUR_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/medrag-backend:latest",
      "portMappings": [
        {
          "containerPort": 8000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {"name": "DATABASE_URL", "value": "your-db-url"},
        {"name": "GEMINI_API_KEY", "value": "your-key"}
      ]
    }
  ]
}
```

### 4. Create ECS Service
```bash
aws ecs create-service \
  --cluster medrag-cluster \
  --service-name medrag-backend \
  --task-definition medrag-backend \
  --desired-count 1 \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[subnet-xxx],securityGroups=[sg-xxx],assignPublicIp=ENABLED}"
```

---

## Cost Comparison

| Method | Monthly Cost | Pros | Cons |
|--------|-------------|------|------|
| **EC2 t3.large** | ~$60 | Simple, full control | Always running |
| **Lambda** | ~$20-40 | Pay per use | Cold starts, 15min timeout |
| **ECS Fargate** | ~$80 | Scalable, managed | More complex setup |

---

## Recommended: EC2 t3.large

**Why?**
- FAISS requires consistent memory (4.4GB index)
- Gemini API calls need stable connection
- Session management works better with persistent server
- Cost-effective for 24/7 availability

---

## Post-Deployment Checklist

- [ ] Update frontend `NEXT_PUBLIC_API_URL` to EC2 public IP or domain
- [ ] Configure CORS in `backend/app/main.py` with frontend URL
- [ ] Setup CloudWatch logs for monitoring
- [ ] Configure automatic backups for EC2
- [ ] Setup Route53 for custom domain
- [ ] Enable AWS CloudWatch alarms for CPU/Memory
- [ ] Test all API endpoints
- [ ] Verify FAISS model loading
- [ ] Test Gemini API integration
- [ ] Verify email sending works

---

## Monitoring

```bash
# View logs
sudo journalctl -u medrag -f

# Check service status
sudo systemctl status medrag

# Restart service
sudo systemctl restart medrag
```

---

## Troubleshooting

### Service won't start
```bash
# Check logs
sudo journalctl -u medrag -n 50

# Test manually
cd /home/ubuntu/medrag/backend
source venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Out of memory
```bash
# Check memory usage
free -h

# Upgrade to t3.xlarge (4 vCPU, 16GB RAM)
```

### FAISS not loading
```bash
# Re-download models
python3 -c "from app.services.s3_loader import download_from_s3; download_from_s3()"

# Check models directory
ls -lh models/
```
