"""
WHY: FastAPI production application with authentication
  - Async/await for high performance (non-blocking I/O)
  - Built-in OpenAPI documentation (Swagger)
  - Dependency injection for clean code
  - CORS for cross-origin requests

HOW:
  - FastAPI app with middleware stack
  - JWT authentication with API keys
  - Structured logging
  - Health check endpoint

ALTERNATIVE not chosen:
  - Django: Too heavy, slower, built-in ORM overhead
  - Flask: Synchronous, hard to add async later
"""

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
import logging
import os
from datetime import datetime
from typing import Optional

# Import custom modules
from src.utils.config import load_config
from src.utils.exceptions import ClaimsEngineException
from src.db.database import get_db, init_db
from src.cache.redis_client import check_redis_connection

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load configuration
config = load_config()

# Initialize FastAPI app
app = FastAPI(
    title="Claims Triage & Fraud Risk Engine",
    description="End-to-end AI/ML system for insurance claims automation",
    version="1.0.0",
    docs_url="/api/docs",  # Swagger UI
    redoc_url="/api/redoc",  # ReDoc UI
    openapi_url="/api/openapi.json",
)

# ============================================
# MIDDLEWARE CONFIGURATION
# ============================================

# CORS: Allow requests from specific origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:8501").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Trusted hosts: Only allow requests from these hosts
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1").split(","),
)


# ============================================
# AUTHENTICATION & AUTHORIZATION
# ============================================

class APIKeyAuth:
    """
    API Key authentication middleware.
    
    Why: Simple, stateless authentication perfect for service-to-service
    
    Usage:
        @app.get("/protected")
        def protected_route(auth: APIKeyAuth = Depends()):
            return {"message": "Authenticated"}
    """

    def __init__(self, api_key: str = Depends(lambda: None)):
        self.api_key = api_key
        self.role = "viewer"  # Default role

    async def validate(self, request) -> bool:
        """Validate API key from request header."""
        api_key_header = request.headers.get("X-API-Key")
        if not api_key_header:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing API key",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Check API key (in production, look up from database)
        if api_key_header != os.getenv("API_KEY", "dev-key-12345"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid API key",
            )

        return True


# ============================================
# HEALTH CHECK ENDPOINT
# ============================================

@app.get("/api/v1/health", tags=["System"])
async def health_check():
    """
    Health check endpoint for Kubernetes liveness/readiness probes.
    
    Returns:
        - database: PostgreSQL connection status
        - redis: Redis connection status
        - timestamp: Server timestamp
    """
    try:
        # Check database
        from src.db.database import engine
        from sqlalchemy import text
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
            db_status = "healthy"
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        db_status = "unhealthy"

    # Check Redis
    redis_status = "healthy" if check_redis_connection() else "unhealthy"

    # Determine overall status
    overall_status = "healthy" if db_status == "healthy" and redis_status == "healthy" else "degraded"

    return {
        "status": overall_status,
        "database": db_status,
        "redis": redis_status,
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0",
    }


# ============================================
# STARTUP & SHUTDOWN EVENTS
# ============================================

@app.on_event("startup")
async def startup_event():
    """Initialize database and caches on startup."""
    logger.info("🚀 Starting Claims Engine...")
    
    # Initialize database tables
    try:
        init_db()
        logger.info("✅ Database initialized")
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
        raise

    # Check Redis connection
    if check_redis_connection():
        logger.info("✅ Redis connected")
    else:
        logger.warning("⚠️ Redis unavailable (caching disabled)")

    logger.info("✅ Claims Engine ready")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    logger.info("🛑 Shutting down Claims Engine...")
    # Add cleanup logic here if needed


# ============================================
# EXCEPTION HANDLERS
# ============================================

@app.exception_handler(ClaimsEngineException)
async def claims_exception_handler(request, exc: ClaimsEngineException):
    """Handle custom ClaimsEngineException."""
    logger.error(f"ClaimsEngineException: {exc}")
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": str(exc)},
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc: Exception):
    """Handle unexpected exceptions."""
    logger.error(f"Unexpected exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error"},
    )


# ============================================
# API ROUTES (Coming in later phases)
# ============================================

# Routes will be added in Phase 3:
# - POST /api/v1/claims/submit
# - GET /api/v1/claims/{claim_id}
# - POST /api/v1/claims/{claim_id}/feedback
# - GET /api/v1/analytics/dashboard
# - GET /api/v1/models/status
# - POST /api/v1/admin/retrain


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "src.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=os.getenv("APP_ENV") == "development",
        log_level="info",
    )
