"""
Main FastAPI Application
Complete SLA Recovery Audit System with Anthropic Claude Integration
"""

import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager

from .config import settings
from .database import init_db, get_db, close_db
from .seed import seed_initial_data

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Lifecycle events
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    # Startup
    logger.info("Starting up...")
    init_db()
    db = next(get_db())
    try:
        seed_initial_data(db)
    finally:
        db.close()
    logger.info("Database initialized and seeded")

    yield

    # Shutdown
    logger.info("Shutting down...")
    close_db()
    logger.info("Database connections closed")


# Create FastAPI app
app = FastAPI(
    title="SLA Recovery Audit System",
    description="Automated SLA and Contract Recovery Claim Processing with Claude AI",
    version="2.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==================== Error Handlers ====================

@app.exception_handler(ValueError)
async def value_error_handler(request, exc):
    return JSONResponse(
        status_code=400,
        content={"status": "error", "message": str(exc)}
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"status": "error", "message": "Internal server error"}
    )


# ==================== Health Check ====================

@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "SLA Recovery Audit System",
        "version": "2.0.0",
        "llm_backend": f"Claude API (Model: {settings.llm_model})"
    }


@app.get("/")
def root():
    """Root endpoint with API information"""
    return {
        "message": "SLA Recovery Audit System API",
        "version": "2.0.0",
        "features": [
            "Document parsing with Claude AI",
            "Multi-document type support (SLA, Insurance, Contracts)",
            "SQL query generation and validation",
            "Automated cost calculation",
            "Role-based approval workflows",
            "Complete audit trails and proofs",
            "Support for multiple cost types and currencies"
        ],
        "endpoints": {
            "docs": "/docs",
            "redoc": "/redoc",
            "openapi": "/openapi.json"
        }
    }


# Import and include routers
from .routers import auth_router, documents, calculations
app.include_router(auth_router.router, prefix="/api/auth")
app.include_router(documents.router, prefix="/api/documents")
app.include_router(calculations.router, prefix="/api/calculations")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=True
    )
