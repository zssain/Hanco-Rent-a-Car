# 🚀 AWS EC2 Deployment Guide - Complete Setup

## Prerequisites
- ✅ AWS Account
- ✅ AWS CLI configured with credentials
- ✅ Firebase service account key (firebase-key.json)
- ✅ Gemini API key

---

## 📋 Step 1: Launch EC2 Instance

1. Go to **AWS Console → EC2 → Launch Instance**

2. **Configure Instance:**
   - **Name:** hanco-ai
   - **AMI:** Ubuntu Server 22.04 LTS
   - **Instance Type:** t3.medium (or t3.large for production)
   - **Key Pair:** Create new → Save `.pem` file securely
   
3. **Security Group (Important!):**
   - SSH (22) - Your IP
   - HTTP (80) - Anywhere (0.0.0.0/0)
   - HTTPS (443) - Anywhere (0.0.0.0/0)
   - Custom TCP (8000) - Anywhere (0.0.0.0/0)

4. **Storage:** 30 GB gp3

5. Click **Launch Instance**

---

## 📋 Step 2: Connect to EC2

### Windows (PowerShell):
```powershell
# Navigate to your key location
cd Downloads

# Connect (replace with your EC2 public IP)
ssh -i hanco-ai-key.pem ubuntu@YOUR_EC2_IP
```

---

## 📋 Step 3: Install Docker on EC2

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
sudo apt install -y docker.io docker-compose git

# Add user to docker group
sudo usermod -aG docker ubuntu
newgrp docker

# Verify installation
docker --version
docker-compose --version
```

---

## 📋 Step 4: Clone Repository

```bash
# Clone your repository
git clone https://github.com/YOUR_USERNAME/Hanco-AI.git
cd Hanco-AI
```

---

## 📋 Step 5: Upload Firebase Key

### From your Windows machine:
```powershell
# Navigate to your project
cd "C:\Users\Sufyaan\Desktop\Hanco AI"

# Upload firebase key (replace with your EC2 IP and key path)
scp -i C:\Users\Sufyaan\Downloads\hanco-ai-key.pem backend\firebase-key.json ubuntu@YOUR_EC2_IP:~/Hanco-AI/backend/
```

---

## 📋 Step 6: Configure Environment Variables

### On EC2:
```bash
cd ~/Hanco-AI

# Create .env file
nano .env
```

### Add these variables (replace with your actual values):
```bash
ENVIRONMENT=production
DEBUG=False
FIREBASE_PROJECT_ID=hanco-ai
GEMINI_API_KEY=your-actual-gemini-api-key
FRONTEND_URL=http://YOUR_EC2_PUBLIC_IP
ALLOWED_ORIGINS=["http://YOUR_EC2_PUBLIC_IP"]
```

**Save:** Ctrl+X → Y → Enter

---

## 📋 Step 7: Deploy!

```bash
cd ~/Hanco-AI

# Make deploy script executable
chmod +x deploy.sh

# Run deployment
./deploy.sh
```

**That's it!** 🎉

---

## 🌐 Access Your Application

- **Frontend:** http://YOUR_EC2_IP
- **Backend API:** http://YOUR_EC2_IP:8000
- **API Documentation:** http://YOUR_EC2_IP:8000/api/v1/docs

---

## 🔄 Update After Code Changes

```bash
cd ~/Hanco-AI
git pull origin main
docker-compose down
docker-compose build
docker-compose up -d
```

Or simply run:
```bash
./deploy.sh
```

---

## 📊 Useful Commands

```bash
# View logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f backend
docker-compose logs -f frontend

# Check container status
docker-compose ps

# Stop all containers
docker-compose down

# Restart containers
docker-compose restart

# Remove all containers and volumes
docker-compose down -v
```

---

## 🔒 (Optional) Set Up Domain & SSL

### If you have a domain:

1. **Point DNS to EC2:**
   - A Record: `yourdomain.com` → EC2 Public IP
   - A Record: `api.yourdomain.com` → EC2 Public IP

2. **Install Certbot:**
```bash
sudo apt install -y certbot python3-certbot-nginx
```

3. **Update docker-compose.yml ports:**
```yaml
frontend:
  ports:
    - "80:80"
    - "443:443"
```

4. **Get SSL Certificate:**
```bash
sudo certbot --nginx -d yourdomain.com -d api.yourdomain.com
```

---

## 🐛 Troubleshooting

### Backend not starting:
```bash
docker logs hanco-backend
```

### Frontend not accessible:
```bash
docker logs hanco-frontend
```

### Port already in use:
```bash
sudo lsof -i :80
sudo lsof -i :8000
# Kill process: sudo kill -9 PID
```

### Firebase connection issues:
- Check firebase-key.json exists in backend/
- Verify FIREBASE_PROJECT_ID in .env matches your Firebase project

### CORS errors:
- Update ALLOWED_ORIGINS in .env to include your domain/IP
- Restart containers: `docker-compose restart`

---

## 💰 Monthly Cost Estimate

- **t3.medium EC2:** ~$30-35
- **30 GB Storage:** ~$3
- **Data Transfer:** ~$5-10
- **Total:** ~$40-50/month

---

## 🎯 Production Checklist

- [ ] EC2 instance launched and running
- [ ] Security groups configured correctly
- [ ] Docker and docker-compose installed
- [ ] Repository cloned
- [ ] Firebase key uploaded
- [ ] .env file configured with real API keys
- [ ] Application deployed successfully
- [ ] Frontend accessible via browser
- [ ] Backend API responding (check /docs)
- [ ] Chatbot working
- [ ] Bookings creating successfully

---

## 📞 Need Help?

Check the logs:
```bash
docker-compose logs -f
```

This will show you real-time logs from both frontend and backend.
