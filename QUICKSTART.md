# 🚀 QUICK START GUIDE - Post Security Hardening

## 🔐 IMPORTANT: This repository no longer contains any secrets!

All API keys and credentials MUST be set via environment variables.

---

## 📋 Local Development Setup

### 1️⃣ Backend Setup (5 minutes)

```bash
cd backend

# Install Python 3.11 dependencies
pip install -r requirements.txt

# Copy environment template
cp .env.example .env

# Edit .env with your credentials
nano .env  # or use any text editor
```

**Required in `.env`:**
```bash
# Firebase - Get from Firebase Console
GOOGLE_APPLICATION_CREDENTIALS=/absolute/path/to/firebase-key.json
FIREBASE_PROJECT_ID=your-project-id
FIREBASE_API_KEY=your-web-api-key
# ... (see .env.example for all required fields)

# Gemini AI - Get from https://makersuite.google.com/app/apikey
GEMINI_API_KEY=your-gemini-key-here

# CORS - Allow frontend
ALLOWED_ORIGINS=http://localhost:5173
```

**Run backend:**
```bash
uvicorn app.main:app --reload --port 8000
```

✅ Backend running at `http://localhost:8000`  
✅ API docs at `http://localhost:8000/api/v1/docs`

---

### 2️⃣ Frontend Setup (5 minutes)

```bash
cd frontend

# Install Node.js dependencies
npm install

# Copy environment template
cp .env.example .env.local

# Edit .env.local with your config
nano .env.local  # or use any text editor
```

**Required in `.env.local`:**
```bash
# Backend API URL
VITE_API_BASE_URL=http://localhost:8000

# Firebase Web Config - Get from Firebase Console > Project Settings
VITE_FIREBASE_API_KEY=your-web-api-key
VITE_FIREBASE_AUTH_DOMAIN=your-project.firebaseapp.com
VITE_FIREBASE_PROJECT_ID=your-project-id
# ... (see .env.example for all required fields)
```

**Run frontend:**
```bash
npm run dev
```

✅ Frontend running at `http://localhost:5173`

---

## 🔍 Before Every Commit

**Run secret scanner to prevent accidental key commits:**

**Windows:**
```powershell
powershell -ExecutionPolicy Bypass -File scripts\check_secrets.ps1
```

**Linux/Mac:**
```bash
bash scripts/check_secrets.sh
```

If secrets detected → Fix before committing!  
If no secrets → Safe to commit ✅

---

## 🚫 NEVER Commit These Files:

- `.env`
- `.env.local`
- `.env.production`
- `firebase-key.json`
- Any file with API keys or secrets

These are already in `.gitignore` - but double-check!

---

## ✅ Safe to Commit:

- `.env.example` (templates only, no real values)
- All code files
- Configuration files (without secrets)
- Documentation

---

## 🌐 Production Deployment

**See full guide:** [`DEPLOYMENT.md`](DEPLOYMENT.md)

**Quick summary:**
1. Backend → AWS EC2 with Nginx
2. Frontend → AWS S3 + CloudFront
3. Secrets → Environment variables or AWS Secrets Manager

---

## 🆘 Common Issues

### "Firebase credentials not found"
→ Check `GOOGLE_APPLICATION_CREDENTIALS` path is correct and file exists

### "VITE_API_BASE_URL not set"
→ Create `frontend/.env.local` and set the variable

### "CORS error" in browser
→ Add your frontend URL to `ALLOWED_ORIGINS` in backend `.env`

### "Module not found" errors
→ Run `pip install -r requirements.txt` (backend) or `npm install` (frontend)

---

## 📚 Documentation

- **Local Development**: [`README.md`](README.md)
- **AWS Deployment**: [`DEPLOYMENT.md`](DEPLOYMENT.md)
- **Security Details**: [`SECURITY_HARDENING_SUMMARY.md`](SECURITY_HARDENING_SUMMARY.md)

---

## 💡 Pro Tips

1. **Use separate Firebase projects** for dev/staging/production
2. **Never share your `.env` files** - each developer creates their own
3. **Run secret scanner** before every commit
4. **Keep dependencies updated**: `pip install -U -r requirements.txt`
5. **Monitor Firebase quotas** in Firebase Console

---

**Questions?** Check the full documentation or the security hardening summary.

**Ready to deploy?** Follow the complete AWS deployment guide in `DEPLOYMENT.md`.

---

✨ **Happy coding! Your secrets are now safe.** 🔒
