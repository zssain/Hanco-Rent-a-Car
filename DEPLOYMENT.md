# Hanco AI - AWS Deployment Guide

This guide covers production deployment to AWS infrastructure.

## 📋 Prerequisites

1. **AWS Account** with appropriate permissions
2. **AWS CLI** installed and configured (`aws configure`)
3. **Firebase Project** set up with Firestore enabled
4. **API Keys**:
   - Firebase service account JSON file
   - Gemini API key
5. **Domain** (optional, for custom domain)

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                         AWS Cloud                           │
│                                                             │
│  ┌──────────────────┐         ┌──────────────────┐        │
│  │   CloudFront     │         │      EC2         │        │
│  │   (CDN)          │────────▶│   (Backend)      │        │
│  │                  │         │   FastAPI        │        │
│  └──────────────────┘         │   + Nginx        │        │
│           │                   └──────────────────┘        │
│           │                            │                   │
│  ┌──────────────────┐                 │                   │
│  │       S3         │                 │                   │
│  │   (Frontend)     │                 │                   │
│  │   React Build    │                 │                   │
│  └──────────────────┘                 │                   │
│                                        │                   │
└────────────────────────────────────────┼───────────────────┘
                                         │
                              ┌──────────▼────────────┐
                              │  Firebase Firestore   │
                              │  (Database + Auth)    │
                              └───────────────────────┘
                                         │
                              ┌──────────▼────────────┐
                              │   Google Gemini AI    │
                              │   (Chatbot)           │
                              └───────────────────────┘
```

## 🔐 Step 1: Prepare Secrets

### 1.1 Firebase Credentials

Download your Firebase service account key:
1. Go to Firebase Console → Project Settings → Service Accounts
2. Click "Generate New Private Key"
3. Save as `firebase-key.json` (DO NOT commit to git)

### 1.2 Create Environment Files

**Backend** (`backend/.env`):
```bash
# Copy from example
cp backend/.env.example backend/.env

# Edit with your values:
ENVIRONMENT=production
DEBUG=False
LOG_LEVEL=INFO

# Firebase - CRITICAL: Set this path
GOOGLE_APPLICATION_CREDENTIALS=/etc/secrets/firebase-key.json
FIREBASE_PROJECT_ID=your-project-id
FIREBASE_API_KEY=your-web-api-key
FIREBASE_AUTH_DOMAIN=your-project.firebaseapp.com
FIREBASE_STORAGE_BUCKET=your-project.firebasestorage.app
FIREBASE_MESSAGING_SENDER_ID=123456789012
FIREBASE_APP_ID=1:123456789012:web:abcdef
FIREBASE_MEASUREMENT_ID=G-XXXXXXXXXX

# AI Services
GEMINI_API_KEY=your-gemini-key-here
OPENAI_API_KEY=  # Optional

# CORS - Add your frontend URL after deployment
ALLOWED_ORIGINS=https://your-cloudfront-url.cloudfront.net,https://yourdomain.com

# Other settings
FRONTEND_URL=https://your-cloudfront-url.cloudfront.net
RATE_LIMIT_ENABLED=True
RATE_LIMIT_PER_MINUTE=60
```

**Frontend** (`frontend/.env.production`):
```bash
# Backend API URL (will be your EC2 URL)
VITE_API_BASE_URL=https://your-ec2-domain-or-ip.com

# Firebase Web Config
VITE_FIREBASE_API_KEY=your-web-api-key
VITE_FIREBASE_AUTH_DOMAIN=your-project.firebaseapp.com
VITE_FIREBASE_PROJECT_ID=your-project-id
VITE_FIREBASE_STORAGE_BUCKET=your-project.firebasestorage.app
VITE_FIREBASE_MESSAGING_SENDER_ID=123456789012
VITE_FIREBASE_APP_ID=1:123456789012:web:abcdef
VITE_FIREBASE_MEASUREMENT_ID=G-XXXXXXXXXX
```

## 🖥️ Step 2: Deploy Backend to EC2

### 2.1 Launch EC2 Instance

```bash
# Launch Ubuntu 22.04 LTS instance
# Instance type: t3.small or larger (t3.medium recommended for production)
# Storage: 20GB minimum
# Security Group: Allow ports 22 (SSH), 80 (HTTP), 443 (HTTPS)
```

### 2.2 Connect and Setup

```bash
# SSH into your instance
ssh -i your-key.pem ubuntu@your-ec2-ip

# Run the automated setup script
cd /tmp
wget https://raw.githubusercontent.com/YOUR_REPO/main/infra/ec2/install_dependencies.sh
chmod +x install_dependencies.sh
sudo ./install_dependencies.sh
```

**Or manual setup:**

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python 3.11
sudo apt install -y python3.11 python3.11-venv python3-pip

# Install Nginx
sudo apt install -y nginx

# Install Git
sudo apt install -y git

# Clone your repository (use private repo deploy key)
cd /opt
sudo git clone https://github.com/YOUR_USERNAME/YOUR_REPO.git hanco-ai
cd hanco-ai

# Create secrets directory
sudo mkdir -p /etc/secrets
sudo chmod 700 /etc/secrets

# Upload Firebase credentials
# On your local machine:
scp -i your-key.pem firebase-key.json ubuntu@your-ec2-ip:/tmp/
# On EC2:
sudo mv /tmp/firebase-key.json /etc/secrets/
sudo chmod 600 /etc/secrets/firebase-key.json

# Setup backend
cd /opt/hanco-ai/backend
python3.11 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Create .env file
sudo nano .env
# Paste your production backend env vars (see Step 1.2)

# Test backend
uvicorn app.main:app --host 0.0.0.0 --port 8000
# Press Ctrl+C after verifying it works
```

### 2.3 Configure Nginx

```bash
# Use the provided Nginx config
sudo cp /opt/hanco-ai/infra/ec2/nginx.conf /etc/nginx/sites-available/hanco-backend
sudo ln -s /etc/nginx/sites-available/hanco-backend /etc/nginx/sites-enabled/
sudo rm /etc/nginx/sites-enabled/default

# Test Nginx config
sudo nginx -t

# Reload Nginx
sudo systemctl reload nginx
```

### 2.4 Setup Systemd Service

```bash
# Create systemd service file
sudo nano /etc/systemd/system/hanco-backend.service
```

Paste:
```ini
[Unit]
Description=Hanco AI Backend
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/opt/hanco-ai/backend
Environment="PATH=/opt/hanco-ai/backend/venv/bin"
ExecStart=/opt/hanco-ai/backend/venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000 --workers 2
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable hanco-backend
sudo systemctl start hanco-backend

# Check status
sudo systemctl status hanco-backend

# View logs
sudo journalctl -u hanco-backend -f
```

### 2.5 Setup SSL (Optional but Recommended)

```bash
# Install Certbot
sudo apt install -y certbot python3-certbot-nginx

# Get SSL certificate (requires domain pointing to EC2)
sudo certbot --nginx -d yourdomain.com

# Auto-renewal is configured automatically
```

### 2.6 Test Backend

```bash
# Test health endpoint
curl http://your-ec2-ip/health

# Should return:
# {"status":"healthy","version":"1.0.0",...}

# Test API docs
# Visit: http://your-ec2-ip/api/v1/docs
```

## ☁️ Step 3: Deploy Frontend to S3 + CloudFront

### 3.1 Build Frontend

**On your local machine:**

```bash
cd frontend

# Create production env file
cp .env.example .env.production

# Edit .env.production with your EC2 backend URL
nano .env.production
# Set: VITE_API_BASE_URL=https://your-ec2-domain.com

# Build for production
npm install
npm run build

# This creates frontend/dist/ directory
```

### 3.2 Create S3 Bucket

```bash
# Create bucket (use unique name)
aws s3 mb s3://hanco-frontend-prod --region us-east-1

# Enable static website hosting
aws s3 website s3://hanco-frontend-prod --index-document index.html --error-document index.html

# Upload build
cd dist
aws s3 sync . s3://hanco-frontend-prod --delete

# Set public read policy
aws s3api put-bucket-policy --bucket hanco-frontend-prod --policy '{
  "Version": "2012-10-17",
  "Statement": [{
    "Sid": "PublicReadGetObject",
    "Effect": "Allow",
    "Principal": "*",
    "Action": "s3:GetObject",
    "Resource": "arn:aws:s3:::hanco-frontend-prod/*"
  }]
}'
```

**Or use the deployment script:**

```bash
cd infra/s3
chmod +x deploy_frontend.sh
./deploy_frontend.sh hanco-frontend-prod us-east-1
```

### 3.3 Setup CloudFront

1. Go to AWS Console → CloudFront → Create Distribution
2. **Origin Settings**:
   - Origin Domain: `hanco-frontend-prod.s3-website-us-east-1.amazonaws.com`
   - Origin Protocol: HTTP only
3. **Default Cache Behavior**:
   - Viewer Protocol: Redirect HTTP to HTTPS
   - Allowed HTTP Methods: GET, HEAD, OPTIONS
   - Cache Policy: CachingOptimized
4. **Settings**:
   - Price Class: Use all edge locations (or choose based on your region)
   - Alternate Domain Names: yourdomain.com (if using custom domain)
   - SSL Certificate: Default or ACM certificate
5. **Create Distribution**

**Wait 10-15 minutes for deployment**

### 3.4 Update Backend CORS

After CloudFront deployment:

```bash
# SSH to EC2
ssh -i your-key.pem ubuntu@your-ec2-ip

# Update backend .env
cd /opt/hanco-ai/backend
sudo nano .env

# Add CloudFront URL to ALLOWED_ORIGINS:
ALLOWED_ORIGINS=https://d1234567890.cloudfront.net,https://yourdomain.com

# Restart backend
sudo systemctl restart hanco-backend
```

## 🧪 Step 4: Testing

### 4.1 Health Checks

```bash
# Backend health
curl https://your-backend-domain.com/health

# Frontend (visit in browser)
https://your-cloudfront-url.cloudfront.net
```

### 4.2 Functionality Tests

1. Visit frontend URL
2. Test user registration/login
3. Test vehicle browsing
4. Test AI chatbot
5. Test booking flow
6. Check Firebase Console for data

## 📊 Step 5: Monitoring & Maintenance

### Backend Logs

```bash
# View real-time logs
sudo journalctl -u hanco-backend -f

# View recent errors
sudo journalctl -u hanco-backend --since "1 hour ago" | grep ERROR

# Application logs
sudo tail -f /opt/hanco-ai/backend/logs/app.log  # if logging to file
```

### Frontend Logs

- Browser DevTools Console
- CloudFront Access Logs (enable in CloudFront settings)

### Database

- Monitor in Firebase Console
- Set up usage alerts
- Regular backups via Firebase automated backups

### Performance Monitoring

- AWS CloudWatch for EC2 metrics
- CloudFront metrics for frontend
- Firebase Performance Monitoring (optional)

## 🔄 Updates & Redeployment

### Backend Updates

```bash
# SSH to EC2
ssh -i your-key.pem ubuntu@your-ec2-ip

# Pull latest code
cd /opt/hanco-ai
sudo git pull origin main

# Update dependencies if needed
cd backend
source venv/bin/activate
pip install -r requirements.txt

# Restart service
sudo systemctl restart hanco-backend

# Verify
sudo systemctl status hanco-backend
```

### Frontend Updates

```bash
# On local machine
cd frontend
npm run build

# Sync to S3
aws s3 sync dist/ s3://hanco-frontend-prod --delete

# Invalidate CloudFront cache
aws cloudfront create-invalidation --distribution-id YOUR_DIST_ID --paths "/*"
```

## 💰 Cost Estimates (Monthly)

- **EC2 t3.small**: ~$15/month
- **S3 Storage (5GB)**: ~$0.12/month
- **CloudFront (100GB transfer)**: ~$8.50/month
- **Firebase (Spark/Blaze)**: Free tier or pay-as-you-go
- **Gemini API**: Free tier (60 RPM) or pay-as-you-go

**Total**: ~$25-50/month for moderate traffic

## 🔒 Security Checklist

- [ ] Firebase credentials stored securely in `/etc/secrets/` with 600 permissions
- [ ] `.env` files NOT committed to git
- [ ] EC2 security group allows only ports 22, 80, 443
- [ ] SSH key-based authentication only (no password auth)
- [ ] SSL/TLS enabled on backend (via Certbot)
- [ ] CloudFront HTTPS enforced
- [ ] Firebase security rules configured
- [ ] API rate limiting enabled
- [ ] Regular security updates: `sudo apt update && sudo apt upgrade`
- [ ] Backup strategy for Firestore data

## 🆘 Troubleshooting

### Backend Issues

**Service won't start:**
```bash
sudo journalctl -u hanco-backend -n 50
# Check for:
# - Missing environment variables
# - Firebase credentials path incorrect
# - Port conflicts
```

**CORS errors:**
```bash
# Verify ALLOWED_ORIGINS includes frontend URL
cd /opt/hanco-ai/backend
cat .env | grep ALLOWED_ORIGINS

# Restart after changes
sudo systemctl restart hanco-backend
```

**Firebase connection errors:**
```bash
# Verify credentials file exists and is readable
sudo ls -la /etc/secrets/firebase-key.json

# Test Firebase connection
cd /opt/hanco-ai/backend
source venv/bin/activate
python -c "from app.core.firebase import firebase_client; print(firebase_client.db)"
```

### Frontend Issues

**Blank page:**
- Check browser console for errors
- Verify `VITE_API_BASE_URL` is correct in build
- Check CloudFront distribution status

**API calls failing:**
- Verify backend URL in `.env.production`
- Check CORS settings on backend
- Verify backend is running: `curl https://backend-url/health`

### Performance Issues

**Slow backend:**
- Check EC2 instance metrics in CloudWatch
- Consider upgrading to t3.medium
- Enable caching in Nginx
- Add database indexes in Firestore

**Slow frontend:**
- Verify CloudFront is being used (check response headers)
- Enable compression in S3/CloudFront
- Optimize bundle size

## 📚 Additional Resources

- [AWS EC2 Documentation](https://docs.aws.amazon.com/ec2/)
- [CloudFront Documentation](https://docs.aws.amazon.com/cloudfront/)
- [Firebase Documentation](https://firebase.google.com/docs)
- [FastAPI Deployment](https://fastapi.tiangolo.com/deployment/)
- [Nginx Configuration](https://nginx.org/en/docs/)

## 🚀 Next Steps

1. **Custom Domain**: Configure Route 53 for custom domain
2. **CI/CD**: Set up GitHub Actions for automated deployments
3. **Monitoring**: Integrate with Datadog, New Relic, or AWS CloudWatch
4. **Backups**: Automate Firebase Firestore backups
5. **Scaling**: Set up Auto Scaling Group for EC2, Multi-region CloudFront
6. **Security**: AWS WAF for DDoS protection, AWS Shield

---

For local development instructions, see [`README.md`](README.md).
1. Upgrade Render to paid tier ($7/month)
2. Add Redis for caching
3. Add CDN for frontend
4. Upgrade Firebase to Blaze plan
