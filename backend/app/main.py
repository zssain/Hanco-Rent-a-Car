"""
Hanco-AI Backend - Main Application Entry Point
FastAPI application with Firebase, ONNX, and AI integration
"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging
import time
from typing import Callable

from app.core.config import settings
from app.core.firebase import firebase_client
from app.api.v1.router import api_router

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan handler.
    Manages startup and shutdown events.
    """
    # ==================== Startup ====================
    logger.info("🚀 Starting Hanco AI Backend...")
    logger.info(f"📝 Environment: {settings.ENVIRONMENT}")
    logger.info(f"🔧 Debug mode: {settings.DEBUG}")
    logger.info(f"🔥 Firebase Project: {settings.FIREBASE_PROJECT_ID}")
    logger.info(f"🤖 Gemini API: {'✅ Configured' if settings.GEMINI_API_KEY else '❌ Not configured'}")
    logger.info(f"🌤️  Weather API: {settings.OPEN_METEO_URL}")
    logger.info(f"📚 API Docs: http://localhost:8000{settings.API_V1_PREFIX}/docs")
    
    # Initialize Firebase (already initialized in firebase.py)
    try:
        _ = firebase_client.db
        logger.info("✅ Firebase connection verified")
    except Exception as e:
        logger.error(f"❌ Firebase initialization error: {e}")
    
    # TODO: Load ONNX model on startup (when model is available)
    # try:
    #     load_onnx_model(settings.ONNX_MODEL_PATH)
    #     logger.info("✅ ONNX model loaded successfully")
    # except Exception as e:
    #     logger.warning(f"⚠️  ONNX model not loaded: {e}")
    
    logger.info("✅ Application startup complete")
    
    yield
    
    # ==================== Shutdown ====================
    logger.info("👋 Shutting down Hanco AI Backend...")
    logger.info("✅ Cleanup complete")


# Create FastAPI application
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.APP_VERSION,
    description="AI-powered car rental platform for Saudi Arabia",
    docs_url=f"{settings.API_V1_PREFIX}/docs",
    redoc_url=f"{settings.API_V1_PREFIX}/redoc",
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
    lifespan=lifespan
)


# ==================== CORS Middleware ====================
def is_allowed_origin(origin: str) -> bool:
    """Check if origin is allowed"""
    if origin in settings.ALLOWED_ORIGINS:
        return True
    # Allow all Vercel preview deployments
    if origin.endswith('.vercel.app'):
        return True
    return False

# Custom CORS middleware to handle dynamic origins
@app.middleware("http")
async def cors_middleware(request: Request, call_next):
    origin = request.headers.get("origin")
    
    response = await call_next(request)
    
    if origin and is_allowed_origin(origin):
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Credentials"] = "true"
        response.headers["Access-Control-Allow-Methods"] = "*"
        response.headers["Access-Control-Allow-Headers"] = "*"
    
    return response

# Handle preflight requests
@app.options("/{rest_of_path:path}")
async def preflight_handler(request: Request, rest_of_path: str):
    origin = request.headers.get("origin")
    
    if origin and is_allowed_origin(origin):
        return JSONResponse(
            content={},
            headers={
                "Access-Control-Allow-Origin": origin,
                "Access-Control-Allow-Credentials": "true",
                "Access-Control-Allow-Methods": "*",
                "Access-Control-Allow-Headers": "*",
            }
        )
    return JSONResponse(content={}, status_code=403)


# ==================== Logging Middleware ====================
@app.middleware("http")
async def log_requests(request: Request, call_next: Callable):
    """Log all HTTP requests"""
    start_time = time.time()
    
    # Process request
    response = await call_next(request)
    
    # Calculate processing time
    process_time = time.time() - start_time
    
    # Log request details
    logger.info(
        f"{request.method} {request.url.path} - "
        f"Status: {response.status_code} - "
        f"Time: {process_time:.3f}s"
    )
    
    # Add custom header
    response.headers["X-Process-Time"] = str(process_time)
    
    return response


# ==================== Error Handlers ====================
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler for unhandled errors"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": str(exc) if settings.DEBUG else "An unexpected error occurred"
        }
    )


# ==================== Root Endpoints ====================
@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "name": settings.PROJECT_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "status": "operational",
        "docs": f"{settings.API_V1_PREFIX}/docs",
        "health": "/health"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring"""
    try:
        # Check Firebase connection
        _ = firebase_client.db.collection("users").limit(1).get()
        firebase_status = "healthy"
    except Exception as e:
        logger.error(f"Firebase health check failed: {e}")
        firebase_status = "unhealthy"
    
    return {
        "status": "healthy" if firebase_status == "healthy" else "degraded",
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "services": {
            "firebase": firebase_status,
            "api": "healthy"
        }
    }


# ==================== Include API Router ====================
app.include_router(api_router, prefix=settings.API_V1_PREFIX)


# ==================== Vercel Handler ====================
# Export app for Vercel serverless deployment
handler = app


# ==================== Run Application ====================
if __name__ == "__main__":
    import uvicorn
    
    logger.info("🌐 Starting uvicorn server...")
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    )
