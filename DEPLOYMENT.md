# Hanco AI - Deployment Guide

## Prerequisites

1. GitHub account
2. Render account (sign up at https://render.com)
3. Firebase project set up
4. Gemini API key

## Environment Setup

### Backend Environment Variables

Create a `.env` file in the `backend/` directory:

```bash
cp backend/.env.example backend/.env
```

Fill in these values:
- `GEMINI_API_KEY` - From Google AI Studio
- `FIREBASE_PROJECT_ID` - From Firebase Console
- `GOOGLE_APPLICATION_CREDENTIALS` - Path to your Firebase service account JSON

### Frontend Environment Variables

Create a `.env` file in the `frontend/` directory:

```bash
cp frontend/.env.example frontend/.env
```

## Deploy to Render

### Step 1: Deploy Backend

1. Go to https://render.com/dashboard
2. Click **"New +"** → **"Web Service"**
3. Connect GitHub repository: `zssain/Hanco-Rent-a-Car`
4. Configure:
   - **Name**: `hanco-backend`
   - **Region**: Singapore (closest to Saudi Arabia)
   - **Branch**: `main`
   - **Root Directory**: `backend`
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - **Instance Type**: Free

5. **Environment Variables**:
   ```
   GEMINI_API_KEY=<your_gemini_api_key>
   FIREBASE_PROJECT_ID=<your_firebase_project_id>
   GOOGLE_APPLICATION_CREDENTIALS=/etc/secrets/firebase-key.json
   ENVIRONMENT=production
   PORT=8000
   ```

6. **Secret Files**:
   - Click "Secret Files"
   - Filename: `/etc/secrets/firebase-key.json`
   - Content: Paste your Firebase service account JSON

7. Click **"Create Web Service"**
8. Wait for deployment (5-10 minutes)
9. **Copy your backend URL** (e.g., `https://hanco-backend.onrender.com`)

### Step 2: Deploy Frontend

1. Click **"New +"** → **"Static Site"**
2. Select repository: `zssain/Hanco-Rent-a-Car`
3. Configure:
   - **Name**: `hanco-frontend`
   - **Branch**: `main`
   - **Root Directory**: `frontend`
   - **Build Command**: `npm install && npm run build`
   - **Publish Directory**: `dist`

4. **Environment Variable**:
   ```
   VITE_API_URL=<your_backend_url_from_step_1>
   ```

5. Click **"Create Static Site"**
6. Wait for deployment (5-10 minutes)

### Step 3: Update CORS

After frontend deployment, update backend environment variables:
- Add frontend URL to `CORS_ORIGINS`

### Step 4: Test

1. Visit your frontend URL
2. Test login (use Consumer quick login)
3. Test chatbot booking flow
4. Test payment

## Architecture

```
Frontend (React + Vite)
    ↓
    → Render Static Site
    ↓
Backend (FastAPI)
    ↓
    → Render Web Service
    ↓
Firebase (Firestore)
    ↓
    → Database & Auth
    ↓
Gemini AI
    ↓
    → Chatbot Intelligence
```

## Monitoring

- **Backend Logs**: Render Dashboard → Your Backend Service → Logs
- **Frontend Logs**: Browser Console
- **Firebase**: Firebase Console → Firestore Database

## Troubleshooting

### Backend won't start
- Check environment variables are set correctly
- Verify Firebase credentials file is uploaded
- Check logs for errors

### Frontend can't connect to backend
- Verify `VITE_API_URL` points to correct backend URL
- Check CORS settings in backend
- Verify backend is running

### Chatbot errors
- Check Gemini API key is valid
- Verify Firebase connection
- Check backend logs for errors

## Costs

- **Render Free Tier**: 750 hours/month (enough for demo)
- **Firebase**: Free tier (50K reads, 20K writes per day)
- **Gemini AI**: Free tier (60 requests/minute)

## Upgrade Path

When you need to scale:
1. Upgrade Render to paid tier ($7/month)
2. Add Redis for caching
3. Add CDN for frontend
4. Upgrade Firebase to Blaze plan
