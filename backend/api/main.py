"""
CareLock Sync - Main FastAPI Application
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
from datetime import datetime
import sys
import os

# Add paths for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import routes
from routes import patients, status, connector, sync

# Create FastAPI app instance
app = FastAPI(
    title="CareLock Sync API",
    description="Secure hospital database synchronization system with automated schema mapping",
    version="0.3.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(patients.router)
app.include_router(status.router)
app.include_router(connector.router)
app.include_router(sync.router)


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint - API information"""
    return {
        "name": "CareLock Sync API",
        "version": "0.3.0",
        "status": "running",
        "timestamp": datetime.utcnow().isoformat(),
        "docs": "/docs",
        "redoc": "/redoc",
        "endpoints": {
            "patients": "/api/v1/patients",
            "status": "/api/v1/status",
            "connector": "/api/v1/connector",
            "sync": "/api/v1/sync",
            "health": "/health"
        }
    }


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "CareLock Sync API"
    }


# Startup event
@app.on_event("startup")
async def startup_event():
    """Run on application startup"""
    print("=" * 60)
    print("CareLock Sync API - Starting Up")
    print("=" * 60)
    print(f"Version: 0.3.0")
    print(f"API Documentation: http://localhost:8000/docs")
    print(f"ReDoc: http://localhost:8000/redoc")
    print(f"Health Check: http://localhost:8000/health")
    print(f"Sync Endpoints: http://localhost:8000/api/v1/sync")
    print("=" * 60)


# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Run on application shutdown"""
    print("\nCareLock Sync API - Shutting Down")


# Development server
if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
