"""
CareLock Sync - Secure HTTPS Server Launcher
Runs FastAPI with TLS 1.3 enabled
"""

import sys
import os

# Add backend to path
backend_path = os.path.join(os.path.dirname(__file__), 'backend')
sys.path.insert(0, backend_path)

# Check if api/main.py exists, if not create minimal app
try:
    from api.main import app
except (ImportError, ModuleNotFoundError):
    print("⚠️  API main.py not found, creating minimal FastAPI app for testing...")
    from fastapi import FastAPI
    app = FastAPI(title="CareLock Sync API", version="0.5.0")
    
    @app.get("/health")
    async def health():
        return {"status": "healthy", "tls": "1.3"}
    
    @app.get("/api/v1/patients")
    async def get_patients():
        return {"error": "Unauthorized"}, 401

from security.tls_config import run_secure_server
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

# Add HTTPS redirect middleware (redirects HTTP to HTTPS)
# app.add_middleware(HTTPSRedirectMiddleware)  # Uncomment for production

# Add trusted host middleware (prevents host header attacks)
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["localhost", "127.0.0.1", "carelock-sync.local", "*.carelock.com"]
)

# Add HSTS (HTTP Strict Transport Security) header
@app.middleware("http")
async def add_security_headers(request, call_next):
    response = await call_next(request)
    
    # HSTS: Force HTTPS for 1 year
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    
    # Additional security headers
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    
    return response

if __name__ == "__main__":
    print("Starting CareLock Sync with TLS 1.3...")
    
    # Run server with HTTPS
    run_secure_server(
        app=app,
        host="0.0.0.0",
        port=8443,  # Use 443 in production
        reload=False  # Set to True for development
    )
