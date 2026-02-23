"""
CareLock Sync — Authentication & Authorization
Sprint 3: API Key auth + Role-Based Access Control

Roles:
  admin        → full access (all tenants, all ops, sync trigger)
  hospital     → own tenant only (read + sync own data)
  readonly     → read-only across allowed tenants

Usage:
  @router.get("/endpoint")
  async def ep(auth: AuthContext = Depends(require_auth)):
      ...

  @router.post("/admin-only")
  async def ep(auth: AuthContext = Depends(require_admin)):
      ...
"""
from fastapi import Security, HTTPException, status, Depends
from fastapi.security import APIKeyHeader
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timedelta
from collections import defaultdict, deque
import os, threading

# ── API Key header ───────────────────────────────────────────────────────────
API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)

# ── In-memory sliding-window rate limiter ────────────────────────────────────
class RateLimiter:
    """Sliding window rate limiter. Thread-safe."""
    def __init__(self, max_requests: int, window_seconds: int):
        self.max_requests = max_requests
        self.window = timedelta(seconds=window_seconds)
        self._buckets: dict = defaultdict(deque)
        self._lock = threading.Lock()

    def is_allowed(self, key: str) -> tuple[bool, int]:
        """Returns (allowed, remaining). Trims old entries each call."""
        now = datetime.utcnow()
        cutoff = now - self.window
        with self._lock:
            bucket = self._buckets[key]
            while bucket and bucket[0] < cutoff:
                bucket.popleft()
            if len(bucket) >= self.max_requests:
                return False, 0
            bucket.append(now)
            return True, self.max_requests - len(bucket)

# 100 requests/minute per valid key; 10 attempts/minute for failed auth
_valid_limiter  = RateLimiter(max_requests=100, window_seconds=60)
_failed_limiter = RateLimiter(max_requests=10,  window_seconds=60)

# ── AuthContext returned to every endpoint ───────────────────────────────────
class AuthContext(BaseModel):
    api_key_id:  str
    role:        str          # admin | hospital | readonly
    tenant_id:   Optional[int]  # None means "all tenants" (admin only)
    hospital:    Optional[str]

    def can_access_tenant(self, tid: int) -> bool:
        if self.role == "admin":
            return True
        return self.tenant_id == tid

    def assert_tenant(self, tid: int) -> None:
        if not self.can_access_tenant(tid):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied: your key is scoped to tenant {self.tenant_id}"
            )

# ── Key registry  (env-var driven so keys never live in source code) ─────────
# Format in .env:
#   CARELOCK_KEYS=admin:clk-admin-key-abc123,hospital1:clk-cgh001-key-xyz,hospital2:clk-pgh002-key-def
#
# Fallback hardcoded keys for development only
_DEV_KEYS = {
    "clk-admin-change-me-in-prod": {
        "api_key_id": "admin-dev",
        "role":       "admin",
        "tenant_id":  None,
        "hospital":   None,
    },
    "clk-cgh001-hospital-key": {
        "api_key_id": "hospital-cgh001",
        "role":       "hospital",
        "tenant_id":  1,
        "hospital":   "City General Hospital",
    },
    "clk-pgh002-hospital-key": {
        "api_key_id": "hospital-pgh002",
        "role":       "hospital",
        "tenant_id":  2,
        "hospital":   "Punjab General Hospital",
    },
    "clk-nmh003-hospital-key": {
        "api_key_id": "hospital-nmh003",
        "role":       "hospital",
        "tenant_id":  3,
        "hospital":   "National Medical Hospital",
    },
    "clk-chi004-hospital-key": {
        "api_key_id": "hospital-chi004",
        "role":       "hospital",
        "tenant_id":  4,
        "hospital":   "City Hospital Islamabad",
    },
    "clk-akh005-hospital-key": {
        "api_key_id": "hospital-akh005",
        "role":       "hospital",
        "tenant_id":  5,
        "hospital":   "Aga Khan University Hospital",
    },
    "clk-readonly-analytics-key": {
        "api_key_id": "readonly-analytics",
        "role":       "readonly",
        "tenant_id":  None,
        "hospital":   None,
    },
}

def _load_key_registry() -> dict:
    """Load keys from CARELOCK_KEYS env var or fall back to dev keys."""
    env_keys = os.environ.get("CARELOCK_KEYS", "")
    if not env_keys:
        return _DEV_KEYS                  # dev mode only

    registry = {}
    for entry in env_keys.split(","):
        parts = entry.strip().split(":")
        if len(parts) == 3:
            key_id, role, key_value = parts
            tid = int(parts[3]) if len(parts) == 4 else None
            registry[key_value] = {
                "api_key_id": key_id, "role": role,
                "tenant_id": tid, "hospital": None
            }
    return registry

KEY_REGISTRY = _load_key_registry()

# ── Core dependency ──────────────────────────────────────────────────────────
def require_auth(api_key: str = Security(API_KEY_HEADER)) -> AuthContext:
    """Base dependency — any valid API key, rate-limited."""
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing X-API-Key header",
            headers={"WWW-Authenticate": "ApiKey"},
        )
    # Rate limit failed auth attempts per raw key (prevents brute force)
    record = KEY_REGISTRY.get(api_key)
    if not record:
        allowed, _ = _failed_limiter.is_allowed(api_key[:16])
        if not allowed:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many invalid key attempts. Try again in 60 seconds.",
            )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "ApiKey"},
        )
    # Rate limit valid key usage
    allowed, remaining = _valid_limiter.is_allowed(record["api_key_id"])
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded: 100 requests/minute. Try again shortly.",
            headers={"Retry-After": "60"},
        )
    return AuthContext(**record)

def require_admin(auth: AuthContext = Depends(require_auth)) -> AuthContext:
    """Dependency — admin role required."""
    if auth.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin role required"
        )
    return auth

def require_write(auth: AuthContext = Depends(require_auth)) -> AuthContext:
    """Dependency — admin or hospital role required (not readonly)."""
    if auth.role == "readonly":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Write access required"
        )
    return auth

def optional_auth(api_key: str = Security(API_KEY_HEADER)) -> Optional[AuthContext]:
    """Optional auth — returns None if no key provided (for public endpoints)."""
    if not api_key:
        return None
    record = KEY_REGISTRY.get(api_key)
    return AuthContext(**record) if record else None
