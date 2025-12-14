# Hanco-AI Backend

Modern FastAPI backend for AI-powered car rental platform.

## Tech Stack

- **Framework**: FastAPI (Python 3.11)
- **Authentication**: Firebase Authentication
- **Database**: Firestore (NoSQL)
- **AI Chatbot**: Gemini API (primary), OpenAI (fallback)
- **ML Pricing**: ONNX Runtime
- **Weather**: Open-Meteo API (free)
- **Scraping**: Crawl4AI (Yelo, Lumi, Budget, Hertz)
- **Payments**: Simulator (no real gateway)

## Project Structure

```
backend/
├── app/
│   ├── api/v1/          # API endpoints
│   ├── core/            # Core configuration
│   ├── models/          # Firestore models
│   ├── schemas/         # Pydantic schemas
│   └── services/        # Business logic services
├── ml/
│   ├── training/        # Model training scripts
│   └── models/          # ONNX models
└── requirements.txt
```

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Configure environment:
```bash
cp .env.example .env
# Edit .env with your credentials
```

3. Run development server:
```bash
uvicorn app.main:app --reload --port 8000
```

## API Documentation

Once running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Deployment

Deploy to AWS EC2 (see infra/ec2/ for scripts)
